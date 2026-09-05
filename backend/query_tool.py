import sqlite3
import os
import re
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "logistics.db")

def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class QueryTool:
    """
    Validated read-only SQL and analytics query tool for logistics data.
    Ensures safe execution and structured output formatting.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_dashboard_kpis(self, time_range_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates core KPIs:
        - Total Orders
        - Delivered Orders
        - Delayed Orders
        - On-Time Delivery Rate (%)
        - Average Delivery Time (days)
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        where_clause = ""
        params = []
        if time_range_days:
            where_clause = "WHERE order_date >= date((SELECT MAX(order_date) FROM logistics), ?)"
            params.append(f"-{time_range_days} days")

        sql = f"""
        SELECT
            COUNT(*) as total_orders,
            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
            SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END) as delayed_orders,
            SUM(CASE WHEN status = 'canceled' THEN 1 ELSE 0 END) as canceled_orders,
            SUM(CASE WHEN status = 'in_transit' THEN 1 ELSE 0 END) as in_transit_orders,
            SUM(CASE WHEN status = 'exception' THEN 1 ELSE 0 END) as exception_orders,
            AVG(CASE
                WHEN delivery_date IS NOT NULL AND delivery_date != ''
                THEN julianday(delivery_date) - julianday(order_date)
                ELSE NULL
            END) as avg_delivery_days,
            ROUND(SUM(order_value_usd), 2) as total_revenue
        FROM logistics {where_clause};
        """

        cursor.execute(sql, params)
        row = cursor.fetchone()
        conn.close()

        total = row['total_orders'] or 0
        delivered = row['delivered_orders'] or 0
        delayed = row['delayed_orders'] or 0

        # On-time rate is delivered / (delivered + delayed) or delivered / total shipped
        shipped = delivered + delayed
        on_time_rate = round((delivered / shipped * 100), 2) if shipped > 0 else 100.0
        avg_delivery_time = round(row['avg_delivery_days'] or 0.0, 1)

        return {
            "total_orders": total,
            "delivered_orders": delivered,
            "delayed_orders": delayed,
            "canceled_orders": row['canceled_orders'] or 0,
            "in_transit_orders": row['in_transit_orders'] or 0,
            "exception_orders": row['exception_orders'] or 0,
            "on_time_delivery_rate_pct": on_time_rate,
            "avg_delivery_time_days": avg_delivery_time,
            "total_revenue_usd": row['total_revenue'] or 0.0
        }

    def execute_analytical_query(
        self,
        select_clause: str,
        group_by: Optional[str] = None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Executes structured read-only analytics query.
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        query = f"SELECT {select_clause} FROM logistics"
        if where_clause:
            query += f" WHERE {where_clause}"
        if group_by:
            query += f" GROUP BY {group_by}"
        if order_by:
            query += f" ORDER BY {order_by}"
        query += f" LIMIT {int(limit)}"

        # Verify safety (prevent state modifications)
        cleaned_query = query.strip().upper()
        if not cleaned_query.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
        for forbidden in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", ";"]:
            if forbidden in cleaned_query:
                raise ValueError(f"Forbidden SQL keywords found: {forbidden}")

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
