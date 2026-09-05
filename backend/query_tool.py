from typing import Any, Dict, List, Optional

from backend.db import IS_POSTGRES, execute_query, get_placeholder


class QueryTool:
    """
    Validated read-only SQL and analytics query tool for logistics data.
    Supports both SQLite and PostgreSQL (Supabase).
    """

    def __init__(self):
        pass

    def get_dashboard_kpis(
        self, time_range_days: Optional[int] = None
    ) -> Dict[str, Any]:
        params = []
        where_clause = ""
        placeholder = get_placeholder()

        if time_range_days:
            if IS_POSTGRES:
                where_clause = f"WHERE order_date >= (SELECT MAX(order_date::date) FROM logistics) - INTERVAL '{time_range_days} days'"
            else:
                where_clause = f"WHERE order_date >= date((SELECT MAX(order_date) FROM logistics), {placeholder})"
                params.append(f"-{time_range_days} days")

        if IS_POSTGRES:
            avg_expr = "AVG(CASE WHEN delivery_date IS NOT NULL AND delivery_date != '' THEN (delivery_date::date - order_date::date) ELSE NULL END)"
        else:
            avg_expr = "AVG(CASE WHEN delivery_date IS NOT NULL AND delivery_date != '' THEN julianday(delivery_date) - julianday(order_date) ELSE NULL END)"

        sql = f"""
        SELECT
            COUNT(*) as total_orders,
            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
            SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END) as delayed_orders,
            SUM(CASE WHEN status = 'canceled' THEN 1 ELSE 0 END) as canceled_orders,
            SUM(CASE WHEN status = 'in_transit' THEN 1 ELSE 0 END) as in_transit_orders,
            SUM(CASE WHEN status = 'exception' THEN 1 ELSE 0 END) as exception_orders,
            {avg_expr} as avg_delivery_days,
            ROUND(CAST(SUM(order_value_usd) AS NUMERIC), 2) as total_revenue
        FROM logistics {where_clause};
        """

        rows = execute_query(sql, tuple(params))
        row = rows[0] if rows else {}

        total = row.get("total_orders") or 0
        delivered = row.get("delivered_orders") or 0
        delayed = row.get("delayed_orders") or 0

        shipped = delivered + delayed
        on_time_rate = round((delivered / shipped * 100), 2) if shipped > 0 else 100.0
        avg_delivery_time = round(float(row.get("avg_delivery_days") or 0.0), 1)

        return {
            "total_orders": total,
            "delivered_orders": delivered,
            "delayed_orders": delayed,
            "canceled_orders": row.get("canceled_orders") or 0,
            "in_transit_orders": row.get("in_transit_orders") or 0,
            "exception_orders": row.get("exception_orders") or 0,
            "on_time_delivery_rate_pct": on_time_rate,
            "avg_delivery_time_days": avg_delivery_time,
            "total_revenue_usd": float(row.get("total_revenue") or 0.0),
        }

    def execute_analytical_query(
        self,
        select_clause: str,
        group_by: Optional[str] = None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        query = f"SELECT {select_clause} FROM logistics"
        if where_clause:
            query += f" WHERE {where_clause}"
        if group_by:
            query += f" GROUP BY {group_by}"
        if order_by:
            query += f" ORDER BY {order_by}"
        query += f" LIMIT {int(limit)}"

        cleaned_query = query.strip().upper()
        if not cleaned_query.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
        for forbidden in [
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",
            "ALTER",
            "TRUNCATE",
            ";",
        ]:
            if forbidden in cleaned_query:
                raise ValueError(f"Forbidden SQL keywords found: {forbidden}")

        return execute_query(query)
