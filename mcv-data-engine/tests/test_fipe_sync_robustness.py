from __future__ import annotations
import json
import sys
from pathlib import Path
from sqlalchemy import create_engine, select

from storage.models import Base, get_session_factory, VehicleVersion
from vehicle_catalog.fipe_full_sync import FipeFullSync, main as full_main
from vehicle_catalog.fipe_incremental_sync import FipeIncrementalSync


class MultiFakeClient:
    def get_json(self, url: str):
        if url.endswith('/marcas'):
            return [{"codigo": "23", "nome": "GM"}, {"codigo": "59", "nome": "VW"}]
        if url.endswith('/marcas/23/modelos'):
            return {"modelos": [{"codigo": "1001", "nome": "Agile"}, {"codigo": "1002", "nome": "Celta"}]}
        if url.endswith('/marcas/59/modelos'):
            return {"modelos": [{"codigo": "2001", "nome": "Gol"}]}
        if url.endswith('/marcas/23/modelos/1001/anos'):
            return [{"codigo": "2013-1", "nome": "2013 Flex"}, {"codigo": "2014-1", "nome": "2014 Flex"}]
        if url.endswith('/marcas/23/modelos/1002/anos'):
            return [{"codigo": "2012-1", "nome": "2012 Flex"}]
        if url.endswith('/marcas/59/modelos/2001/anos'):
            return [{"codigo": "2015-1", "nome": "2015 Flex"}]
        if '/anos/' in url:
            year_code = url.rsplit('/', 1)[-1]
            year = int(year_code.split('-')[0])
            return {"Valor": "R$ 38.900,00", "Marca": "GM", "Modelo": "Agile LTZ 1.4 Flex", "AnoModelo": year, "Combustivel": "Flex", "CodigoFipe": f"004{year}-1", "MesReferencia": "maio/2026"}
        raise AssertionError(url)


def _patch_db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    import vehicle_catalog.fipe_full_sync as full_module
    import vehicle_catalog.catalog_manifest as manifest_module
    import vehicle_catalog.catalog_search_index as search_module
    monkeypatch.setattr(full_module, "init_db", lambda: engine)
    monkeypatch.setattr(full_module, "get_session_factory", lambda engine_arg: get_session_factory(engine))
    monkeypatch.setattr(manifest_module, "init_db", lambda: engine)
    monkeypatch.setattr(manifest_module, "get_session_factory", lambda engine_arg: get_session_factory(engine))
    monkeypatch.setattr(search_module, "init_db", lambda: engine)
    monkeypatch.setattr(search_module, "get_session_factory", lambda engine_arg: get_session_factory(engine))
    return engine


def test_full_sync_sem_confirmacao_cancela(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["fipe_full_sync"])
    full_main()
    out = capsys.readouterr().out
    assert "cancelled" in out
    assert "--confirm-full-sync" in out


def test_incremental_com_limites_e_export_automatico(tmp_path, monkeypatch):
    engine = _patch_db(monkeypatch)
    sync = FipeIncrementalSync(client=MultiFakeClient(), export_dir=tmp_path)
    sync.sleep_seconds = 0
    sync.checkpoint_path = tmp_path / "checkpoint.json"
    result = sync.run(vehicle_types=["carros"], max_brands=1, max_models=1, max_versions=1)
    assert result["totals"] == {"brands": 1, "models": 1, "versions": 1}
    assert (tmp_path / "vehicle_catalog_full.csv").exists()
    assert (tmp_path / "vehicle_search_index.csv").exists()
    assert (tmp_path / "catalog_manifest.json").exists()
    assert sync.checkpoint_path.exists()
    Session = get_session_factory(engine)
    with Session() as session:
        assert len(session.scalars(select(VehicleVersion)).all()) == 1


def test_incremental_duas_execucoes_nao_duplica_e_manifest_expandido(tmp_path, monkeypatch):
    engine = _patch_db(monkeypatch)
    sync = FipeIncrementalSync(client=MultiFakeClient(), export_dir=tmp_path)
    sync.sleep_seconds = 0
    sync.checkpoint_path = tmp_path / "checkpoint.json"
    sync.run(vehicle_types=["carros"], max_brands=1, max_models=1, max_versions=1)
    second = sync.run(vehicle_types=["carros"], max_brands=1, max_models=1, max_versions=1)
    assert second["stats"]["new_versions"] == 0
    assert second["manifest"]["schema_version"] == "catalog.v2"
    assert second["manifest"]["skipped"] >= 1
    Session = get_session_factory(engine)
    with Session() as session:
        assert len(session.scalars(select(VehicleVersion)).all()) == 1


