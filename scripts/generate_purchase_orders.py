"""
Generates fact_purchase_orders.csv for the Daxwell-inspired operations
intelligence project.

Grain: one row per PO line (one product, one supplier, one order date).

Depends on: dim_products.csv, dim_suppliers.csv

Deliberately links the two Watch-tier suppliers to the two stockout-risk
products from fact_inventory_snapshot.py, so the story is coherent
end-to-end: those products run low BECAUSE their suppliers have been
arriving later and later.
"""

import pandas as pd
import numpy as np

np.random.seed(42)

dim_products = pd.read_csv("data/raw/dim_products.csv")
dim_suppliers = pd.read_csv("data/raw/dim_suppliers.csv")

product_ids = dim_products["product_id"].tolist()
watch_suppliers = dim_suppliers.loc[
    dim_suppliers["reliability_tier"] == "Watch", "supplier_id"
].tolist()
reliable_suppliers = dim_suppliers.loc[
    dim_suppliers["reliability_tier"] == "Reliable", "supplier_id"
].tolist()

# Must match STOCKOUT_RISK_PRODUCTS in generate_inventory.py
STOCKOUT_RISK_PRODUCTS = ["P0002", "P0004"]

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2025-12-31")
DEGRADATION_START = pd.Timestamp("2025-01-01")  # Watch suppliers start slipping here

# ---------------------------------------------------------------------------
# Assign each product a primary supplier. The two stockout-risk products
# are deliberately pinned to the two Watch suppliers; everything else goes
# to a random Reliable supplier.
# ---------------------------------------------------------------------------
product_supplier_map = {}
for pid, supplier_id in zip(STOCKOUT_RISK_PRODUCTS, watch_suppliers):
    product_supplier_map[pid] = supplier_id

for pid in product_ids:
    if pid not in product_supplier_map:
        product_supplier_map[pid] = np.random.choice(reliable_suppliers)


def delivery_variance_days(supplier_id: str, order_date: pd.Timestamp) -> int:
    """How many days late (positive) or early (negative) a delivery lands."""
    tier = dim_suppliers.loc[
        dim_suppliers["supplier_id"] == supplier_id, "reliability_tier"
    ].values[0]

    if tier == "Reliable" or order_date < DEGRADATION_START:
        return int(np.random.randint(-2, 4))

    # Watch supplier, on or after the degradation start date: delay grows
    # roughly linearly through 2025, capped at 35 days by year-end.
    days_into_degradation = (order_date - DEGRADATION_START).days
    max_delay = min(35, (days_into_degradation / 365) * 35)
    return int(np.random.uniform(max_delay * 0.6, max_delay)) + int(np.random.randint(-1, 3))


def build_fact_purchase_orders() -> pd.DataFrame:
    rows = []
    po_id = 1

    for pid in product_ids:
        supplier_id = product_supplier_map[pid]
        baseline_lead = dim_suppliers.loc[
            dim_suppliers["supplier_id"] == supplier_id, "baseline_lead_time_days"
        ].values[0]

        order_date = START_DATE
        while order_date <= END_DATE:
            expected_delivery = order_date + pd.Timedelta(days=int(baseline_lead))
            variance = delivery_variance_days(supplier_id, order_date)
            actual_delivery = expected_delivery + pd.Timedelta(days=variance)
            status = "Delivered" if actual_delivery <= END_DATE else "In Transit"

            rows.append({
                "po_id": f"PO{po_id:05d}",
                "order_date": order_date.strftime("%Y-%m-%d"),
                "product_id": pid,
                "supplier_id": supplier_id,
                "quantity_ordered": int(np.random.randint(300, 900)),
                "expected_delivery_date": expected_delivery.strftime("%Y-%m-%d"),
                "actual_delivery_date": actual_delivery.strftime("%Y-%m-%d") if status == "Delivered" else None,
                "status": status,
            })
            po_id += 1
            # Next PO for this product, roughly monthly with some jitter
            order_date += pd.Timedelta(days=int(np.random.randint(30, 41)))

    return pd.DataFrame(rows)


if __name__ == "__main__":
    fact_po = build_fact_purchase_orders()
    fact_po.to_csv("data/raw/fact_purchase_orders.csv", index=False)

    print(f"fact_purchase_orders.csv -> {len(fact_po):,} rows")

    print("\n--- Product -> Supplier assignments for stockout-risk products ---")
    for pid in STOCKOUT_RISK_PRODUCTS:
        sid = product_supplier_map[pid]
        tier = dim_suppliers.loc[dim_suppliers["supplier_id"] == sid, "reliability_tier"].values[0]
        print(f"{pid} -> {sid} (tier={tier})")

    print("\n--- Delay trend check: expected vs. actual delivery gap over time (Watch suppliers) ---")
    delivered = fact_po[fact_po["status"] == "Delivered"].copy()
    delivered["expected_delivery_date"] = pd.to_datetime(delivered["expected_delivery_date"])
    delivered["actual_delivery_date"] = pd.to_datetime(delivered["actual_delivery_date"])
    delivered["delay_days"] = (delivered["actual_delivery_date"] - delivered["expected_delivery_date"]).dt.days

    watch_pos = delivered[delivered["supplier_id"].isin(watch_suppliers)].copy()
    watch_pos["order_date"] = pd.to_datetime(watch_pos["order_date"])
    quarterly_delay = watch_pos.groupby(watch_pos["order_date"].dt.to_period("Q"))["delay_days"].mean()
    print(quarterly_delay)

    print("\nSample rows:")
    print(fact_po.head(5).to_string(index=False))