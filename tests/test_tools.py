import pytest
import os
import sqlite3
from backend.query_tool import QueryTool
from backend.forecasting_tool import ForecastingTool
from scripts.migrate_to_sqlite import migrate

@pytest.fixture(scope="module")
def setup_db():
    migrate()
    yield

def test_query_tool_kpis(setup_db):
    qt = QueryTool()
    kpis = qt.get_dashboard_kpis()
    assert kpis["total_orders"] == 400
    assert kpis["delivered_orders"] > 0
    assert kpis["delayed_orders"] > 0
    assert 0 <= kpis["on_time_delivery_rate_pct"] <= 100

def test_query_tool_analytical_query(setup_db):
    qt = QueryTool()
    res = qt.execute_analytical_query(
        select_clause="carrier, COUNT(*) as cnt",
        group_by="carrier",
        order_by="cnt DESC"
    )
    assert len(res) > 0
    assert "carrier" in res[0]
    assert "cnt" in res[0]

def test_query_tool_sql_injection_prevention(setup_db):
    qt = QueryTool()
    with pytest.raises(ValueError):
        qt.execute_analytical_query("DROP TABLE logistics")

def test_forecasting_tool(setup_db):
    ft = ForecastingTool()
    res = ft.predict_demand(months_ahead=4, method="exponential_smoothing")
    assert "forecast_data" in res
    assert len(res["forecast_data"]) == 4
    assert res["summary_metrics"]["recommended_procurement_units"] > 0

def test_forecasting_tool_sku(setup_db):
    ft = ForecastingTool()
    res = ft.predict_demand(sku="PAPER-0197", months_ahead=3)
    assert res["sku"] == "PAPER-0197"
    assert len(res["forecast_data"]) == 3
