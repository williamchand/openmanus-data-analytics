import os
import sqlite3
from typing import Any, Dict, List, Tuple


# Check environment for PostgreSQL / Supabase connection URL
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DATABASE_URL")

IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "logistics.db")


def get_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def execute_query(query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        if IS_POSTGRES:
            # Replace sqlite strftime / julianday functions or placeholder if needed
            pg_query = query.replace("?", "%s")
            # Convert strftime('%Y-%m', order_date) to to_char(order_date::date, 'YYYY-MM')
            pg_query = pg_query.replace(
                "strftime('%Y-%m', order_date)", "to_char(order_date::date, 'YYYY-MM')"
            )
            pg_query = pg_query.replace(
                "strftime('%Y-%W', order_date)", "to_char(order_date::date, 'YYYY-IW')"
            )
            pg_query = pg_query.replace(
                "julianday(delivery_date) - julianday(order_date)",
                "EXTRACT(DAY FROM (delivery_date::timestamp - order_date::timestamp))",
            )

            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(pg_query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        else:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def get_placeholder() -> str:
    return "%s" if IS_POSTGRES else "?"
