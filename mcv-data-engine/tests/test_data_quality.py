from ingestion.validators.data_quality_engine import DataQualityEngine
from normalizers.vehicle_normalizer import VehicleNormalizer


def test_data_quality_flags_missing_required_fields():
    record = VehicleNormalizer().normalize({"marca": "Toyota", "modelo": "Corolla", "ano": 2020})
    result = DataQualityEngine().evaluate(record)
    assert result.quality_score < 0.75
    assert any("campos_obrigatorios_ausentes" in e for e in result.validation_errors)


def test_advanced_normalization_corolla_xei():
    record = VehicleNormalizer().normalize({"marca": "Toyota", "modelo": "Corolla XEi", "versao": "2.0 flex cvt", "ano": "2021", "preco": "R$ 119.900", "estado": "sp"})
    assert record["modelo"] == "Corolla"
    assert record["versao"] == "2.0 FLEX CVT"
    assert record["preco"] == 119900.0
