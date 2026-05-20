from fastapi.testclient import TestClient

from api.main import app


def test_api_comparables_endpoint_shape():
    client = TestClient(app)
    response = client.get(
        "/market/comparables",
        params={"brand": "Toyota", "model": "Corolla", "year": 2020, "mileage": 40000, "state": "SP", "limit": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "target" in payload
    assert "comparables" in payload
    assert "sample_statistics" in payload
    assert "outliers_removed" in payload
