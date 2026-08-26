"""
Generates fact_sales.csv for the Daxwell-inspired operations
intelligence project.

Grain: one row per order line (one product, one customer, one date).

Depends on: dim_dates.csv, dim_products.csv, dim_customers.csv
  -- must be generated first, since this table references their IDs
  as foreign keys.
"""

import pandas as pd
import numpy as np

np.random.seed(42)

dim_dates = pd.read_csv("data/raw/dim_dates.csv", parse_dates=["date"])
dim_products = pd.read_csv("data/raw/dim_products.csv")
dim_customers = pd.read_csv("data/raw/dim_customers.csv")

product_ids = dim_products["product_id"].tolist()
customer_ids = dim_customers["customer_id"].tolist()

# ---------------------------------------------------------------------------
# Scenario setup -- decided BEFORE generating rows, so every row generated
# already "knows" whether it falls inside a seeded scenario window.
# ---------------------------------------------------------------------------

# Scenario 1: DEMAND SPIKE
# PPE products see a sharp, temporary volume spike -- e.g. a seasonal
# illness wave driving mask/glove demand well above normal.
SPIKE_PRODUCT_IDS = dim_products.loc[
    dim_products["category"] == "PPE", "product_id"
].tolist()
SPIKE_START = pd.Timestamp("2025-01-15")
SPIKE_END = pd.Timestamp("2025-02-15")
SPIKE_MULTIPLIER = 4.0

# Scenario 2: PRICING / MARGIN PROBLEM
# One product's discounting creeps steadily upward over the final six
# months of the dataset, while its cost stays flat -- silently
# compressing margin. This is deliberately NOT a spike; it should look
# like a slow leak, since that's more realistic and harder to spot.
MARGIN_PROBLEM_PRODUCT = "P0006"  # Compostable Plates 9in
MARGIN_CREEP_START = pd.Timestamp("2025-07-01")


def daily_transaction_count(date: pd.Timestamp) -> int:
    """How many order lines happen on a given day."""
    base = 25
    # Weekends are quieter -- food service/healthcare ordering patterns
    # skew toward weekday business hours.
    if date.dayofweek >= 5:
        base = int(base * 0.4)
    return np.random.poisson(base)


def pick_product_for_day(date: pd.Timestamp) -> str:
    """Choose a product, boosting spike products during the spike window."""
    if SPIKE_START <= date <= SPIKE_END and np.random.random() < 0.5:
        return np.random.choice(SPIKE_PRODUCT_IDS)
    return np.random.choice(product_ids)


def discount_for_row(product_id: str, date: pd.Timestamp) -> float:
    """Normal discounting is small and random. The margin-problem product
    gets an upward-creeping discount after the creep start date."""
    if product_id == MARGIN_PROBLEM_PRODUCT and date >= MARGIN_CREEP_START:
        days_into_creep = (date - MARGIN_CREEP_START).days
        creep = min(0.30, 0.05 + (days_into_creep / 180) * 0.25)
        return round(creep + np.random.uniform(-0.02, 0.02), 3)
    return round(np.random.uniform(0.0, 0.10), 3)


def build_fact_sales() -> pd.DataFrame:
    rows = []
    sale_id = 1

    for date in dim_dates["date"]:
        n_transactions = daily_transaction_count(date)

        for _ in range(n_transactions):
            product_id = pick_product_for_day(date)
            customer_id = np.random.choice(customer_ids)

            list_price = dim_products.loc[
                dim_products["product_id"] == product_id, "list_price"
            ].values[0]

            quantity = np.random.randint(5, 50)
            discount_pct = discount_for_row(product_id, date)
            unit_price = round(list_price * (1 - discount_pct), 2)
            revenue = round(unit_price * quantity, 2)

            rows.append({
                "sale_id": f"SO{sale_id:06d}",
                "date": date.strftime("%Y-%m-%d"),
                "product_id": product_id,
                "customer_id": customer_id,
                "quantity_sold": quantity,
                "unit_price": unit_price,
                "discount_pct": discount_pct,
                "revenue": revenue,
            })
            sale_id += 1

    return pd.DataFrame(rows)


if __name__ == "__main__":
    fact_sales = build_fact_sales()
    fact_sales.to_csv("data/raw/fact_sales.csv", index=False)

    print(f"fact_sales.csv -> {len(fact_sales):,} rows")
    print(f"\nDate range: {fact_sales['date'].min()} to {fact_sales['date'].max()}")
    print(f"Total revenue: ${fact_sales['revenue'].sum():,.2f}")

    print("\n--- Spike check: PPE volume during spike window vs. a normal window ---")
    spike_window = fact_sales[
        (fact_sales["date"] >= "2025-01-15") & (fact_sales["date"] <= "2025-02-15")
        & (fact_sales["product_id"].isin(SPIKE_PRODUCT_IDS))
    ]
    normal_window = fact_sales[
        (fact_sales["date"] >= "2024-11-01") & (fact_sales["date"] <= "2024-12-01")
        & (fact_sales["product_id"].isin(SPIKE_PRODUCT_IDS))
    ]
    print(f"PPE order lines during spike window (1 month): {len(spike_window)}")
    print(f"PPE order lines during normal window (1 month): {len(normal_window)}")

    print("\n--- Margin creep check: P0006 discount over time ---")
    p6 = fact_sales[fact_sales["product_id"] == MARGIN_PROBLEM_PRODUCT].copy()
    p6["date"] = pd.to_datetime(p6["date"])
    monthly_avg_discount = p6.groupby(p6["date"].dt.to_period("M"))["discount_pct"].mean()
    print(monthly_avg_discount.tail(8))

    print("\nSample rows:")
    print(fact_sales.head(5).to_string(index=False))