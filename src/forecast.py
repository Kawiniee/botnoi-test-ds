"""
Forecasting Pipeline
====================

Purpose:
    Forecast next 7 days of store-product-day demand using the main model.

Inputs:
    data/processed/retail_dataset.csv
    data/processed/retail_features.csv

Outputs:
    output/forecast/demand_forecast.csv
    output/forecast/forecast_summary.csv
    output/forecast/inventory_recommendation.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from data_preprocessing import OUTPUT_PATH as PROCESSED_DATA_PATH
from feature_engineering import FEATURE_OUTPUT_PATH, create_features, load_processed_data, save_features
from train_model import RANDOM_SEED, build_preprocessor, get_feature_columns, load_feature_data
from generate_inventory_mock import OUTPUT_PATH as INVENTORY_PATH
from generate_inventory_mock import generate_current_inventory, save_inventory


FORECAST_HORIZON_DAYS = 7
SAFETY_STOCK_RATE = 0.15

OUTPUT_DIR = Path("output/forecast")
FORECAST_PATH = OUTPUT_DIR / "demand_forecast.csv"
SUMMARY_PATH = OUTPUT_DIR / "forecast_summary.csv"
INVENTORY_RECOMMENDATION_PATH = OUTPUT_DIR / "inventory_recommendation.csv"

NO_PROMO_ID = "PROMO00"
NO_PROMO_NAME = "No Promotion"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load processed dataset and feature dataset, creating features if needed."""
    processed_df = load_processed_data(PROCESSED_DATA_PATH)
    processed_df["date"] = pd.to_datetime(processed_df["date"])

    if not FEATURE_OUTPUT_PATH.exists():
        features_df = create_features(processed_df)
        save_features(features_df, FEATURE_OUTPUT_PATH)

    features_df = load_feature_data(FEATURE_OUTPUT_PATH)

    return processed_df, features_df


def load_current_inventory(processed_df: pd.DataFrame, inventory_path: Path = INVENTORY_PATH) -> pd.DataFrame:
    """Load current inventory, creating mock data if it does not exist."""
    if not inventory_path.exists():
        inventory_df = generate_current_inventory(processed_df)
        save_inventory(inventory_df, inventory_path)

    inventory_df = pd.read_csv(inventory_path, encoding="utf-8")
    duplicate_count = inventory_df.duplicated(["store_id", "product_id"]).sum()
    if duplicate_count:
        raise ValueError(f"current inventory has {duplicate_count} duplicate store-product rows")

    return inventory_df


def train_forecast_model(features_df: pd.DataFrame) -> tuple[Pipeline, list[str]]:
    """Train the Random Forest model on all available feature rows."""
    numeric_features, categorical_features = get_feature_columns(features_df)
    feature_columns = numeric_features + categorical_features

    model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(numeric_features, categorical_features)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    min_samples_leaf=2,
                    random_state=RANDOM_SEED,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(features_df[feature_columns], features_df["qty"])

    return model, feature_columns


def get_static_store_product_rows(processed_df: pd.DataFrame) -> pd.DataFrame:
    """Get one latest static row per store-product pair."""
    sort_columns = ["store_id", "product_id", "date"]
    static_columns = [
        "store_id",
        "store_name",
        "store_type",
        "demand_multiplier",
        "product_id",
        "product_name",
        "category",
        "unit_price",
        "base_demand",
    ]

    return (
        processed_df.sort_values(sort_columns)
        .groupby(["store_id", "product_id"], as_index=False)
        .tail(1)[static_columns]
        .sort_values(["store_id", "product_id"])
        .reset_index(drop=True)
    )


def initialize_history(processed_df: pd.DataFrame) -> dict[tuple[str, str], list[float]]:
    """Create quantity history for recursive forecasting."""
    history = {}
    for key, group in processed_df.sort_values("date").groupby(["store_id", "product_id"]):
        history[key] = group["qty"].astype(float).tolist()

    return history


