"""
Daxwell ETL pipeline: Extract -> Transform -> Load.

This replaces the Phase 1/2 workflow of manually running several scripts
in the right order. Running this ONE script does the whole job,
automatically, in order, with a permanent log record of what happened.

Run with: python scripts/run_pipeline.py
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

# ---------------------------------------------------------------------------
# Logging setup -- writes to BOTH the terminal (so you see it live) and a
# file on disk (so the record survives after the terminal closes -- the
# whole point of using logging instead of print()).
# ---------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("daxwell_pipeline")

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/daxwell.duckdb")

TABLES = {
    "dim_dates": RAW_DIR / "dim_dates.csv",
    "dim_products": RAW_DIR / "dim_products.csv",
    "dim_customers": RAW_DIR / "dim_customers.csv",
    "dim_suppliers": RAW_DIR / "dim_suppliers.csv",
    "fact_sales": RAW_DIR / "fact_sales.csv",
    "fact_inventory_snapshot": RAW_DIR / "fact_inventory_snapshot.csv",
    "fact_purchase_orders": RAW_DIR / "fact_purchase_orders.csv",
    "fact_pricing_history": RAW_DIR / "fact_pricing_history.csv",
}

# Which column(s) in each table should be treated as real dates, not text.
DATE_COLUMNS = {
    "dim_dates": ["date"],
    "fact_sales": ["date"],
    "fact_inventory_snapshot": ["snapshot_date"],
    "fact_purchase_orders": ["order_date", "expected_delivery_date", "actual_delivery_date"],
    "fact_pricing_history": ["effective_date"],
}


def extract() -> dict[str, pd.DataFrame]:
    """Stage 1: EXTRACT -- read every raw CSV into memory.

    Fails loudly and immediately if a file is missing, rather than letting
    a confusing error happen three steps later in Transform or Load.
    """
    logger.info("EXTRACT: starting")
    tables = {}

    for name, path in TABLES.items():
        if not path.exists():
            raise FileNotFoundError(f"Expected raw file missing: {path}")

        df = pd.read_csv(path)
        if len(df) == 0:
            logger.warning(f"EXTRACT: {name} loaded with 0 rows -- check the source file")

        tables[name] = df
        logger.info(f"EXTRACT: {name:28s} {len(df):>8,} rows  <- {path}")

    logger.info("EXTRACT: complete")
    return tables


def transform(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Stage 2: TRANSFORM -- light, safe reshaping only.

    This is deliberately NOT a data-quality cleanup step -- finding and
    fixing bad rows (nulls, duplicates, invalid IDs) is Phase 4's dedicated
    job. Here we just do what a real staging layer does: fix column types,
    and stamp each row with when it was loaded (a lineage/audit column --
    genuinely common in production pipelines, useful for debugging
    "which run produced this row?" later).
    """
    logger.info("TRANSFORM: starting")
    loaded_at = datetime.now(timezone.utc).isoformat()

    for name, df in tables.items():
        for col in DATE_COLUMNS.get(name, []):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df["_loaded_at"] = loaded_at
        logger.info(f"TRANSFORM: {name:28s} date columns normalized, lineage stamped")

    logger.info("TRANSFORM: complete")
    return tables


def load(tables: dict[str, pd.DataFrame]) -> None:
    """Stage 3: LOAD -- write every transformed table into DuckDB."""
    logger.info("LOAD: starting")
    con = duckdb.connect(str(DB_PATH))

    for name, df in tables.items():
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df")
        count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        logger.info(f"LOAD: {name:28s} {count:>8,} rows  -> {DB_PATH}")

    con.close()
    logger.info("LOAD: complete")


def run_pipeline() -> None:
    logger.info("=" * 70)
    logger.info("Daxwell ETL pipeline starting")

    try:
        tables = extract()
        tables = transform(tables)
        load(tables)
    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}")
        sys.exit(1)

    logger.info("Daxwell ETL pipeline finished successfully")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_pipeline()