"""
Current Inventory Mock Data Generator
=====================================

Purpose:
    Create a current inventory snapshot for inventory recommendation.

Input:
    data/processed/retail_dataset.csv

Output:
    data/raw/current_inventory.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from data_preprocessing import OUTPUT_PATH as PROCESSED_DATA_PATH
from data_preprocessing import prepare_retail_dataset, save_processed_data


RANDOM_SEED = 42
LOOKBACK_DAYS = 30
OUTPUT_PATH = Path("data/raw/current_inventory.csv")


def load_processed_dataset(input_path: Path = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Load processed data, creating it first if needed."""
    if not input_path.exists():
        dataset = prepare_retail_dataset()
        save_processed_data(dataset, input_path)

    df = pd.read_csv(input_path, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    return df


def generate_current_inventory(df: pd.DataFrame, random_seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate inventory snapshot using recent demand as a business-informed baseline."""
    rng = np.random.default_rng(random_seed)
    inventory_date = df["date"].max()
    start_date = inventory_date - pd.Timedelta(days=LOOKBACK_DAYS - 1)

    recent_sales = df[df["date"] >= start_date].copy()
    recent_demand = (
        recent_sales.groupby(["store_id", "product_id"], as_index=False)
        .agg(
            recent_avg_daily_qty=("qty", "mean"),
            recent_max_daily_qty=("qty", "max"),
            unit_price=("unit_price", "last"),
            store_name=("store_name", "last"),
            product_name=("product_name", "last"),
            category=("category", "last"),
        )
        .sort_values(["store_id", "product_id"])
        .reset_index(drop=True)
    )

    coverage_days = rng.uniform(2.0, 10.0, size=len(recent_demand))
    noise = rng.uniform(0.85, 1.15, size=len(recent_demand))

    recent_demand["inventory_date"] = inventory_date.date().isoformat()
    recent_demand["current_inventory_qty"] = np.maximum(
        0,
        np.round(recent_demand["recent_avg_daily_qty"] * coverage_days * noise),
    ).astype(int)
    recent_demand["inventory_value"] = (
        recent_demand["current_inventory_qty"] * recent_demand["unit_price"]
    ).round(2)
    recent_demand["inventory_coverage_days"] = (
        recent_demand["current_inventory_qty"] / recent_demand["recent_avg_daily_qty"]
    ).round(2)

    output_columns = [
        "inventory_date",
        "store_id",
        "store_name",
        "product_id",
        "product_name",
        "category",
        "unit_price",
        "current_inventory_qty",
        "inventory_value",
        "recent_avg_daily_qty",
        "recent_max_daily_qty",
        "inventory_coverage_days",
    ]

    return recent_demand[output_columns]


def save_inventory(df: pd.DataFrame, output_path: Path = OUTPUT_PATH) -> None:
    """Save inventory snapshot."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("Starting Current Inventory Mock Generation")
    print("=" * 70)

    dataset = load_processed_dataset()
    inventory = generate_current_inventory(dataset)
    save_inventory(inventory)

    print(f"Saved: {OUTPUT_PATH}")
    print(f"Rows: {len(inventory):,}")
    print(f"Inventory date: {inventory['inventory_date'].iloc[0]}")
    print(f"Total inventory qty: {inventory['current_inventory_qty'].sum():,}")
    print(f"Total inventory value: {inventory['inventory_value'].sum():,.2f} THB")
    print("=" * 70)
    print("Current Inventory Mock Generation Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
