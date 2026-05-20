from normalizers.vehicle_normalizer import VehicleNormalizer


def test_normalizer_maps_common_fields():
    record = {
        "brand": "Chevrolet",
        "model": "Tracker",
        "version": "Premier 1.2 turbo",
        "year": "2023",
        "mileage": "32.000 km",
        "price": "R$ 118.900",
        "city": "Santo André",
        "state": "SP",
        "source": "CSV",
    }
    out = VehicleNormalizer().normalize(record)
    assert out["marca"] == "Chevrolet"
    assert out["modelo"] == "Tracker"
    assert out["ano"] == 2023
    assert out["km"] == 32000
    assert out["preco"] == 118900.0
    assert out["estado"] == "SP"
    assert out["normalizado"] is True
    assert out["qualidade_dado"] > 0.7
