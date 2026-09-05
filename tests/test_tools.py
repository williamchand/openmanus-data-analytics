import pytest

from backend.forecasting_tool import ForecastingTool
from backend.query_tool import QueryTool
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
        order_by="cnt DESC",
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


def test_postgres_query_transformations(monkeypatch, setup_db):
    from unittest.mock import MagicMock
    import backend.db as db_module

    executed_queries = []

    class DummyCursor:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def execute(self, query, params=()):
            executed_queries.append((query, params))
        def fetchall(self):
            return [{"cnt": 1}]

    class DummyConn:
        def cursor(self, cursor_factory=None):
            return DummyCursor()
        def close(self):
            pass

    monkeypatch.setattr(db_module, "IS_POSTGRES", True)
    monkeypatch.setattr(db_module, "get_connection", lambda: DummyConn())

    q = "SELECT delivery_date != '' as is_deliv, CAST(val AS FLOAT) as val_num FROM logistics"
    db_module.execute_query(q)

    assert len(executed_queries) == 1
    transformed = executed_queries[0][0]
    assert "delivery_date::text != ''" in transformed
    assert "AS NUMERIC" in transformed
