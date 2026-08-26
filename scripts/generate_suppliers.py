"""
Generates dim_suppliers.csv for the Daxwell-inspired operations
intelligence project.

Grain: one row per supplier.
"""

import pandas as pd
import numpy as np
from faker import Faker

np.random.seed(42)
fake = Faker()
Faker.seed(42)

# Mirrors Daxwell's real sourcing footprint: import-heavy from Asia,
# with a couple of domestic suppliers for faster-turnaround items.
# Fixed counts (not a random draw) so the composition is guaranteed on
# every run, rather than left to chance on a small sample of 12.
COUNTRIES_FIXED = (
    ["China"] * 6 + ["Vietnam"] * 2 + ["India"] * 1 + ["United States"] * 3
)
np.random.shuffle(COUNTRIES_FIXED)  # randomize WHICH supplier gets which country

COMPANY_SUFFIXES = ["Manufacturing", "Industries", "Trading Co.", "Exports", "Group"]

def build_dim_suppliers(n_suppliers: int = 12) -> pd.DataFrame:
    rows = []
    for i in range(1, n_suppliers + 1):
        country = COUNTRIES_FIXED[i - 1]
        name = f"{fake.last_name()} {np.random.choice(COMPANY_SUFFIXES)}"

        # Baseline lead time depends on geography -- overseas shipping
        # genuinely takes longer than domestic trucking. This isn't
        # arbitrary noise, it reflects real supply-chain physics.
        if country == "United States":
            base_lead_time = np.random.randint(5, 12)
        else:
            base_lead_time = np.random.randint(20, 35)

        rows.append({
            "supplier_id": f"S{i:03d}",
            "supplier_name": name,
            "country": country,
            "baseline_lead_time_days": base_lead_time,
            "reliability_tier": None,  # filled in below, once we know the group
        })

    df = pd.DataFrame(rows)

    # Deliberately seed the "supplier delay" scenario: mark 2 suppliers as
    # Watch-tier. Their PURCHASE ORDERS (built in a later step) will show a
    # growing gap between expected and actual delivery -- this table just
    # tags WHO those problem suppliers are.
    watch_suppliers = df.sample(n=2, random_state=42).index
    df["reliability_tier"] = "Reliable"
    df.loc[watch_suppliers, "reliability_tier"] = "Watch"

    return df


if __name__ == "__main__":
    dim_suppliers = build_dim_suppliers()
    dim_suppliers.to_csv("data/raw/dim_suppliers.csv", index=False)

    print(f"dim_suppliers.csv -> {len(dim_suppliers):,} rows")
    print("\nReliability tier breakdown:")
    print(dim_suppliers["reliability_tier"].value_counts())
    print("\nFull table:")
    print(dim_suppliers.to_string(index=False))