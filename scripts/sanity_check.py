"""
Sanity check across the full synthetic dataset -- run this after all 8
CSVs exist. Confirms row counts look reasonable and does a quick
referential integrity pass (fact tables' foreign keys should all exist
in their dimension tables -- except where we deliberately broke that,
which this script should also surface).

This is deliberately lightweight -- a full data-quality FRAMEWORK is
Phase 4. This step just confirms Phase 1 is internally consistent
before we commit it.
"""

import pandas as pd

files = {
    "dim_dates": "data/raw/dim_dates.csv",
    "dim_products": "data/raw/dim_products.csv",
    "dim_customers": "data/raw/dim_customers.csv",
    "dim_suppliers": "data/raw/dim_suppliers.csv",
    "fact_sales": "data/raw/fact_sales.csv",
    "fact_inventory_snapshot": "data/raw/fact_inventory_snapshot.csv",
    "fact_purchase_orders": "data/raw/fact_purchase_orders.csv",
    "fact_pricing_history": "data/raw/fact_pricing_history.csv",
}

tables = {name: pd.read_csv(path) for name, path in files.items()}

print("=== Row counts ===")
for name, df in tables.items():
    print(f"{name:28s} {len(df):>8,} rows")

print("\n=== Referential integrity: fact_sales -> dim_products ===")
valid_products = set(tables["dim_products"]["product_id"])
orphaned = tables["fact_sales"][~tables["fact_sales"]["product_id"].isin(valid_products)]
print(f"Order lines referencing a product_id NOT in dim_products: {len(orphaned)}")
if len(orphaned) > 0:
    print(f"  Example bad product_id(s): {orphaned['product_id'].unique()[:3]}")

print("\n=== Referential integrity: fact_sales -> dim_customers ===")
valid_customers = set(tables["dim_customers"]["customer_id"])
null_or_bad_customer = tables["fact_sales"][
    tables["fact_sales"]["customer_id"].isna()
    | ~tables["fact_sales"]["customer_id"].isin(valid_customers | {None})
]
print(f"Order lines with missing/invalid customer_id: {len(null_or_bad_customer)}")

print("\n=== Known problems (should be non-zero -- these are our seeded issues) ===")
print(f"Duplicate sale_id values:    {tables['fact_sales']['sale_id'].duplicated().sum()}")
print(f"Negative quantity_sold:      {(tables['fact_sales']['quantity_sold'] < 0).sum()}")
print(f"Zero or negative unit_price: {(tables['fact_sales']['unit_price'] <= 0).sum()}")
print(f"Null date:                   {tables['fact_sales']['date'].isna().sum()}")

print("\n=== Date range check across fact tables ===")
print(f"fact_sales: {tables['fact_sales']['date'].min()} to {tables['fact_sales']['date'].max()}")
print(f"fact_inventory_snapshot: {tables['fact_inventory_snapshot']['snapshot_date'].min()} "
      f"to {tables['fact_inventory_snapshot']['snapshot_date'].max()}")