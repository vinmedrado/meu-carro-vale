from __future__ import annotations
import argparse
import json
from .fipe_full_sync import FipeFullSync

class FipeIncrementalSync(FipeFullSync):
    """Sincronização incremental idempotente.

    Usa os mesmos upserts/deduplicação do full sync, mas não exige confirmação e
    é segura para automação recorrente. Gera exports e manifest automaticamente.
    """
    def run(self, vehicle_types: list[str] | None = None, max_brands: int | None = None, max_models: int | None = None, max_versions: int | None = None, only_brands: bool = False, only_models: bool = False, only_versions: bool = False, resume: bool = True) -> dict:
        result = super().run(vehicle_types=vehicle_types, max_brands=max_brands, max_models=max_models, max_versions=max_versions, only_brands=only_brands, only_models=only_models, only_versions=only_versions, resume=resume)
        result["run_type"] = "incremental"
        if isinstance(result.get("manifest"), dict):
            result["manifest"]["modo_execucao"] = "incremental"
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincronização incremental do catálogo FIPE.")
    parser.add_argument("--type", choices=["carros", "motos", "caminhoes"], action="append", dest="types")
    parser.add_argument("--max-brands", type=int, default=None)
    parser.add_argument("--max-models", type=int, default=None)
    parser.add_argument("--max-versions", type=int, default=None)
    parser.add_argument("--only-brands", action="store_true")
    parser.add_argument("--only-models", action="store_true")
    parser.add_argument("--only-versions", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    print(json.dumps(FipeIncrementalSync().run(vehicle_types=args.types, max_brands=args.max_brands, max_models=args.max_models, max_versions=args.max_versions, only_brands=args.only_brands, only_models=args.only_models, only_versions=args.only_versions, resume=not args.no_resume), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
