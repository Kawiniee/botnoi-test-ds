"""
Feature Engineering Pipeline
============================

Purpose:
    Create model-ready features for store-product-day demand forecasting.

Input:
    data/processed/retail_dataset.csv

Output:
    data/processed/retail_features.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from data_preprocessing import OUTPUT_PATH as PROCESSED_DATA_PATH
from data_preprocessing import prepare_retail_dataset, save_processed_data


FEATURE_OUTPUT_PATH = Path("data/processed/retail_features.csv")
GROUP_COLUMNS = ["store_id", "product_id"]
TARGET_COLUMN = "qty"

LAG_WINDOWS = [1, 7, 14, 30]
ROLLING_WINDOWS = [7, 14, 30]

SYNTHETIC_GENERATION_COLUMNS = [
    "base_demand",
    "demand_multiplier",
    "demand_boost",
]


def load_processed_data(input_path: Path = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Load processed data, creating it first if it does not exist."""
    if not input_path.exists():
        dataset = prepare_retail_dataset()
        save_processed_data(dataset, input_path)

    return pd.read_csv(input_path, encoding="utf-8")


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar features available at prediction time."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["is_weekend"] = df["day_of_week"] >= 5

    return df


def add_promotion_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add promotion features based on the known promotion calendar."""
    df = df.copy()
    df["promo_start_date"] = pd.to_datetime(df["promo_start_date"])
    df["promo_end_date"] = pd.to_datetime(df["promo_end_date"])

    df["has_promo"] = df["promotion_id"] != "PROMO00"
    df["promo_days_since_start"] = (df["date"] - df["promo_start_date"]).dt.days
    df["promo_days_until_end"] = (df["promo_end_date"] - df["date"]).dt.days
    df["is_promo_start_day"] = df["has_promo"] & (df["promo_days_since_start"] == 0)
    df["is_promo_end_day"] = df["has_promo"] & (df["promo_days_until_end"] == 0)

    no_promo_mask = ~df["has_promo"]
    df.loc[no_promo_mask, ["promo_days_since_start", "promo_days_until_end"]] = 0

    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag features within each store-product time series."""
    df = df.copy()
    df = df.sort_values(GROUP_COLUMNS + ["date"]).reset_index(drop=True)
    grouped_qty = df.groupby(GROUP_COLUMNS, sort=False)[TARGET_COLUMN]

    for window in LAG_WINDOWS:
        df[f"lag_{window}"] = grouped_qty.shift(window)

    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rolling statistics using only historical demand."""
    df = df.copy()
    grouped_qty = df.groupby(GROUP_COLUMNS, sort=False)[TARGET_COLUMN]
    shifted_qty = grouped_qty.shift(1)

    for window in ROLLING_WINDOWS:
        rolling = shifted_qty.groupby([df["store_id"], df["product_id"]], sort=False).rolling(
            window=window,
            min_periods=window,
        )
        df[f"rolling_mean_{window}"] = rolling.mean().reset_index(level=[0, 1], drop=True)

    rolling_7 = shifted_qty.groupby([df["store_id"], df["product_id"]], sort=False).rolling(
        window=7,
        min_periods=7,
    )
    df["rolling_std_7"] = rolling_7.std().reset_index(level=[0, 1], drop=True)
    df["rolling_median_7"] = rolling_7.median().reset_index(level=[0, 1], drop=True)

    return df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add simple categorical interaction features for tree-based models."""
    df = df.copy()
    df["category_month"] = df["category"].astype(str) + "_" + df["month"].astype(str)
    df["store_type_category"] = df["store_type"].astype(str) + "_" + df["category"].astype(str)
    df["promo_category"] = np.where(
        df["has_promo"],
        "promo_" + df["category"].astype(str),
        "no_promo_" + df["category"].astype(str),
    )

    return df


def validate_features(df: pd.DataFrame) -> None:
    """Validate that engineered features are model-ready."""
    duplicate_count = df.duplicated(["date", "store_id", "product_id"]).sum()
    if duplicate_count:
        raise ValueError(f"feature dataset has {duplicate_count} duplicate grain rows")

    required_columns = [
        "year",
        "month",
        "quarter",
        "week_of_year",
        "day_of_week",
        "is_weekend",
        "has_promo",
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_7",
        "rolling_median_7",
    ]
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"feature dataset missing columns: {sorted(missing_columns)}")

    if df[required_columns].isna().any().any():
        missing = df[required_columns].isna().sum()
        missing = missing[missing > 0].to_dict()
        raise ValueError(f"feature dataset contains missing values: {missing}")


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Run all feature engineering steps."""
    features = add_time_features(df)
    features = add_promotion_features(features)
    features = add_lag_features(features)
    features = add_rolling_features(features)
    features = add_interaction_features(features)

    historical_feature_columns = [
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_7",
        "rolling_median_7",
    ]
    features = features.dropna(subset=historical_feature_columns).reset_index(drop=True)
    validate_features(features)

    return features


def save_features(df: pd.DataFrame, output_path: Path = FEATURE_OUTPUT_PATH) -> None:
    """Save engineered features as CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("Starting Feature Engineering")
    print("=" * 70)

    dataset = load_processed_data()
    features = create_features(dataset)
    save_features(features)

    print(f"Input rows: {len(dataset):,}")
    print(f"Feature rows: {len(features):,}")
    print(f"Columns: {len(features.columns)}")
    print(f"Saved: {FEATURE_OUTPUT_PATH}")
    print()
    print("Synthetic generation columns kept for audit, not recommended for MVP modeling:")
    for column in SYNTHETIC_GENERATION_COLUMNS:
        print(f"  - {column}")

    print("=" * 70)
    print("Feature Engineering Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
