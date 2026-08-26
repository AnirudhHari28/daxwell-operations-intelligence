"""
Generates fact_pricing_history.csv for the Daxwell-inspired operations
intelligence project.

Grain: one row per product per price-effective-date.

This is a Type-2-style slowly changing dimension in fact-table form:
rather than overwriting dim_products' price whenever it changes, every
change gets its own dated row, so historical sales can always be joined
back to the price that was ACTUALLY in effect at the time.

Depends on: dim_products.csv
"""

import pandas as pd
import numpy as np

np.random.seed(42)

dim_products = pd.read_csv("data/raw/dim_products.csv")

# Annual repricing -- a normal, expected cost-of-living style adjustment
ANNUAL_EFFECTIVE_DATES = [
    pd.Timestamp("2023-01-01"),
    pd.Timestamp("2024-01-01"),
    pd.Timestamp("2025-01-01"),
]

# Reinforces the margin-problem story from fact_sales: this product's cost
# jumps meaningfully mid-2025, but list price is NOT adjusted to compensate
# -- exactly the kind of thing a pricing analyst should catch and flag.
MARGIN_PROBLEM_PRODUCT = "P0006"
UNPLANNED_COST_INCREASE_DATE = pd.Timestamp("2025-06-01")
UNPLANNED_COST_INCREASE_PCT = 0.15


def build_fact_pricing_history() -> pd.DataFrame:
    rows = []

    for _, product in dim_products.iterrows():
        pid = product["product_id"]
        cost = product["unit_cost"]
        price = product["list_price"]

        for i, effective_date in enumerate(ANNUAL_EFFECTIVE_DATES):
            if i > 0:
                # Small annual inflation-style bump, 3-6%
                bump = np.random.uniform(0.03, 0.06)
                cost = round(cost * (1 + bump), 2)
                price = round(price * (1 + bump), 2)

            rows.append({
                "product_id": pid,
                "effective_date": effective_date.strftime("%Y-%m-%d"),
                "unit_cost": cost,
                "list_price": price,
            })

        if pid == MARGIN_PROBLEM_PRODUCT:
            cost = round(cost * (1 + UNPLANNED_COST_INCREASE_PCT), 2)
            # Deliberately NOT increasing price here -- that's the whole point
            rows.append({
                "product_id": pid,
                "effective_date": UNPLANNED_COST_INCREASE_DATE.strftime("%Y-%m-%d"),
                "unit_cost": cost,
                "list_price": price,
            })

    df = pd.DataFrame(rows)
    return df.sort_values(["product_id", "effective_date"]).reset_index(drop=True)


if __name__ == "__main__":
    fact_pricing = build_fact_pricing_history()
    fact_pricing.to_csv("data/raw/fact_pricing_history.csv", index=False)

    print(f"fact_pricing_history.csv -> {len(fact_pricing):,} rows")

    print("\n--- Row count per product (most should have 3, P0006 should have 4) ---")
    print(fact_pricing["product_id"].value_counts().sort_index())

    print(f"\n--- Full price/cost history for {MARGIN_PROBLEM_PRODUCT} ---")
    print(fact_pricing[fact_pricing["product_id"] == MARGIN_PROBLEM_PRODUCT].to_string(index=False))

    print("\n--- Margin % implied at each point for P0006 (list_price - cost) / list_price ---")
    p6 = fact_pricing[fact_pricing["product_id"] == MARGIN_PROBLEM_PRODUCT].copy()
    p6["margin_pct"] = ((p6["list_price"] - p6["unit_cost"]) / p6["list_price"] * 100).round(1)
    print(p6[["effective_date", "unit_cost", "list_price", "margin_pct"]].to_string(index=False))