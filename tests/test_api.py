import pytest
from fastapi.testclient import TestClient

from backend.main import app
from scripts.migrate_to_sqlite import migrate


@pytest.fixture(scope="module")
def client():
    migrate()
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_get_kpis(client):
    res = client.get("/api/kpis")
    assert res.status_code == 200
    data = res.json()
    assert data["total_orders"] == 400
    assert "on_time_delivery_rate_pct" in data


def test_get_order_volume(client):
    res = client.get("/api/charts/order-volume")
    assert res.status_code == 200
    data = res.json()
    assert "chart_data" in data
    assert len(data["chart_data"]) > 0


def test_ask_ai_carrier_query(client):
    res = client.post(
        "/api/ask-ai", json={"question": "Which carrier has the highest delay rate?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "carrier_delay_analysis"
    assert "explainability" in data
    assert len(data["chart_data"]) > 0


def test_ask_ai_forecasting_query(client):
    res = client.post(
        "/api/ask-ai",
        json={"question": "Predict demand for SKU PAPER-0197 for the next 4 months"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "predictive_forecasting"
    assert "methodology" in data["explainability"]


def test_ask_ai_empty_question(client):
    res = client.post("/api/ask-ai", json={"question": ""})
    assert res.status_code == 400
