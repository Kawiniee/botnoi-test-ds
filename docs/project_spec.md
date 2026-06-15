# AI-Powered Demand Forecasting for Retail Inventory Optimization

## Project Overview

This project aims to develop a machine learning-based demand forecasting system for a convenience store chain.

The objective is to predict future product demand and provide inventory recommendations that help reduce stock shortages (Stockout) and excess inventory (Overstock).

---

# Business Problem

Many retail stores rely on manual estimation and historical experience when replenishing inventory.

This approach often leads to:

* Stockout (insufficient inventory)
* Overstock (excess inventory)
* Increased storage cost
* Lost sales opportunities

The project proposes an AI-powered forecasting solution that predicts future demand and supports inventory planning.

---

# Business Objectives

1. Forecast future product demand.
2. Reduce stockout events.
3. Reduce overstock situations.
4. Improve inventory management efficiency.

---

# Dataset Design

Because no real operational data is provided, synthetic data will be generated to simulate realistic retail operations.

The generated data should contain:

* Product demand patterns
* Store-specific demand differences
* Promotion effects
* Seasonal effects
* Weekend effects
* Natural random variation

---

# Data Sources

## Product Master

Columns:

* product_id
* product_name
* category
* unit_price
* base_demand

---

## Store Master

Columns:

* store_id
* store_name
* store_type
* demand_multiplier

---

## Promotion Master

Columns:

* promotion_id
* promotion_name
* discount_percent
* demand_boost
* start_date
* end_date

---

## Sales Transaction

Columns:

* date
* store_id
* product_id
* promotion_id
* qty
* revenue

---

# Assumptions

Since no real retail dataset is available, the following fields are introduced solely for synthetic data generation:

* base_demand
* demand_multiplier
* demand_boost

These fields are used to simulate realistic business behavior and are not prediction targets.

---

# Forecasting Target

Target Variable:

qty

Definition:

Number of units sold per product per day.

---

# Feature Engineering Plan

Time Features:

* day_of_week
* month
* quarter
* is_weekend

Historical Features:

* lag_1
* lag_7
* lag_30
* rolling_mean_7
* rolling_mean_30

Business Features:

* category
* store_type
* promotion_id
* discount_percent

---

# Machine Learning Approach

Baseline Model:

* Linear Regression

Main Model:

* Random Forest Regressor

Model Performance Metrics:

* MAE
* RMSE

---

# Expected Outputs

1. Daily demand forecast
2. Weekly demand forecast
3. Inventory recommendation
4. Business insights from EDA

---

# Deliverables

* Synthetic dataset
* EDA notebook
* Feature engineering notebook
* Modeling notebook
* Forecast results
* Presentation slides
* GitHub repository
