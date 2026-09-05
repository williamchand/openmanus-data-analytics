import os
import csv
import sqlite3

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "use_case", "logistic_data", "mock_logistics_data.csv")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "logistics.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS logistics (
    client_id TEXT NOT NULL,
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    delivery_date TEXT,
    carrier TEXT NOT NULL,
    origin_city TEXT NOT NULL,
    destination_city TEXT NOT NULL,
    status TEXT NOT NULL,
    sku TEXT NOT NULL,
    product_category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price_usd REAL NOT NULL,
    order_value_usd REAL NOT NULL,
    is_promo INTEGER NOT NULL,
    promo_discount_pct REAL NOT NULL,
    region TEXT NOT NULL,
    warehouse TEXT NOT NULL
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_logistics_order_date ON logistics(order_date);",
    "CREATE INDEX IF NOT EXISTS idx_logistics_carrier ON logistics(carrier);",
    "CREATE INDEX IF NOT EXISTS idx_logistics_status ON logistics(status);",
    "CREATE INDEX IF NOT EXISTS idx_logistics_sku ON logistics(sku);",
    "CREATE INDEX IF NOT EXISTS idx_logistics_region ON logistics(region);"
]

def migrate():
    abs_csv = os.path.abspath(CSV_PATH)
    abs_db = os.path.abspath(DB_PATH)
    print(f"Migrating CSV from {abs_csv} to SQLite DB at {abs_db}...")

    if not os.path.exists(abs_csv):
        raise FileNotFoundError(f"CSV file not found at {abs_csv}")

    conn = sqlite3.connect(abs_db)
    cursor = conn.cursor()

    cursor.execute(CREATE_TABLE_SQL)
    for idx_sql in CREATE_INDEXES_SQL:
        cursor.execute(idx_sql)

    # Clear existing data to allow re-runs
    cursor.execute("DELETE FROM logistics;")

    with open(abs_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT INTO logistics (
                    client_id, order_id, order_date, delivery_date, carrier,
                    origin_city, destination_city, status, sku, product_category,
                    quantity, unit_price_usd, order_value_usd, is_promo,
                    promo_discount_pct, region, warehouse
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                row['client_id'],
                row['order_id'],
                row['order_date'],
                row['delivery_date'] if row['delivery_date'] else None,
                row['carrier'],
                row['origin_city'],
                row['destination_city'],
                row['status'],
                row['sku'],
                row['product_category'],
                int(row['quantity']),
                float(row['unit_price_usd']),
                float(row['order_value_usd']),
                int(row['is_promo']),
                float(row['promo_discount_pct']),
                row['region'],
                row['warehouse']
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"Successfully migrated {count} records to SQLite database.")

if __name__ == "__main__":
    migrate()
