"""
Generates dim_customers.csv for the Daxwell-inspired operations
intelligence project.

Grain: one row per customer.
"""

import pandas as pd
import numpy as np
from faker import Faker

np.random.seed(42)
fake = Faker()
Faker.seed(42)  # Faker has its own internal random state, seeded separately

# Segments mirror Daxwell's real customer base: healthcare facilities,
# food-service operators, and distributors who resell to smaller accounts.
SEGMENTS = ["Healthcare", "Food Service", "Distributor"]
SEGMENT_WEIGHTS = [0.35, 0.45, 0.20]  # food service is the largest customer base

REGIONS = {
    "Northeast": ["NY", "MA", "PA", "NJ"],
    "South": ["TX", "FL", "GA", "NC"],
    "Midwest": ["IL", "OH", "MI", "WI"],
    "West": ["CA", "WA", "AZ", "CO"],
}

HEALTHCARE_SUFFIXES = ["Medical Center", "Regional Hospital", "Clinic", "Health System"]
FOODSERVICE_SUFFIXES = ["Bistro Group", "Catering Co.", "Restaurant Group", "Diner"]
DISTRIBUTOR_SUFFIXES = ["Supply Co.", "Distribution", "Wholesale Partners", "Trading Co."]

def build_customer_name(segment: str) -> str:
    base = fake.last_name()
    if segment == "Healthcare":
        suffix = np.random.choice(HEALTHCARE_SUFFIXES)
    elif segment == "Food Service":
        suffix = np.random.choice(FOODSERVICE_SUFFIXES)
    else:
        suffix = np.random.choice(DISTRIBUTOR_SUFFIXES)
    return f"{base} {suffix}"

def build_dim_customers(n_customers: int = 45) -> pd.DataFrame:
    rows = []
    for i in range(1, n_customers + 1):
        segment = np.random.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
        region = np.random.choice(list(REGIONS.keys()))
        state = np.random.choice(REGIONS[region])

        rows.append({
            "customer_id": f"C{i:04d}",
            "customer_name": build_customer_name(segment),
            "segment": segment,
            "region": region,
            "state": state,
            "is_active": True,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    dim_customers = build_dim_customers()
    dim_customers.to_csv("data/raw/dim_customers.csv", index=False)

    print(f"dim_customers.csv -> {len(dim_customers):,} rows")
    print("\nSegment breakdown:")
    print(dim_customers["segment"].value_counts())
    print("\nSample:")
    print(dim_customers.head(6).to_string(index=False))