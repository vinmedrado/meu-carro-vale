from fastapi.testclient import TestClient

from api.main import app


def test_market_behavior_endpoint_empty_database_is_safe():
    client = TestClient(app)
    response = client.get('/market/behavior?brand=Toyota&model=Corolla&year=2021&state=SP')
    assert response.status_code == 200
    payload = response.json()
    assert 'behavior' in payload
    assert payload['behavior']['market_behavior_summary']


def test_market_pressure_endpoint_empty_database_is_safe():
    client = TestClient(app)
    response = client.get('/market/price-pressure?brand=Toyota&model=Corolla&year=2021&preco=120000')
    assert response.status_code == 200
    assert 'price_pressure' in response.json()
