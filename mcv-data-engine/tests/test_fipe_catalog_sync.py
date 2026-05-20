from __future__ import annotations
from sqlalchemy import create_engine, select
from storage.models import Base, get_session_factory, VehicleBrand, VehicleModelMaster, VehicleVersion
from vehicle_catalog.fipe_full_sync import FipeFullSync

class FakeClient:
    def get_json(self, url: str):
        if url.endswith('/marcas'):
            return [{"codigo": "23", "nome": "GM"}]
        if url.endswith('/marcas/23/modelos'):
            return {"modelos": [{"codigo": "1001", "nome": "Agile"}]}
        if url.endswith('/marcas/23/modelos/1001/anos'):
            return [{"codigo": "2013-1", "nome": "2013 Flex"}]
        if url.endswith('/marcas/23/modelos/1001/anos/2013-1'):
            return {"Valor": "R$ 38.900,00", "Marca": "GM", "Modelo": "Agile LTZ 1.4 Flex", "AnoModelo": 2013, "Combustivel": "Flex", "CodigoFipe": "004381-1", "MesReferencia": "maio/2026"}
        raise AssertionError(url)


def test_fipe_full_sync_amostra_incremental_sem_duplicar(tmp_path, monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    import vehicle_catalog.fipe_full_sync as sync_module
    monkeypatch.setattr(sync_module, "init_db", lambda: engine)
    monkeypatch.setattr(sync_module, "get_session_factory", lambda engine_arg: get_session_factory(engine))
    sync = FipeFullSync(client=FakeClient(), export_dir=tmp_path)
    sync.sleep_seconds = 0
    first = sync.run(vehicle_types=["carros"])
    second = sync.run(vehicle_types=["carros"])
    Session = get_session_factory(engine)
    with Session() as session:
        assert len(session.scalars(select(VehicleBrand)).all()) == 1
        assert len(session.scalars(select(VehicleModelMaster)).all()) == 1
        assert len(session.scalars(select(VehicleVersion)).all()) == 1
    assert first["stats"]["new_versions"] == 1
    assert second["stats"]["new_versions"] == 0
    assert second["stats"]["skipped_existing"] >= 1
