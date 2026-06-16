"""
Model Training Pipeline
=======================

Purpose:
    Train demand forecasting models for store-product-day quantity prediction.

Input:
    data/processed/retail_features.csv

Outputs:
    output/modeling/metrics.csv
    output/modeling/predictions.csv
    output/modeling/feature_importance.csv
    output/modeling/model_comparison.png
    output/modeling/feature_importance.png
    output/modeling/actual_vs_predicted.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from feature_engineering import FEATURE_OUTPUT_PATH, create_features, load_processed_data, save_features


RANDOM_SEED = 42
TARGET_COLUMN = "qty"
TEST_DAYS = 90

OUTPUT_DIR = Path("output/modeling")
METRICS_PATH = OUTPUT_DIR / "metrics.csv"
PREDICTIONS_PATH = OUTPUT_DIR / "predictions.csv"
FEATURE_IMPORTANCE_PATH = OUTPUT_DIR / "feature_importance.csv"
MODEL_COMPARISON_PATH = OUTPUT_DIR / "model_comparison.png"
FEATURE_IMPORTANCE_CHART_PATH = OUTPUT_DIR / "feature_importance.png"
ACTUAL_VS_PREDICTED_PATH = OUTPUT_DIR / "actual_vs_predicted.png"

ID_COLUMNS = ["date", "store_id", "product_id"]

# Excluded from model input to avoid direct target leakage or synthetic-generator shortcuts.
EXCLUDED_FEATURE_COLUMNS = [
    TARGET_COLUMN,
    "date",
    "revenue",
    "expected_revenue",
    "revenue_diff",
    "product_name",
    "store_name",
    "promotion_name",
    "promo_start_date",
    "promo_end_date",
    "base_demand",
    "demand_multiplier",
    "demand_boost",
]


def load_feature_data(feature_path: Path = FEATURE_OUTPUT_PATH) -> pd.DataFrame:
    """Load engineered features, creating them first if needed."""
    if not feature_path.exists():
        dataset = load_processed_data()
        features = create_features(dataset)
        save_features(features, feature_path)

    df = pd.read_csv(feature_path, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    return df


def split_train_test(df: pd.DataFrame, test_days: int = TEST_DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use the most recent dates as the test set to respect time order."""
    cutoff_date = df["date"].max() - pd.Timedelta(days=test_days - 1)
    train_df = df[df["date"] < cutoff_date].copy()
    test_df = df[df["date"] >= cutoff_date].copy()

    if train_df.empty or test_df.empty:
        raise ValueError("train/test split produced an empty dataset")

    return train_df, test_df


def get_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Select model input columns and split them by type."""
    candidate_columns = [col for col in df.columns if col not in EXCLUDED_FEATURE_COLUMNS]
    categorical_features = [
        col
        for col in candidate_columns
        if df[col].dtype == "object" or str(df[col].dtype) == "category"
    ]
    numeric_features = [col for col in candidate_columns if col not in categorical_features]

    return numeric_features, categorical_features


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    """Build a shared preprocessing step for both models."""
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_models(preprocessor: ColumnTransformer) -> dict[str, Pipeline]:
    """Create baseline and main model pipelines."""
    return {
        "Linear Regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", LinearRegression()),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
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
        ),
    }


def evaluate_model(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    """Calculate core regression metrics."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {"MAE": mae, "RMSE": rmse}


def train_and_evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, Pipeline]:
    """Train both models and return metrics, predictions, and the main model."""
    feature_columns = numeric_features + categorical_features
    x_train = train_df[feature_columns]
    y_train = train_df[TARGET_COLUMN]
    x_test = test_df[feature_columns]
    y_test = test_df[TARGET_COLUMN]

    metrics_rows = []
    prediction_frames = []
    models = build_models(build_preprocessor(numeric_features, categorical_features))

    for model_name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        predictions = np.maximum(predictions, 0)
        metrics = evaluate_model(y_test, predictions)

        metrics_rows.append(
            {
                "model": model_name,
                "train_rows": len(train_df),
                "test_rows": len(test_df),
                "test_start_date": test_df["date"].min().date().isoformat(),
                "test_end_date": test_df["date"].max().date().isoformat(),
                **metrics,
            }
        )

        model_predictions = test_df[ID_COLUMNS + [TARGET_COLUMN]].copy()
        model_predictions["model"] = model_name
        model_predictions["prediction"] = predictions
        model_predictions["absolute_error"] = (model_predictions[TARGET_COLUMN] - predictions).abs()
        prediction_frames.append(model_predictions)

    metrics_df = pd.DataFrame(metrics_rows).sort_values("RMSE").reset_index(drop=True)
    predictions_df = pd.concat(prediction_frames, ignore_index=True)

    return metrics_df, predictions_df, models["Random Forest"]


