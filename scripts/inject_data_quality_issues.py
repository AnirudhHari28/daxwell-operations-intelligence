"""
Deliberately injects realistic data-quality problems into fact_sales.csv.

This runs AFTER generate_sales.py, on purpose -- it simulates the mess
that shows up in real-world captured data (bad manual entry, integration
bugs, system glitches), separate from the clean business logic that
generated the data in the first place.

Every injected issue is logged with its exact sale_id, so Phase 4's
quality checks can be verified against a known, exact answer key.
"""

import pandas as pd
import numpy as np

np.random.seed(99)  # different seed on purpose -- this is a distinct process

fact_sales = pd.read_csv("data/raw/fact_sales.csv")
issue_log = []

# ---------------------------------------------------------------------------
# 1. Duplicate rows -- same sale_id appears twice (a real system replay /
#    double-submit bug)
# ---------------------------------------------------------------------------
dupe_rows = fact_sales.sample(n=6, random_state=1)
fact_sales = pd.concat([fact_sales, dupe_rows], ignore_index=True)
issue_log += [(sid, "duplicate_row") for sid in dupe_rows["sale_id"]]

# ---------------------------------------------------------------------------
# 2. Missing customer_id -- null foreign key (e.g. a POS system that let an
#    order through without a customer selected)
# ---------------------------------------------------------------------------
null_customer_idx = fact_sales.sample(n=10, random_state=2).index
fact_sales.loc[null_customer_idx, "customer_id"] = np.nan
issue_log += [(fact_sales.loc[i, "sale_id"], "null_customer_id") for i in null_customer_idx]

# ---------------------------------------------------------------------------
# 3. Invalid product_id -- references a product that doesn't exist in
#    dim_products (referential integrity violation; e.g. a discontinued
#    or mistyped SKU)
# ---------------------------------------------------------------------------
bad_product_idx = fact_sales.sample(n=7, random_state=3).index
fact_sales.loc[bad_product_idx, "product_id"] = "P9999"
issue_log += [(fact_sales.loc[i, "sale_id"], "invalid_product_id") for i in bad_product_idx]

# ---------------------------------------------------------------------------
# 4. Negative quantity_sold -- shouldn't be physically possible, but data
#    entry errors and unhandled returns/refunds cause this constantly in
#    real systems
# ---------------------------------------------------------------------------
neg_qty_idx = fact_sales.sample(n=6, random_state=4).index
fact_sales.loc[neg_qty_idx, "quantity_sold"] = -fact_sales.loc[neg_qty_idx, "quantity_sold"].abs()
issue_log += [(fact_sales.loc[i, "sale_id"], "negative_quantity") for i in neg_qty_idx]

# ---------------------------------------------------------------------------
# 5. Invalid unit_price -- zero or negative, e.g. a pricing system glitch
# ---------------------------------------------------------------------------
bad_price_idx = fact_sales.sample(n=6, random_state=5).index
fact_sales.loc[bad_price_idx, "unit_price"] = 0.0
issue_log += [(fact_sales.loc[i, "sale_id"], "invalid_price") for i in bad_price_idx]

# ---------------------------------------------------------------------------
# 6. Missing date -- null in a column that should never be null
# ---------------------------------------------------------------------------
null_date_idx = fact_sales.sample(n=5, random_state=6).index
fact_sales.loc[null_date_idx, "date"] = np.nan
issue_log += [(fact_sales.loc[i, "sale_id"], "null_date") for i in null_date_idx]

# ---------------------------------------------------------------------------
# Save the now-imperfect fact_sales, and a log of exactly what we broke
# ---------------------------------------------------------------------------
fact_sales.to_csv("data/raw/fact_sales.csv", index=False)

issue_log_df = pd.DataFrame(issue_log, columns=["sale_id", "issue_type"])
issue_log_df.to_csv("data/raw/_injected_issues_log.csv", index=False)

print(f"fact_sales.csv now has {len(fact_sales):,} rows (was {len(fact_sales) - len(dupe_rows):,} before duplicates)")
print(f"\nIssues injected, by type:")
print(issue_log_df["issue_type"].value_counts())
print(f"\nTotal distinct affected rows logged: {len(issue_log_df)}")
print("\nLog saved to data/raw/_injected_issues_log.csv for later verification in Phase 4.")