def create_future_base_rows(processed_df: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    """Create future rows with known calendar, product, store, and no-promo assumptions."""
    static_rows = get_static_store_product_rows(processed_df)
    last_date = processed_df["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon_days, freq="D")

    rows = []
    for forecast_date in future_dates:
        for _, static_row in static_rows.iterrows():
            row = static_row.to_dict()
            row.update(
                {
                    "date": forecast_date,
                    "promotion_id": NO_PROMO_ID,
                    "promotion_name": NO_PROMO_NAME,
                    "discount_percent": 0.0,
                    "demand_boost": 0.0,
                    "promo_start_date": forecast_date,
                    "promo_end_date": forecast_date,
                    "has_promo": False,
                    "net_unit_price": row["unit_price"],
                    "qty": np.nan,
                    "revenue": np.nan,
                    "expected_revenue": np.nan,
                    "revenue_diff": np.nan,
                }
            )
            rows.append(row)

    return pd.DataFrame(rows)


def add_future_known_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add future features that are known before prediction time."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["promo_start_date"] = pd.to_datetime(df["promo_start_date"])
    df["promo_end_date"] = pd.to_datetime(df["promo_end_date"])

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["is_weekend"] = df["day_of_week"] >= 5

    df["promo_days_since_start"] = 0
    df["promo_days_until_end"] = 0
    df["is_promo_start_day"] = False
    df["is_promo_end_day"] = False

    df["category_month"] = df["category"].astype(str) + "_" + df["month"].astype(str)
    df["store_type_category"] = df["store_type"].astype(str) + "_" + df["category"].astype(str)
    df["promo_category"] = "no_promo_" + df["category"].astype(str)

    return df


def add_history_features(row: pd.Series, history: dict[tuple[str, str], list[float]]) -> pd.Series:
    """Add lag and rolling features from actual plus predicted history."""
    key = (row["store_id"], row["product_id"])
    qty_history = np.array(history[key], dtype=float)

    row["lag_1"] = qty_history[-1]
    row["lag_7"] = qty_history[-7]
    row["lag_14"] = qty_history[-14]
    row["lag_30"] = qty_history[-30]
    row["rolling_mean_7"] = qty_history[-7:].mean()
    row["rolling_mean_14"] = qty_history[-14:].mean()
    row["rolling_mean_30"] = qty_history[-30:].mean()
    row["rolling_std_7"] = qty_history[-7:].std(ddof=1)
    row["rolling_median_7"] = np.median(qty_history[-7:])

    return row


def forecast_next_days(
    processed_df: pd.DataFrame,
    model: Pipeline,
    feature_columns: list[str],
    horizon_days: int = FORECAST_HORIZON_DAYS,
) -> pd.DataFrame:
    """Forecast future demand recursively for the requested horizon."""
    future_rows = add_future_known_features(create_future_base_rows(processed_df, horizon_days))
    history = initialize_history(processed_df)
    forecast_frames = []

    for forecast_date in sorted(future_rows["date"].unique()):
        day_rows = future_rows[future_rows["date"] == forecast_date].copy()
        day_rows = day_rows.apply(lambda row: add_history_features(row, history), axis=1)

        predictions = np.maximum(model.predict(day_rows[feature_columns]), 0)
        day_rows["forecast_qty"] = np.round(predictions, 2)
        day_rows["forecast_revenue"] = np.round(day_rows["forecast_qty"] * day_rows["net_unit_price"], 2)

        for _, row in day_rows.iterrows():
            key = (row["store_id"], row["product_id"])
            history[key].append(float(row["forecast_qty"]))

        forecast_frames.append(day_rows)

    forecast_df = pd.concat(forecast_frames, ignore_index=True)
    return forecast_df


def create_forecast_outputs(
    forecast_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create detailed forecast, summary, and mock inventory recommendation outputs."""
    detail_columns = [
        "date",
        "store_id",
        "store_name",
        "store_type",
        "product_id",
        "product_name",
        "category",
        "promotion_id",
        "has_promo",
        "unit_price",
        "forecast_qty",
        "forecast_revenue",
    ]
    detail_df = forecast_df[detail_columns].copy()

    summary_df = (
        detail_df.groupby(["date", "store_type", "category"], as_index=False)
        .agg(
            forecast_qty=("forecast_qty", "sum"),
            forecast_revenue=("forecast_revenue", "sum"),
            product_count=("product_id", "nunique"),
            store_count=("store_id", "nunique"),
        )
        .sort_values(["date", "store_type", "category"])
    )

    inventory_columns = [
        "inventory_date",
        "store_id",
        "product_id",
        "current_inventory_qty",
        "inventory_value",
        "recent_avg_daily_qty",
        "recent_max_daily_qty",
        "inventory_coverage_days",
    ]

    horizon_df = (
        detail_df.groupby(
            [
                "store_id",
                "store_name",
                "store_type",
                "product_id",
                "product_name",
                "category",
                "unit_price",
            ],
            as_index=False,
        )
        .agg(
            forecast_start_date=("date", "min"),
            forecast_end_date=("date", "max"),
            forecast_qty=("forecast_qty", "sum"),
            forecast_revenue=("forecast_revenue", "sum"),
        )
        .sort_values(["store_id", "product_id"])
    )
    horizon_df["forecast_days"] = (
        pd.to_datetime(horizon_df["forecast_end_date"])
        - pd.to_datetime(horizon_df["forecast_start_date"])
    ).dt.days + 1

    recommendation_df = horizon_df.merge(
        inventory_df[inventory_columns],
        on=["store_id", "product_id"],
        how="left",
    )

    if recommendation_df["current_inventory_qty"].isna().any():
        raise ValueError("inventory recommendation has missing current_inventory_qty after merge")

    recommendation_df["safety_stock_qty"] = np.ceil(
        recommendation_df["forecast_qty"] * SAFETY_STOCK_RATE
    ).astype(int)
    recommendation_df["recommended_stock_qty"] = np.ceil(
        recommendation_df["forecast_qty"] + recommendation_df["safety_stock_qty"]
    ).astype(int)
    recommendation_df["recommended_order_qty"] = np.maximum(
        recommendation_df["recommended_stock_qty"] - recommendation_df["current_inventory_qty"],
        0,
    ).astype(int)
    recommendation_df["projected_remaining_qty"] = (
        recommendation_df["current_inventory_qty"] - recommendation_df["forecast_qty"]
    ).round(2)
    recommendation_df["stock_status"] = np.select(
        [
            recommendation_df["recommended_order_qty"] > 0,
            recommendation_df["current_inventory_qty"] > recommendation_df["recommended_stock_qty"] * 1.5,
        ],
        [
            "Need Order",
            "Overstock Risk",
        ],
        default="Enough Stock",
    )

    return detail_df, summary_df, recommendation_df


def save_outputs(
    detail_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
) -> None:
    """Save forecasting outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail_df.to_csv(FORECAST_PATH, index=False, encoding="utf-8")
    summary_df.to_csv(SUMMARY_PATH, index=False, encoding="utf-8")
    recommendation_df.to_csv(INVENTORY_RECOMMENDATION_PATH, index=False, encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("Starting Demand Forecasting")
    print("=" * 70)

    processed_df, features_df = load_inputs()
    inventory_df = load_current_inventory(processed_df)
    model, feature_columns = train_forecast_model(features_df)
    forecast_df = forecast_next_days(processed_df, model, feature_columns)
    detail_df, summary_df, recommendation_df = create_forecast_outputs(forecast_df, inventory_df)
    save_outputs(detail_df, summary_df, recommendation_df)

    print(f"Forecast horizon: {FORECAST_HORIZON_DAYS} days")
    print(f"Forecast rows: {len(detail_df):,}")
    print(f"Forecast date range: {detail_df['date'].min()} to {detail_df['date'].max()}")
    print(f"Total forecast qty: {detail_df['forecast_qty'].sum():,.2f}")
    print(f"Total forecast revenue: {detail_df['forecast_revenue'].sum():,.2f} THB")
    print(f"Saved detail forecast: {FORECAST_PATH}")
    print(f"Saved forecast summary: {SUMMARY_PATH}")
    print(f"Saved inventory recommendation: {INVENTORY_RECOMMENDATION_PATH}")
    print()
    print("Assumption: future promotion calendar is unavailable, so forecast uses PROMO00.")
    print(f"Inventory source: {INVENTORY_PATH}")
    print("=" * 70)
    print("Demand Forecasting Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
