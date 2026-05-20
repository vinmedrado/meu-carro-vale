from __future__ import annotations
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from collectors.base import ResponsibleHttpClient
from config.settings import get_settings
from storage.models import init_db, get_session_factory
from .catalog_repository import CatalogRepository, CatalogUpsertStats
from .catalog_manifest import CatalogManifestBuilder
from .catalog_search_index import CatalogSearchIndexBuilder

TYPE_PATHS = {"carros": "carros", "motos": "motos", "caminhoes": "caminhoes"}


class FipeRateLimitError(RuntimeError):
    """Erro operacional usado quando a API FIPE continua retornando limite 429."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_price(value: Any) -> float | None:
    if value is None:
        return None
    raw = str(value).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(raw)
    except ValueError:
        return None


class FipeFullSync:
    """Sincronização completa do Catálogo Mestre FIPE.

    Proteções operacionais:
    - full sync exige confirmação explícita quando chamado por CLI;
    - suporta limites de amostra para testes controlados;
    - salva checkpoint antes de marca/modelo/versão;
    - faz backoff exponencial em HTTP 429;
    - aplica cooldown global após muitos 429 seguidos;
    - preserva itens limitados em fila de retentativa;
    - exporta catálogo, índice de busca e manifest automaticamente ao fim.
    """

    DEFAULT_429_BACKOFFS = [5, 15, 45, 120]

    def __init__(self, client: ResponsibleHttpClient | None = None, export_dir: str | Path = "exports"):
        self.settings = get_settings()
        self.client = client or ResponsibleHttpClient()
        self.export_dir = Path(export_dir)
        self.checkpoint_path = Path("logs/pipeline/fipe_catalog_checkpoint.json")
        self.retry_queue_path = Path("logs/pipeline/fipe_retry_queue.json")
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.retry_queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.sleep_seconds = float(
            getattr(self.settings, "fipe_sync_base_sleep_seconds", None)
            or getattr(self.settings, "fipe_sync_sleep_seconds", 1.5)
        )
        self.max_retries = int(getattr(self.settings, "fipe_sync_max_retries", 6))
        self.backoff_multiplier = float(getattr(self.settings, "fipe_sync_backoff_multiplier", 3))
        self.max_backoff_seconds = float(getattr(self.settings, "fipe_sync_max_backoff_seconds", 180))
        self.cooldown_seconds = float(getattr(self.settings, "fipe_sync_429_cooldown_seconds", 300))
        self.max_429_before_cooldown = int(getattr(self.settings, "fipe_sync_max_429_before_cooldown", 5))
        self.started_at = time.monotonic()
        self._processed_versions = 0
        self._estimated_total_versions: int | None = None
        self._consecutive_429 = 0
        self._active_checkpoint: dict[str, Any] = {}
        self._retry_queue: list[dict[str, Any]] = self._load_retry_queue()

    def enabled_types(self) -> list[str]:
        types: list[str] = []
        if self.settings.fipe_sync_enable_carros:
            types.append("carros")
        if self.settings.fipe_sync_enable_motos:
            types.append("motos")
        if self.settings.fipe_sync_enable_caminhoes:
            types.append("caminhoes")
        return types

    def run(
        self,
        vehicle_types: list[str] | None = None,
        max_brands: int | None = None,
        max_models: int | None = None,
        max_versions: int | None = None,
        only_brands: bool = False,
        only_models: bool = False,
        only_versions: bool = False,
        resume: bool = True,
    ) -> dict[str, Any]:
        vehicle_types = vehicle_types or self.enabled_types()
        if resume and self.checkpoint_path.exists():
            self._log("Retomando do checkpoint")
        engine = init_db()
        Session = get_session_factory(engine)
        totals = {"brands": 0, "models": 0, "versions": 0}
        all_stats = CatalogUpsertStats()
        with Session() as session:
            repo = CatalogRepository(session)
            run = repo.start_run("full", ",".join(vehicle_types))
            try:
                for vehicle_type in vehicle_types:
                    stats, type_totals = self._sync_type(
                        repo,
                        vehicle_type,
                        max_brands=max_brands,
                        max_models=max_models,
                        max_versions=max_versions,
                        only_brands=only_brands,
                        only_models=only_models,
                        only_versions=only_versions,
                        resume=resume,
                    )
                    for field in ["new_brands", "new_models", "new_versions", "updated_brands", "updated_models", "updated_versions", "skipped_existing", "failed_items"]:
                        setattr(all_stats, field, getattr(all_stats, field) + getattr(stats, field))
                    all_stats.errors.extend(stats.errors)
                    for k, v in type_totals.items():
                        totals[k] += v
                retry_stats = self._drain_retry_queue(repo)
                for field in ["new_versions", "updated_versions", "skipped_existing", "failed_items"]:
                    setattr(all_stats, field, getattr(all_stats, field) + getattr(retry_stats, field))
                all_stats.errors.extend(retry_stats.errors)
                repo.finish_run(run, "success" if not all_stats.errors else "partial_success", all_stats, totals)
            except Exception as exc:  # noqa: BLE001
                all_stats.failed_items += 1
                all_stats.errors.append(str(exc))
                repo.finish_run(run, "error", all_stats, totals, error_message=str(exc))
                raise
        exports = CatalogManifestBuilder(self.export_dir).export_catalog_tables()
        search_index = CatalogSearchIndexBuilder(self.export_dir).export()
        manifest = CatalogManifestBuilder(self.export_dir).build(mode="full", stats=all_stats.as_dict(), totals=totals, exports={**exports, "vehicle_search_index": search_index})
        return {"status": "success" if not all_stats.errors else "partial_success", "run_type": "full", "totals": totals, "stats": all_stats.as_dict(), "exports": exports, "search_index": search_index, "manifest": manifest}

    def _sync_type(
        self,
        repo: CatalogRepository,
        vehicle_type: str,
        max_brands: int | None = None,
        max_models: int | None = None,
        max_versions: int | None = None,
        only_brands: bool = False,
        only_models: bool = False,
        only_versions: bool = False,
        resume: bool = True,
    ) -> tuple[CatalogUpsertStats, dict[str, int]]:
        stats = CatalogUpsertStats()
        totals = {"brands": 0, "models": 0, "versions": 0}
        checkpoint = self._load_checkpoint() if resume else {}
        brands = self._get_json(vehicle_type, "marcas")
        if max_brands:
            brands = brands[:max_brands]
        totals["brands"] += len(brands)
        self._log(f"Iniciando {vehicle_type}: {len(brands)} marcas planejadas")
        for brand_index, brand_payload in enumerate(brands, start=1):
            brand_code = str(brand_payload.get("codigo") or "")
            if not brand_code:
                continue
            self._checkpoint(vehicle_type, brand_code, None, None, stage="brand", brand_index=brand_index, model_index=None, version_index=None)
            try:
                self._log_progress(vehicle_type, brand_index, len(brands), f"marca {brand_payload.get('nome')} ({brand_code})")
                brand = repo.upsert_brand(vehicle_type, brand_code, brand_payload.get("nome") or "", stats)
                if only_brands:
                    repo.commit()
                    continue
                models_payload = self._get_json(vehicle_type, f"marcas/{brand_code}/modelos")
                models = models_payload.get("modelos", models_payload if isinstance(models_payload, list) else [])
                if max_models:
                    models = models[:max_models]
                totals["models"] += len(models)
                for model_index, model_payload in enumerate(models, start=1):
                    model_code = str(model_payload.get("codigo") or "")
                    if not model_code:
                        continue
                    self._checkpoint(vehicle_type, brand_code, model_code, None, stage="model", brand_index=brand_index, model_index=model_index, version_index=None)
                    try:
                        self._log_progress(vehicle_type, brand_index, len(brands), f"modelo {model_payload.get('nome')} ({model_code})")
                        model = repo.upsert_model(brand, model_code, model_payload.get("nome") or "", stats)
                        if only_models:
                            continue
                        years = self._get_json(vehicle_type, f"marcas/{brand_code}/modelos/{model_code}/anos")
                        if max_versions:
                            years = years[:max_versions]
                        totals["versions"] += len(years)
                        self._estimated_total_versions = (self._estimated_total_versions or 0) + len(years)
                        for version_index, year_payload in enumerate(years, start=1):
                            year_code = str(year_payload.get("codigo") or "")
                            if not year_code:
                                continue
                            self._checkpoint(vehicle_type, brand_code, model_code, year_code, stage="version", brand_index=brand_index, model_index=model_index, version_index=version_index)
                            if only_versions and checkpoint and self._already_checkpointed(checkpoint, vehicle_type, brand_code, model_code, year_code):
                                continue
                            detail_path = f"marcas/{brand_code}/modelos/{model_code}/anos/{year_code}"
                            try:
                                detail = self._get_json(vehicle_type, detail_path)
                            except FipeRateLimitError as exc:
                                self._enqueue_retry(vehicle_type, brand_code, model_code, year_code, detail_path, str(exc))
                                stats.failed_items += 1
                                stats.errors.append(f"Item enviado para retentativa {vehicle_type}/{brand_code}/{model_code}/{year_code}: {exc}")
                                continue
                            repo.upsert_version(brand, model, self._detail_to_payload(detail, year_code), stats)
                            self._processed_versions += 1
                            self._checkpoint(vehicle_type, brand_code, model_code, year_code, stage="version_done", brand_index=brand_index, model_index=model_index, version_index=version_index)
                            self._log_eta(vehicle_type, brand_payload.get("nome"), model_payload.get("nome"), version_index, len(years))
                    except FipeRateLimitError as exc:
                        stats.failed_items += 1
                        stats.errors.append(f"Falha temporária modelo {vehicle_type}/{brand_code}/{model_code}: {exc}")
                        self._log(f"Item enviado para retentativa: modelo {vehicle_type}/{brand_code}/{model_code}")
                    except Exception as exc:  # noqa: BLE001
                        stats.failed_items += 1
                        stats.errors.append(f"Falha modelo {vehicle_type}/{brand_code}/{model_code}: {exc}")
                repo.commit()
            except FipeRateLimitError as exc:
                stats.failed_items += 1
                stats.errors.append(f"Falha temporária marca {vehicle_type}/{brand_code}: {exc}")
                self._log(f"Item enviado para retentativa: marca {vehicle_type}/{brand_code}")
            except Exception as exc:  # noqa: BLE001
                stats.failed_items += 1
                stats.errors.append(f"Falha marca {vehicle_type}/{brand_code}: {exc}")
        repo.commit()
        return stats, totals

    def _get_json(self, vehicle_type: str, path: str):
        base = self.settings.fipe_base_url.rstrip("/")
        if not base.endswith(vehicle_type):
            base = f"{base.rsplit('/api/v1', 1)[0]}/api/v1/{vehicle_type}" if "/api/v1" in base else f"{base}/{vehicle_type}"
        url = f"{base}/{path.lstrip('/')}"
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                payload = self.client.get_json(url)
                self._consecutive_429 = 0
                if self.sleep_seconds:
                    time.sleep(self.sleep_seconds)
                return payload
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if not self._is_rate_limit_error(exc):
                    raise
                self._consecutive_429 += 1
                wait_seconds = self._backoff_seconds(attempt)
                self._log(f"Limite detectado na FIPE (429). Tentativa {attempt}/{self.max_retries}.")
                self._log(f"Aguardando {wait_seconds:g} segundos antes de retomar.")
                self._maybe_global_cooldown()
                time.sleep(wait_seconds)
                self.sleep_seconds = min(max(self.sleep_seconds * 1.5, self.sleep_seconds + 0.5), self.max_backoff_seconds)
        raise FipeRateLimitError(f"Limite 429 persistente após {self.max_retries} tentativas em {path}: {last_exc}")

    def _backoff_seconds(self, attempt: int) -> float:
        if attempt <= len(self.DEFAULT_429_BACKOFFS):
            return min(float(self.DEFAULT_429_BACKOFFS[attempt - 1]), self.max_backoff_seconds)
        previous = float(self.DEFAULT_429_BACKOFFS[-1])
        extra_steps = attempt - len(self.DEFAULT_429_BACKOFFS)
        return min(previous * (self.backoff_multiplier ** extra_steps), self.max_backoff_seconds)

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code == 429:
            return True
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
            return True
        text = str(exc).lower()
        return "429" in text or "too many requests" in text or "rate limit" in text

    def _maybe_global_cooldown(self) -> None:
        if self._consecutive_429 < self.max_429_before_cooldown:
            return
        self._persist_active_checkpoint()
        self._log("Limite detectado repetidas vezes. Salvando checkpoint e iniciando cooldown global.")
        self._log(f"Aguardando {self.cooldown_seconds:g} segundos para reduzir velocidade da sync inteira.")
        time.sleep(self.cooldown_seconds)
        self._log("Retomando do checkpoint")
        self._consecutive_429 = 0

    def _persist_active_checkpoint(self) -> None:
        if not self._active_checkpoint:
            return
        payload = dict(self._active_checkpoint)
        payload["processed_versions"] = self._processed_versions
        payload["updated_at"] = utc_now()
        payload["updated_at_epoch"] = time.time()
        self.checkpoint_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _detail_to_payload(self, detail: dict[str, Any], year_code: str) -> dict[str, Any]:
        return {
            "fipe_year_code": year_code,
            "fipe_code": detail.get("CodigoFipe"),
            "year": detail.get("AnoModelo"),
            "fuel": detail.get("Combustivel"),
            "version_name": detail.get("Modelo"),
            "reference_month": detail.get("MesReferencia"),
            "fipe_price": parse_price(detail.get("Valor")),
        }

    def _load_checkpoint(self) -> dict[str, Any]:
        if not self.checkpoint_path.exists():
            return {}
        try:
            return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _already_checkpointed(self, checkpoint: dict[str, Any], vehicle_type: str, brand_code: str, model_code: str, year_code: str) -> bool:
        return (
            checkpoint.get("vehicle_type") == vehicle_type
            and checkpoint.get("brand_code") == str(brand_code)
            and checkpoint.get("model_code") == str(model_code)
            and checkpoint.get("year_code") == str(year_code)
            and checkpoint.get("stage") in {"version", "version_done"}
        )

    def _checkpoint(self, vehicle_type: str, brand_code: str, model_code: str | None, year_code: str | None, stage: str, brand_index: int | None, model_index: int | None, version_index: int | None) -> None:
        payload = {
            "vehicle_type": vehicle_type,
            "brand_code": str(brand_code) if brand_code is not None else None,
            "model_code": str(model_code) if model_code is not None else None,
            "year_code": str(year_code) if year_code is not None else None,
            "stage": stage,
            "brand_index": brand_index,
            "model_index": model_index,
            "version_index": version_index,
            "processed_versions": self._processed_versions,
            "updated_at": utc_now(),
            "updated_at_epoch": time.time(),
        }
        self._active_checkpoint = payload
        self.checkpoint_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_retry_queue(self) -> list[dict[str, Any]]:
        if not self.retry_queue_path.exists():
            return []
        try:
            payload = json.loads(self.retry_queue_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, list) else []
        except json.JSONDecodeError:
            return []

    def _save_retry_queue(self) -> None:
        self.retry_queue_path.write_text(json.dumps(self._retry_queue, ensure_ascii=False, indent=2), encoding="utf-8")

    def _enqueue_retry(self, vehicle_type: str, brand_code: str, model_code: str, year_code: str, path: str, reason: str) -> None:
        item = {
            "vehicle_type": vehicle_type,
            "brand_code": str(brand_code),
            "model_code": str(model_code),
            "year_code": str(year_code),
            "path": path,
            "reason": reason,
            "created_at": utc_now(),
        }
        key = (item["vehicle_type"], item["brand_code"], item["model_code"], item["year_code"])
        existing_keys = {(i.get("vehicle_type"), i.get("brand_code"), i.get("model_code"), i.get("year_code")) for i in self._retry_queue}
        if key not in existing_keys:
            self._retry_queue.append(item)
        self._save_retry_queue()
        self._log(f"Item enviado para retentativa: {vehicle_type}/{brand_code}/{model_code}/{year_code}")

    def _drain_retry_queue(self, repo: CatalogRepository) -> CatalogUpsertStats:
        stats = CatalogUpsertStats()
        if not self._retry_queue:
            return stats
        pending = list(self._retry_queue)
        self._retry_queue = []
        self._save_retry_queue()
        self._log(f"Retomando fila de retentativa com {len(pending)} item(ns)")
        for item in pending:
            try:
                vehicle_type = str(item["vehicle_type"])
                brand_code = str(item["brand_code"])
                model_code = str(item["model_code"])
                year_code = str(item["year_code"])
                detail = self._get_json(vehicle_type, item["path"])
                brand = repo.get_brand(vehicle_type, brand_code)
                model = repo.get_model(brand.id, model_code) if brand else None
                if not brand or not model:
                    raise RuntimeError("Marca/modelo ausente para reprocessar versão FIPE")
                repo.upsert_version(brand, model, self._detail_to_payload(detail, year_code), stats)
                self._processed_versions += 1
                self._checkpoint(vehicle_type, brand_code, model_code, year_code, stage="retry_done", brand_index=None, model_index=None, version_index=None)
            except FipeRateLimitError as exc:
                self._retry_queue.append(item)
                stats.failed_items += 1
                stats.errors.append(f"Retentativa mantida na fila {item}: {exc}")
                self._log(f"Item enviado para retentativa: {item.get('vehicle_type')}/{item.get('brand_code')}/{item.get('model_code')}/{item.get('year_code')}")
            except Exception as exc:  # noqa: BLE001
                stats.failed_items += 1
                stats.errors.append(f"Falha retentativa {item}: {exc}")
        self._save_retry_queue()
        repo.commit()
        return stats

    def _log(self, message: str) -> None:
        print(f"[FIPE] {utc_now()} | {message}")

    def _log_progress(self, vehicle_type: str, current: int, total: int, detail: str) -> None:
        elapsed = max(time.monotonic() - self.started_at, 0.001)
        speed = self._processed_versions / elapsed if self._processed_versions else 0.0
        self._log(f"tipo={vehicle_type} progresso={current}/{total} detalhe={detail} tempo={elapsed:.1f}s velocidade={speed:.2f} versões/s")

    def _log_eta(self, vehicle_type: str, brand_name: str | None, model_name: str | None, version_index: int, total_versions: int) -> None:
        elapsed = max(time.monotonic() - self.started_at, 0.001)
        speed = self._processed_versions / elapsed if self._processed_versions else 0.0
        remaining_in_model = max(total_versions - version_index, 0)
        eta = remaining_in_model / speed if speed > 0 else None
        eta_text = f"ETA modelo ~{eta:.1f}s" if eta is not None else "ETA calculando"
        self._log(f"{vehicle_type} | {brand_name} / {model_name} | versões {version_index}/{total_versions} | {eta_text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincronização completa do catálogo FIPE.")
    parser.add_argument("--type", choices=list(TYPE_PATHS), action="append", dest="types")
    parser.add_argument("--max-brands", type=int, default=None)
    parser.add_argument("--max-models", type=int, default=None)
    parser.add_argument("--max-versions", type=int, default=None)
    parser.add_argument("--only-brands", action="store_true")
    parser.add_argument("--only-models", action="store_true")
    parser.add_argument("--only-versions", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--confirm-full-sync", action="store_true", help="Confirma execução completa. Obrigatório para evitar coleta acidental longa.")
    args = parser.parse_args()
    if not args.confirm_full_sync:
        print(json.dumps({"status": "cancelled", "message": "Full sync cancelada. Use --confirm-full-sync para confirmar execução completa."}, ensure_ascii=False, indent=2))
        return
    print(json.dumps(FipeFullSync().run(vehicle_types=args.types, max_brands=args.max_brands, max_models=args.max_models, max_versions=args.max_versions, only_brands=args.only_brands, only_models=args.only_models, only_versions=args.only_versions, resume=not args.no_resume), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
