from collectors.fipe_collector import FipeCollector


def test_fipe_detail_mapping():
    detail = {
        "Valor": "R$ 55.123,00",
        "Marca": "Fiat",
        "Modelo": "Argo Drive 1.0",
        "AnoModelo": 2021,
        "Combustivel": "Gasolina",
        "CodigoFipe": "001267-0",
        "MesReferencia": "maio de 2026",
    }
    out = FipeCollector().__class__._to_record(FipeCollector.__new__(FipeCollector), "Fiat", "Argo", detail)
    assert out["preco"] == 55123.0
    assert out["codigo_fipe"] == "001267-0"
