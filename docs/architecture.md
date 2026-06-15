# System Architecture

## High-Level Workflow

```text
Business Problem
        │
        ▼
Synthetic Data Generation
        │
        ▼
Data Preprocessing
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Feature Engineering
        │
        ▼
Machine Learning Model
        │
        ▼
Demand Forecast
        │
        ▼
Inventory Recommendation
```

---

# Detailed Pipeline

## 1. Synthetic Data Generation

Input:

* Product Master
* Store Master
* Promotion Master

Output:

* Sales Transaction Dataset

Business Logic:

qty =
base_demand
× demand_multiplier
× seasonal_effect
× weekend_effect
× promotion_effect
× random_noise

---

## 2. Data Preprocessing

Tasks:

* Missing value handling
* Data type conversion
* Date formatting
* Data validation

Output:

Processed Dataset

---

## 3. Exploratory Data Analysis (EDA)

Analysis:

* Revenue Trend
* Product Performance
* Category Performance
* Store Performance
* Weekend vs Weekday Sales
* Promotion Impact

Output:

Charts and Business Insights

---

## 4. Feature Engineering

Time-Based Features:

* day_of_week
* month
* quarter
* is_weekend

Lag Features:

* lag_1
* lag_7
* lag_30

Rolling Statistics:

* rolling_mean_7
* rolling_mean_30

Output:

Model-ready dataset

---

## 5. Machine Learning Modeling

Baseline:

* Linear Regression

Primary Model:

* Random Forest Regressor

Evaluation Metrics:

* MAE
* RMSE

Output:

Demand Forecast Model

---

## 6. Demand Forecasting

Forecast Horizon:

* Next 7 Days

Prediction Granularity:

* Product Level
* Store Level

Output:

Forecast Dataset

---

## 7. Inventory Recommendation

Formula:

Recommended Order Quantity =
Forecast Demand - Current Inventory

Business Goal:

* Reduce stockout
* Reduce overstock

Output:

Inventory Recommendation Report

---

# Project Folder Structure

```text
project/
├── docs/
│   ├── project_spec.md
│   └── architecture.md
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── eda.ipynb
│   ├── feature_engineering.ipynb
│   └── modeling.ipynb
│
├── src/
│   ├── generate_mock_data.py
│   ├── data_preprocessing.py
│   ├── feature_engineering.py
│   └── train_model.py
│
├── output/
│   ├── charts/
│   └── forecast/
│
├── README.md
└── data_dictionary.md
```