class RateLimitThenSuccessClient(MultiFakeClient):
    def __init__(self, failures_before_success: int = 1):
        self.failures_before_success = failures_before_success
        self.calls_by_url = {}

    def get_json(self, url: str):
        if '/anos/' in url:
            count = self.calls_by_url.get(url, 0)
            self.calls_by_url[url] = count + 1
            if count < self.failures_before_success:
                raise RuntimeError('HTTP 429 Too Many Requests')
        return super().get_json(url)


class AlwaysRateLimitDetailClient(MultiFakeClient):
    def get_json(self, url: str):
        if '/anos/' in url:
            raise RuntimeError('HTTP 429 Too Many Requests')
        return super().get_json(url)


def test_fipe_429_retry_backoff_e_continua_sem_perder_item(tmp_path, monkeypatch, capsys):
    engine = _patch_db(monkeypatch)
    sleeps = []
    import vehicle_catalog.fipe_full_sync as full_module
    monkeypatch.setattr(full_module.time, 'sleep', lambda seconds: sleeps.append(seconds))
    sync = FipeIncrementalSync(client=RateLimitThenSuccessClient(failures_before_success=1), export_dir=tmp_path)
    sync.checkpoint_path = tmp_path / 'checkpoint.json'
    sync.retry_queue_path = tmp_path / 'retry_queue.json'
    sync.sleep_seconds = 0
    result = sync.run(vehicle_types=['carros'], max_brands=1, max_models=1, max_versions=1)
    out = capsys.readouterr().out
    assert 'Limite detectado' in out
    assert 'Aguardando 5 segundos' in out
    assert result['totals']['versions'] == 1
    assert sleeps[0] == 5
    Session = get_session_factory(engine)
    with Session() as session:
        assert len(session.scalars(select(VehicleVersion)).all()) == 1


def test_fipe_429_cooldown_global_salva_checkpoint(tmp_path, monkeypatch, capsys):
    _patch_db(monkeypatch)
    sleeps = []
    import vehicle_catalog.fipe_full_sync as full_module
    monkeypatch.setattr(full_module.time, 'sleep', lambda seconds: sleeps.append(seconds))
    sync = FipeIncrementalSync(client=AlwaysRateLimitDetailClient(), export_dir=tmp_path)
    sync.checkpoint_path = tmp_path / 'checkpoint.json'
    sync.retry_queue_path = tmp_path / 'retry_queue.json'
    sync.sleep_seconds = 0
    sync.max_retries = 2
    sync.max_429_before_cooldown = 2
    sync.cooldown_seconds = 300
    sync.run(vehicle_types=['carros'], max_brands=1, max_models=1, max_versions=1)
    out = capsys.readouterr().out
    assert 'cooldown global' in out
    assert 'Retomando do checkpoint' in out
    assert 300 in sleeps
    checkpoint = json.loads(sync.checkpoint_path.read_text(encoding='utf-8'))
    assert checkpoint['stage'] == 'version'
    assert checkpoint['year_code'] == '2013-1'


def test_fipe_429_retry_queue_item_nao_perdido(tmp_path, monkeypatch):
    _patch_db(monkeypatch)
    import vehicle_catalog.fipe_full_sync as full_module
    monkeypatch.setattr(full_module.time, 'sleep', lambda seconds: None)
    sync = FipeIncrementalSync(client=AlwaysRateLimitDetailClient(), export_dir=tmp_path)
    sync.checkpoint_path = tmp_path / 'checkpoint.json'
    sync.retry_queue_path = tmp_path / 'retry_queue.json'
    sync.sleep_seconds = 0
    sync.max_retries = 1
    sync.run(vehicle_types=['carros'], max_brands=1, max_models=1, max_versions=1)
    queue = json.loads(sync.retry_queue_path.read_text(encoding='utf-8'))
    assert len(queue) == 1
    assert queue[0]['year_code'] == '2013-1'
    assert queue[0]['path'].endswith('/anos/2013-1')
