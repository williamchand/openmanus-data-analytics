import csv
import os
import sys

import psycopg2


CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "examples",
    "use_case",
    "logistic_data",
    "mock_logistics_data.csv",
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS logistics (
    client_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(100) PRIMARY KEY,
    order_date DATE NOT NULL,
    delivery_date DATE,
    carrier VARCHAR(50) NOT NULL,
    origin_city VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    product_category VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price_usd NUMERIC(10, 2) NOT NULL,
    order_value_usd NUMERIC(10, 2) NOT NULL,
    is_promo INTEGER NOT NULL,
    promo_discount_pct NUMERIC(5, 2) NOT NULL,
    region VARCHAR(50) NOT NULL,
    warehouse VARCHAR(50) NOT NULL
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_pg_logistics_order_date ON logistics(order_date);",
    "CREATE INDEX IF NOT EXISTS idx_pg_logistics_carrier ON logistics(carrier);",
    "CREATE INDEX IF NOT EXISTS idx_pg_logistics_status ON logistics(status);",
    "CREATE INDEX IF NOT EXISTS idx_pg_logistics_sku ON logistics(sku);",
    "CREATE INDEX IF NOT EXISTS idx_pg_logistics_region ON logistics(region);",
]


def migrate_to_postgres():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DATABASE_URL")
    if not db_url:
        print(
            "Error: DATABASE_URL or SUPABASE_DATABASE_URL environment variable is required."
        )
        sys.exit(1)

    print(f"Connecting to PostgreSQL / Supabase...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    cursor.execute(CREATE_TABLE_SQL)
    for idx_sql in CREATE_INDEXES_SQL:
        cursor.execute(idx_sql)

    cursor.execute("TRUNCATE TABLE logistics;")

    abs_csv = os.path.abspath(CSV_PATH)
    with open(abs_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute(
                """
                INSERT INTO logistics (
                    client_id, order_id, order_date, delivery_date, carrier,
                    origin_city, destination_city, status, sku, product_category,
                    quantity, unit_price_usd, order_value_usd, is_promo,
                    promo_discount_pct, region, warehouse
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
                (
                    row["client_id"],
                    row["order_id"],
                    row["order_date"],
                    row["delivery_date"] if row["delivery_date"] else None,
                    row["carrier"],
                    row["origin_city"],
                    row["destination_city"],
                    row["status"],
                    row["sku"],
                    row["product_category"],
                    int(row["quantity"]),
                    float(row["unit_price_usd"]),
                    float(row["order_value_usd"]),
                    int(row["is_promo"]),
                    float(row["promo_discount_pct"]),
                    row["region"],
                    row["warehouse"],
                ),
            )
            count += 1

    conn.commit()
    conn.close()
    print(f"Successfully migrated {count} records to Supabase PostgreSQL database.")


if __name__ == "__main__":
    migrate_to_postgres()
