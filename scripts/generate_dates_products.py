"""
Generates dim_dates.csv and dim_products.csv for the Daxwell-inspired
operations intelligence project.

Grain:
  dim_dates    -> one row per calendar day
  dim_products -> one row per SKU
"""

import pandas as pd
import numpy as np
from datetime import date

# Reproducibility: same "random" data every time we run this.
np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. dim_dates
# ---------------------------------------------------------------------------
START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)

def build_dim_dates(start: date, end: date) -> pd.DataFrame:
    all_days = pd.date_range(start, end, freq="D")

    dim_dates = pd.DataFrame({"date": all_days})
    dim_dates["day"] = dim_dates["date"].dt.day
    dim_dates["month"] = dim_dates["date"].dt.month
    dim_dates["month_name"] = dim_dates["date"].dt.strftime("%B")
    dim_dates["quarter"] = dim_dates["date"].dt.quarter
    dim_dates["year"] = dim_dates["date"].dt.year
    dim_dates["day_of_week"] = dim_dates["date"].dt.strftime("%A")
    dim_dates["is_weekend"] = dim_dates["date"].dt.dayofweek >= 5

    fixed_holidays = {
        (1, 1),    # New Year's Day
        (7, 4),    # Independence Day
        (11, 11),  # Veterans Day
        (12, 25),  # Christmas
    }
    dim_dates["is_holiday"] = dim_dates["date"].apply(
        lambda d: (d.month, d.day) in fixed_holidays
    )

    dim_dates["date"] = dim_dates["date"].dt.strftime("%Y-%m-%d")
    return dim_dates


# ---------------------------------------------------------------------------
# 2. dim_products
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = [
    ("Gloves", "Nitrile Exam Gloves - M", 4.20, 6.99),
    ("Gloves", "Nitrile Exam Gloves - L", 4.35, 7.19),
    ("Gloves", "Vinyl Food-Prep Gloves", 2.10, 3.49),
    ("PPE", "3-Ply Face Masks (Box 50)", 3.80, 6.49),
    ("PPE", "Isolation Gowns", 5.60, 8.99),
    ("Tableware", "Compostable Plates 9in", 1.90, 3.29),
    ("Tableware", "Plastic Cutlery Kits", 1.40, 2.59),
    ("Food Packaging", "Aluminum Foil Rolls 18in", 3.10, 5.29),
    ("Food Packaging", "Take-Out Containers", 2.60, 4.49),
    ("Food Packaging", "Paper Straws (Box 500)", 2.20, 3.99),
]

def build_dim_products(catalog: list[tuple]) -> pd.DataFrame:
    rows = []
    for i, (category, name, unit_cost, list_price) in enumerate(catalog, start=1):
        rows.append({
            "product_id": f"P{i:04d}",
            "product_name": name,
            "category": category,
            "unit_of_measure": "case",
            "unit_cost": unit_cost,
            "list_price": list_price,
            "is_active": True,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    dim_dates = build_dim_dates(START_DATE, END_DATE)
    dim_products = build_dim_products(PRODUCT_CATALOG)

    dim_dates.to_csv("data/raw/dim_dates.csv", index=False)
    dim_products.to_csv("data/raw/dim_products.csv", index=False)

    print(f"dim_dates.csv    -> {len(dim_dates):,} rows")
    print(f"dim_products.csv -> {len(dim_products):,} rows")
    print("\nSample dim_dates:")
    print(dim_dates.head(3).to_string(index=False))
    print("\nSample dim_products:")
    print(dim_products.head(3).to_string(index=False))