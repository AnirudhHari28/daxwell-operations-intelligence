"""
Generates fact_inventory_snapshot.csv for the Daxwell-inspired operations
intelligence project.

Grain: one row per product per day.

Depends on: dim_dates.csv, dim_products.csv, fact_sales.csv
"""

import pandas as pd
import numpy as np

np.random.seed(42)

dim_dates = pd.read_csv("data/raw/dim_dates.csv", parse_dates=["date"])
dim_products = pd.read_csv("data/raw/dim_products.csv")
fact_sales = pd.read_csv("data/raw/fact_sales.csv", parse_dates=["date"])

product_ids = dim_products["product_id"].tolist()
all_dates = dim_dates["date"].tolist()

# Daily demand per product, filling days with zero sales as 0 (not missing)
daily_demand = (
    fact_sales.groupby(["date", "product_id"])["quantity_sold"]
    .sum()
    .unstack(fill_value=0)
    .reindex(index=all_dates, columns=product_ids, fill_value=0)
)

# ---------------------------------------------------------------------------
# Scenario setup
# ---------------------------------------------------------------------------
# STOCKOUT RISK: replenishment for these two products gets delayed in the
# final stretch of the dataset -- stock quietly runs down toward zero.
STOCKOUT_RISK_PRODUCTS = ["P0002", "P0004"]  # Nitrile Gloves L, Face Masks
STOCKOUT_DELAY_START = pd.Timestamp("2025-10-15")
NORMAL_LEAD_TIME = 20
DELAYED_LEAD_TIME = 55  # replenishment takes much longer once this kicks in

# OVERSTOCK: these two products get ONE large, real-world-style over-order
# event (e.g. a demand forecast that didn't pan out, or hitting a
# supplier's minimum order quantity) -- a clear, explainable jump that
# stays visibly elevated because normal demand doesn't absorb it quickly.
OVERSTOCK_PRODUCTS = ["P0009", "P0010"]  # Take-Out Containers, Paper Straws
OVERSTOCK_INJECTION_DATE = pd.Timestamp("2025-11-15")  # close enough to year-end that
                                                         # demand hasn't absorbed it yet
OVERSTOCK_INJECTION_MULTIPLIER = 4.0  # extra stock = 4x the normal 45-day target


def build_fact_inventory() -> pd.DataFrame:
    rows = []

    for product_id in product_ids:
        avg_daily_demand = max(daily_demand[product_id].mean(), 1.0)

        reorder_point = avg_daily_demand * 20
        safety_stock = avg_daily_demand * 10
        target_stock = avg_daily_demand * 45

        on_hand = target_stock  # start fully stocked
        pending_order = None  # (arrival_date, quantity) or None

        for date in all_dates:
            # Receive a pending order if it's arrived
            if pending_order is not None and date >= pending_order[0]:
                on_hand += pending_order[1]
                pending_order = None

            # One-time over-order event for designated overstock products
            if product_id in OVERSTOCK_PRODUCTS and date == OVERSTOCK_INJECTION_DATE:
                on_hand += target_stock * OVERSTOCK_INJECTION_MULTIPLIER

            # Sell today's demand
            todays_demand = daily_demand.loc[date, product_id]
            on_hand = max(0, on_hand - todays_demand)

            # Decide whether to place a new order
            if on_hand <= reorder_point and pending_order is None:
                lead_time = NORMAL_LEAD_TIME
                if product_id in STOCKOUT_RISK_PRODUCTS and date >= STOCKOUT_DELAY_START:
                    lead_time = DELAYED_LEAD_TIME
                order_qty = max(target_stock - on_hand, avg_daily_demand * 10)
                pending_order = (date + pd.Timedelta(days=lead_time), order_qty)

            rows.append({
                "snapshot_date": date.strftime("%Y-%m-%d"),
                "product_id": product_id,
                "on_hand_qty": round(on_hand, 1),
                "reorder_point": round(reorder_point, 1),
                "safety_stock": round(safety_stock, 1),
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    fact_inventory = build_fact_inventory()
    fact_inventory.to_csv("data/raw/fact_inventory_snapshot.csv", index=False)

    print(f"fact_inventory_snapshot.csv -> {len(fact_inventory):,} rows")

    print("\n--- Stockout risk check (last 30 days, should be near/below reorder point) ---")
    for pid in STOCKOUT_RISK_PRODUCTS:
        subset = fact_inventory[fact_inventory["product_id"] == pid].tail(30)
        print(f"{pid}: min on_hand={subset['on_hand_qty'].min():.1f}, "
              f"reorder_point={subset['reorder_point'].iloc[0]:.1f}, "
              f"days below reorder point={int((subset['on_hand_qty'] <= subset['reorder_point']).sum())}/30")

    print("\n--- Overstock check: on_hand right before vs. after the injection, and at year-end ---")
    for pid in OVERSTOCK_PRODUCTS:
        subset = fact_inventory[fact_inventory["product_id"] == pid].set_index("snapshot_date")
        avg_demand = daily_demand[pid].mean()
        before = subset.loc["2025-11-14", "on_hand_qty"]
        after = subset.loc["2025-11-16", "on_hand_qty"]
        year_end = subset.loc["2025-12-31", "on_hand_qty"]
        print(f"{pid}: before={before:.0f}, right after injection={after:.0f}, "
              f"year-end={year_end:.0f} (normal 45-day target={avg_demand*45:.0f})")

    print("\nSample rows:")
    print(fact_inventory.head(5).to_string(index=False))