def extract_feature_importance(model: Pipeline, top_n: int = 30) -> pd.DataFrame:
    """Extract Random Forest feature importance after preprocessing."""
    preprocessor = model.named_steps["preprocessor"]
    regressor = model.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    importances = regressor.feature_importances_

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importances,
        }
    ).sort_values("importance", ascending=False)

    return importance_df.head(top_n).reset_index(drop=True)


def plot_model_comparison(metrics_df: pd.DataFrame) -> None:
    """Create MAE/RMSE comparison chart."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(metrics_df["model"], metrics_df["MAE"], color=["#577590", "#43AA8B"])
    axes[0].set_title("MAE by Model", fontweight="bold")
    axes[0].set_ylabel("MAE")
    axes[0].tick_params(axis="x", rotation=15)

    axes[1].bar(metrics_df["model"], metrics_df["RMSE"], color=["#577590", "#43AA8B"])
    axes[1].set_title("RMSE by Model", fontweight="bold")
    axes[1].set_ylabel("RMSE")
    axes[1].tick_params(axis="x", rotation=15)

    plt.tight_layout()
    plt.savefig(MODEL_COMPARISON_PATH, dpi=150, bbox_inches="tight")
    plt.close()


def plot_feature_importance(importance_df: pd.DataFrame) -> None:
    """Create Random Forest feature importance chart."""
    plot_df = importance_df.sort_values("importance", ascending=True)

    plt.figure(figsize=(10, 8))
    plt.barh(plot_df["feature"], plot_df["importance"], color="#43AA8B")
    plt.title("Random Forest Feature Importance", fontweight="bold")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(FEATURE_IMPORTANCE_CHART_PATH, dpi=150, bbox_inches="tight")
    plt.close()


def plot_actual_vs_predicted(predictions_df: pd.DataFrame) -> None:
    """Create actual vs predicted chart for the main model."""
    rf_predictions = predictions_df[predictions_df["model"] == "Random Forest"].copy()

    sample_size = min(3000, len(rf_predictions))
    scatter_df = rf_predictions.sample(sample_size, random_state=RANDOM_SEED)

    daily_df = (
        rf_predictions.groupby("date")
        .agg(actual=(TARGET_COLUMN, "sum"), predicted=("prediction", "sum"))
        .reset_index()
        .sort_values("date")
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].scatter(scatter_df[TARGET_COLUMN], scatter_df["prediction"], alpha=0.25, color="#577590")
    max_value = max(scatter_df[TARGET_COLUMN].max(), scatter_df["prediction"].max())
    axes[0].plot([0, max_value], [0, max_value], color="#F94144", linestyle="--")
    axes[0].set_title("Actual vs Predicted (Sample)", fontweight="bold")
    axes[0].set_xlabel("Actual qty")
    axes[0].set_ylabel("Predicted qty")

    axes[1].plot(daily_df["date"], daily_df["actual"], label="Actual", color="#577590")
    axes[1].plot(daily_df["date"], daily_df["predicted"], label="Predicted", color="#43AA8B")
    axes[1].set_title("Daily Total: Actual vs Predicted", fontweight="bold")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Total qty")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(ACTUAL_VS_PREDICTED_PATH, dpi=150, bbox_inches="tight")
    plt.close()


def save_outputs(
    metrics_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
    importance_df: pd.DataFrame,
) -> None:
    """Save model outputs and charts."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metrics_df.to_csv(METRICS_PATH, index=False, encoding="utf-8")
    predictions_df.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8")
    importance_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False, encoding="utf-8")

    plot_model_comparison(metrics_df)
    plot_feature_importance(importance_df)
    plot_actual_vs_predicted(predictions_df)


def main() -> None:
    print("=" * 70)
    print("Starting Model Training")
    print("=" * 70)

    df = load_feature_data()
    train_df, test_df = split_train_test(df)
    numeric_features, categorical_features = get_feature_columns(df)

    print(f"Feature rows: {len(df):,}")
    print(f"Train rows: {len(train_df):,}")
    print(f"Test rows: {len(test_df):,}")
    print(f"Numeric features: {len(numeric_features)}")
    print(f"Categorical features: {len(categorical_features)}")
    print(f"Test period: {test_df['date'].min().date()} to {test_df['date'].max().date()}")
    print()

    metrics_df, predictions_df, random_forest_model = train_and_evaluate(
        train_df,
        test_df,
        numeric_features,
        categorical_features,
    )
    importance_df = extract_feature_importance(random_forest_model)
    save_outputs(metrics_df, predictions_df, importance_df)

    print("Metrics:")
    print(metrics_df.to_string(index=False))
    print()
    print(f"Saved metrics: {METRICS_PATH}")
    print(f"Saved predictions: {PREDICTIONS_PATH}")
    print(f"Saved feature importance: {FEATURE_IMPORTANCE_PATH}")
    print(f"Saved charts: {OUTPUT_DIR}")
    print("=" * 70)
    print("Model Training Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
