"""
Loads all 8 raw CSVs into a single DuckDB database file.

This is intentionally simple -- straight load, no cleaning yet. We're
loading the data AS-IS, including the data-quality problems we seeded
on purpose. Cleaning that up is Phase 3/4's job, not this script's.
"""

import duckdb

con = duckdb.connect("data/daxwell.duckdb")

tables = {
    "dim_dates": "data/raw/dim_dates.csv",
    "dim_products": "data/raw/dim_products.csv",
    "dim_customers": "data/raw/dim_customers.csv",
    "dim_suppliers": "data/raw/dim_suppliers.csv",
    "fact_sales": "data/raw/fact_sales.csv",
    "fact_inventory_snapshot": "data/raw/fact_inventory_snapshot.csv",
    "fact_purchase_orders": "data/raw/fact_purchase_orders.csv",
    "fact_pricing_history": "data/raw/fact_pricing_history.csv",
}

for table_name, csv_path in tables.items():
    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM read_csv_auto('{csv_path}')
    """)

print("Tables loaded into data/daxwell.duckdb:\n")
for table_name in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  {table_name:28s} {count:>8,} rows")

print("\nSchema check -- fact_sales columns and types:")
print(con.execute("DESCRIBE fact_sales").fetchdf().to_string(index=False))

con.close()