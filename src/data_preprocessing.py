"""
Data Preprocessing Pipeline
===========================

Purpose:
    Convert raw retail mock data into one clean store-product-day dataset.

Input:
    data/raw/product_master.csv
    data/raw/store_master.csv
    data/raw/promotion_master.csv
    data/raw/sales_transaction.csv

Output:
    data/processed/retail_dataset.csv
"""

from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_PATH = PROCESSED_DIR / "retail_dataset.csv"

PRODUCT_COLUMNS = ["product_id", "product_name", "category", "unit_price", "base_demand"]
STORE_COLUMNS = ["store_id", "store_name", "store_type", "demand_multiplier"]
PROMOTION_COLUMNS = [
    "promotion_id",
    "promotion_name",
    "discount_percent",
    "demand_boost",
    "start_date",
    "end_date",
]
SALES_COLUMNS = ["date", "store_id", "product_id", "promotion_id", "qty", "revenue"]


def load_raw_data(raw_dir: Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    """Load all raw CSV files needed for preprocessing."""
    return {
        "products": pd.read_csv(raw_dir / "product_master.csv", encoding="utf-8"),
        "stores": pd.read_csv(raw_dir / "store_master.csv", encoding="utf-8"),
        "promotions": pd.read_csv(raw_dir / "promotion_master.csv", encoding="utf-8"),
        "sales": pd.read_csv(raw_dir / "sales_transaction.csv", encoding="utf-8"),
    }


def validate_schema(tables: dict[str, pd.DataFrame]) -> None:
    """Validate required columns before any transformation."""
    expected_columns = {
        "products": PRODUCT_COLUMNS,
        "stores": STORE_COLUMNS,
        "promotions": PROMOTION_COLUMNS,
        "sales": SALES_COLUMNS,
    }

    for table_name, required_columns in expected_columns.items():
        missing_columns = set(required_columns) - set(tables[table_name].columns)
        if missing_columns:
            raise ValueError(f"{table_name} missing columns: {sorted(missing_columns)}")


def convert_dates(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Convert date-like columns to datetime."""
    tables = {name: df.copy() for name, df in tables.items()}

    tables["sales"]["date"] = pd.to_datetime(tables["sales"]["date"], errors="coerce")
    tables["promotions"]["start_date"] = pd.to_datetime(
        tables["promotions"]["start_date"], errors="coerce"
    )
    tables["promotions"]["end_date"] = pd.to_datetime(
        tables["promotions"]["end_date"], errors="coerce"
    )

    if tables["sales"]["date"].isna().any():
        raise ValueError("sales contains invalid date values")
    if tables["promotions"]["start_date"].isna().any():
        raise ValueError("promotions contains invalid start_date values")
    if tables["promotions"]["end_date"].isna().any():
        raise ValueError("promotions contains invalid end_date values")

    return tables


def validate_primary_keys(tables: dict[str, pd.DataFrame]) -> None:
    """Validate master keys and transaction grain uniqueness."""
    key_checks = {
        "products": ["product_id"],
        "stores": ["store_id"],
        "promotions": ["promotion_id"],
        "sales": ["date", "store_id", "product_id"],
    }

    for table_name, key_columns in key_checks.items():
        duplicate_count = tables[table_name].duplicated(key_columns).sum()
        if duplicate_count:
            raise ValueError(
                f"{table_name} has {duplicate_count} duplicate rows for key {key_columns}"
            )


def validate_foreign_keys(tables: dict[str, pd.DataFrame]) -> None:
    """Validate that sales rows can join to every master table."""
    sales = tables["sales"]

    fk_checks = [
        ("product_id", sales["product_id"], tables["products"]["product_id"]),
        ("store_id", sales["store_id"], tables["stores"]["store_id"]),
        ("promotion_id", sales["promotion_id"], tables["promotions"]["promotion_id"]),
    ]

    for key_name, child_values, parent_values in fk_checks:
        invalid_values = sorted(set(child_values) - set(parent_values))
        if invalid_values:
            raise ValueError(f"sales has invalid {key_name}: {invalid_values}")


def validate_business_rules(tables: dict[str, pd.DataFrame]) -> None:
    """Validate business constraints before merging."""
    products = tables["products"]
    stores = tables["stores"]
    promotions = tables["promotions"]
    sales = tables["sales"]

    if sales[SALES_COLUMNS].isna().any().any():
        raise ValueError("sales contains missing values")
    if products[PRODUCT_COLUMNS].isna().any().any():
        raise ValueError("products contains missing values")
    if stores[STORE_COLUMNS].isna().any().any():
        raise ValueError("stores contains missing values")
    if promotions[PROMOTION_COLUMNS].isna().any().any():
        raise ValueError("promotions contains missing values")

    if (sales["qty"] < 0).any():
        raise ValueError("sales contains negative qty")
    if (sales["revenue"] < 0).any():
        raise ValueError("sales contains negative revenue")
    if (products["unit_price"] <= 0).any():
        raise ValueError("products contains non-positive unit_price")
    if (products["base_demand"] < 0).any():
        raise ValueError("products contains negative base_demand")
    if (stores["demand_multiplier"] <= 0).any():
        raise ValueError("stores contains non-positive demand_multiplier")
    if ((promotions["discount_percent"] < 0) | (promotions["discount_percent"] > 100)).any():
        raise ValueError("promotions contains discount_percent outside 0-100")
    if (promotions["demand_boost"] < 0).any():
        raise ValueError("promotions contains negative demand_boost")
    if (promotions["start_date"] > promotions["end_date"]).any():
        raise ValueError("promotions contains start_date after end_date")


def merge_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge sales with product, store, and promotion dimensions."""
    promotions = tables["promotions"].rename(
        columns={"start_date": "promo_start_date", "end_date": "promo_end_date"}
    )

    dataset = tables["sales"].merge(tables["products"], on="product_id", how="left")
    dataset = dataset.merge(tables["stores"], on="store_id", how="left")
    dataset = dataset.merge(promotions, on="promotion_id", how="left")

    if len(dataset) != len(tables["sales"]):
        raise ValueError(
            f"merged dataset row count changed from {len(tables['sales'])} to {len(dataset)}"
        )

    return dataset


def add_basic_columns(dataset: pd.DataFrame) -> pd.DataFrame:
    """Add preprocessing-level derived columns used for validation and EDA."""
    dataset = dataset.copy()
    dataset["has_promo"] = dataset["promotion_id"] != "PROMO00"
    dataset["net_unit_price"] = (
        dataset["unit_price"] * (1 - dataset["discount_percent"] / 100)
    ).round(2)
    dataset["expected_revenue"] = (
        dataset["qty"] * dataset["unit_price"] * (1 - dataset["discount_percent"] / 100)
    ).round(2)
    dataset["revenue_diff"] = (dataset["revenue"] - dataset["expected_revenue"]).round(2)

    return dataset


def validate_processed_dataset(dataset: pd.DataFrame) -> None:
    """Validate the merged dataset before saving it."""
    if dataset.isna().any().any():
        missing = dataset.isna().sum()
        missing = missing[missing > 0].to_dict()
        raise ValueError(f"processed dataset contains missing values: {missing}")

    duplicate_count = dataset.duplicated(["date", "store_id", "product_id"]).sum()
    if duplicate_count:
        raise ValueError(f"processed dataset has {duplicate_count} duplicate grain rows")

    max_revenue_diff = dataset["revenue_diff"].abs().max()
    if max_revenue_diff > 0.01:
        raise ValueError(f"revenue validation failed, max diff = {max_revenue_diff}")


def prepare_retail_dataset(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Run the full preprocessing pipeline and return the processed dataset."""
    tables = load_raw_data(raw_dir)
    validate_schema(tables)
    tables = convert_dates(tables)
    validate_primary_keys(tables)
    validate_foreign_keys(tables)
    validate_business_rules(tables)

    dataset = merge_tables(tables)
    dataset = add_basic_columns(dataset)
    dataset = dataset.sort_values(["store_id", "product_id", "date"]).reset_index(drop=True)
    validate_processed_dataset(dataset)

    return dataset


def save_processed_data(dataset: pd.DataFrame, output_path: Path = OUTPUT_PATH) -> None:
    """Save the processed dataset as CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False, encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("Starting Data Preprocessing")
    print("=" * 70)

    dataset = prepare_retail_dataset()
    save_processed_data(dataset)

    print(f"Saved: {OUTPUT_PATH}")
    print(f"Rows: {len(dataset):,}")
    print(f"Columns: {len(dataset.columns)}")
    print(f"Date range: {dataset['date'].min().date()} to {dataset['date'].max().date()}")
    print(f"Total qty: {dataset['qty'].sum():,}")
    print(f"Total revenue: {dataset['revenue'].sum():,.2f} THB")
    print("=" * 70)
    print("Data Preprocessing Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
