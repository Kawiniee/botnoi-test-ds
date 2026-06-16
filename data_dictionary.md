# Data Dictionary

เอกสารนี้อธิบายข้อมูลที่ใช้ในโปรเจกต์ AI-Powered Demand Forecasting for Retail Inventory Optimization โดยอิงจากไฟล์จริงใน `data/raw/` และ output ที่ออกแบบไว้ใน `data/processed/`

## Dataset Overview

ข้อมูลเป็น synthetic retail dataset สำหรับจำลองยอดขายร้านค้าปลีกและใช้วิเคราะห์ demand forecasting

Prediction target:

- `qty`: จำนวนสินค้าที่ขายได้

Prediction grain:

- `store-product-day`
- หนึ่งแถวหมายถึงยอดขายของสินค้า 1 รายการ ในร้าน 1 สาขา ในวันที่ 1 วัน

Primary key ของ transaction dataset:

- `date + store_id + product_id`

## Table Relationships

```text
sales_transaction
    product_id    -> product_master.product_id
    store_id      -> store_master.store_id
    promotion_id  -> promotion_master.promotion_id
```

## Raw Tables

### `data/raw/product_master.csv`

Primary key:

- `product_id`

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `product_id` | string | รหัสสินค้า | unique ต่อสินค้า |
| `product_name` | string | ชื่อสินค้า | มีชื่อภาษาไทย |
| `category` | string | หมวดหมู่สินค้า | เช่น Beverage, Snack, Instant Food |
| `unit_price` | float | ราคาต่อหน่วยก่อนส่วนลด | ต้องมากกว่า 0 |
| `base_demand` | integer | demand ตั้งต้นที่ใช้สร้างข้อมูลจำลอง | synthetic-only field |

ข้อควรระวัง:

- `base_demand` เป็นค่าที่ใช้สร้าง mock data ไม่ใช่ข้อมูลธุรกิจจริงที่มักมีให้ใช้โดยตรง
- ถ้าใช้ `base_demand` เป็น feature ใน model อาจทำให้ model ดีเกินจริง เพราะเป็นส่วนหนึ่งของ data generation logic

### `data/raw/store_master.csv`

Primary key:

- `store_id`

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `store_id` | string | รหัสสาขา | unique ต่อร้าน |
| `store_name` | string | ชื่อสาขา | มีชื่อภาษาไทย |
| `store_type` | string | ประเภทร้าน | เช่น Central, Community, Express |
| `demand_multiplier` | float | ตัวคูณ demand ที่ใช้สร้างข้อมูลจำลอง | synthetic-only field |

ข้อควรระวัง:

- `demand_multiplier` เป็นค่าจำลองความต่างของ demand ระหว่าง store type
- ไม่ควรใช้เป็น feature หลักใน MVP model หากต้องการจำลองสถานการณ์ธุรกิจจริง

### `data/raw/promotion_master.csv`

Primary key:

- `promotion_id`

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `promotion_id` | string | รหัสโปรโมชัน | `PROMO00` หมายถึงไม่มีโปรโมชัน |
| `promotion_name` | string | ชื่อโปรโมชัน | เช่น No Promotion, ลด 10% |
| `discount_percent` | float | เปอร์เซ็นต์ส่วนลด | ควรอยู่ระหว่าง 0 ถึง 100 |
| `demand_boost` | float | ค่ากระตุ้น demand ที่ใช้สร้างข้อมูลจำลอง | synthetic-only field |
| `start_date` | date/string | วันเริ่มโปรโมชัน | ต้องแปลงเป็น date ใน preprocessing |
| `end_date` | date/string | วันสิ้นสุดโปรโมชัน | ต้องไม่ก่อน `start_date` |

ข้อควรระวัง:

- `demand_boost` เป็น synthetic generation field
- ในงานจริงอาจไม่มีตัวเลข demand boost ให้ใช้ล่วงหน้า ต้องเรียนรู้ผลของ promotion จาก historical data แทน

### `data/raw/sales_transaction.csv`

Primary key เชิงธุรกิจ:

- `date + store_id + product_id`

Foreign keys:

- `product_id`
- `store_id`
- `promotion_id`

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `date` | date/string | วันที่ขาย | ต้องแปลงเป็น date ใน preprocessing |
| `store_id` | string | รหัสสาขา | join กับ `store_master` |
| `product_id` | string | รหัสสินค้า | join กับ `product_master` |
| `promotion_id` | string | รหัสโปรโมชัน | join กับ `promotion_master` |
| `qty` | integer | จำนวนสินค้าที่ขายได้ | target variable |
| `revenue` | float | รายได้หลังส่วนลด | คำนวณจาก `qty`, `unit_price`, `discount_percent` |

สูตร revenue ที่ใช้ตรวจสอบ:

```text
revenue = qty * unit_price * (1 - discount_percent / 100)
```

### `data/raw/current_inventory.csv`

Primary key เชิงธุรกิจ:

- `inventory_date + store_id + product_id`

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `inventory_date` | date | วันที่ snapshot ของ inventory | ปัจจุบันคือวันสุดท้ายของ sales data |
| `store_id` | string | รหัสสาขา | join กับ forecast output |
| `store_name` | string | ชื่อสาขา | ใช้เพื่ออ่านผลลัพธ์ |
| `product_id` | string | รหัสสินค้า | join กับ forecast output |
| `product_name` | string | ชื่อสินค้า | ใช้เพื่ออ่านผลลัพธ์ |
| `category` | string | หมวดหมู่สินค้า | ใช้เพื่อ group recommendation |
| `unit_price` | float | ราคาต่อหน่วย | ใช้คำนวณ inventory value |
| `current_inventory_qty` | integer | จำนวนสินค้าคงเหลือปัจจุบัน | mock จาก demand 30 วันล่าสุด |
| `inventory_value` | float | มูลค่า inventory ปัจจุบัน | `current_inventory_qty * unit_price` |
| `recent_avg_daily_qty` | float | ยอดขายเฉลี่ยรายวัน 30 วันล่าสุด | ใช้สร้าง mock inventory |
| `recent_max_daily_qty` | integer | ยอดขายสูงสุดรายวันใน 30 วันล่าสุด | ใช้ audit inventory level |
| `inventory_coverage_days` | float | จำนวนวันที่ inventory น่าจะครอบคลุมจาก recent average demand | ใช้ดู stock coverage |

## Processed Dataset

ไฟล์ output จาก preprocessing:

- `data/processed/retail_dataset.csv`

Grain:

- `store-product-day`

Primary key:

- `date + store_id + product_id`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `date` | date | วันที่ขาย | `sales_transaction` |
| `store_id` | string | รหัสสาขา | `sales_transaction` |
| `product_id` | string | รหัสสินค้า | `sales_transaction` |
| `promotion_id` | string | รหัสโปรโมชัน | `sales_transaction` |
| `qty` | integer | จำนวนขายต่อวัน | `sales_transaction` |
| `revenue` | float | รายได้หลังส่วนลด | `sales_transaction` |
| `product_name` | string | ชื่อสินค้า | `product_master` |
| `category` | string | หมวดหมู่สินค้า | `product_master` |
| `unit_price` | float | ราคาต่อหน่วยก่อนส่วนลด | `product_master` |
| `base_demand` | integer | demand ตั้งต้นใน mock data | `product_master` |
| `store_name` | string | ชื่อสาขา | `store_master` |
| `store_type` | string | ประเภทร้าน | `store_master` |
| `demand_multiplier` | float | store demand multiplier ใน mock data | `store_master` |
| `promotion_name` | string | ชื่อโปรโมชัน | `promotion_master` |
| `discount_percent` | float | เปอร์เซ็นต์ส่วนลด | `promotion_master` |
| `demand_boost` | float | promotion demand boost ใน mock data | `promotion_master` |
| `promo_start_date` | date | วันเริ่มโปรโมชัน | `promotion_master.start_date` |
| `promo_end_date` | date | วันสิ้นสุดโปรโมชัน | `promotion_master.end_date` |
| `has_promo` | boolean | มีโปรโมชันหรือไม่ | derived |
| `net_unit_price` | float | ราคาต่อหน่วยหลังส่วนลด | derived |
| `expected_revenue` | float | revenue ที่คำนวณจากสูตร | derived |
| `revenue_diff` | float | ส่วนต่างระหว่าง `revenue` กับ `expected_revenue` | derived |

## Validation Rules

กฎที่ preprocessing pipeline ควรตรวจ:

- ทุกไฟล์ต้องมี required columns ครบ
- primary key ของ master tables ต้องไม่ซ้ำ
- `date + store_id + product_id` ต้องไม่ซ้ำใน transaction
- transaction ทุกแถวต้อง join กับ product, store และ promotion master ได้
- date columns ต้อง parse ได้
- `promo_start_date <= promo_end_date`
- `qty >= 0`
- `revenue >= 0`
- `unit_price > 0`
- `0 <= discount_percent <= 100`
- `revenue_diff` ต้องใกล้ 0 หลังคำนวณ expected revenue

## Fields Not Recommended For MVP Modeling

คอลัมน์ต่อไปนี้ควรเก็บไว้เพื่อ audit และอธิบาย mock data แต่ไม่ควรใช้เป็น model features ใน MVP:

- `base_demand`
- `demand_multiplier`
- `demand_boost`

เหตุผลคือเป็นคอลัมน์ที่ถูกสร้างขึ้นเพื่อจำลองพฤติกรรมของข้อมูล ไม่ใช่ feature ที่มักมีพร้อมใช้งานในธุรกิจจริง

## Feature Dataset

ไฟล์ output จาก feature engineering:

- `data/processed/retail_features.csv`

Input:

- `data/processed/retail_dataset.csv`

Grain:

- `store-product-day`

หมายเหตุ:

- Feature dataset ตัด 30 วันแรกของแต่ละ `store_id + product_id` ออก เพราะต้องใช้ `lag_30` และ `rolling_mean_30`
- จำนวนแถวปัจจุบันคือ 52,500 แถว จาก processed dataset เดิม 54,750 แถว

### Engineered Features

| Column | Type | Meaning |
|---|---|---|
| `year` | integer | ปีของรายการขาย |
| `month` | integer | เดือนของรายการขาย |
| `quarter` | integer | ไตรมาสของรายการขาย |
| `week_of_year` | integer | สัปดาห์ของปีตาม ISO calendar |
| `day_of_week` | integer | วันในสัปดาห์ โดย Monday = 0 |
| `day_of_month` | integer | วันที่ในเดือน |
| `is_weekend` | boolean | เป็นวันเสาร์หรืออาทิตย์หรือไม่ |
| `has_promo` | boolean | มีโปรโมชันหรือไม่ |
| `promo_days_since_start` | integer | จำนวนวันที่ผ่านไปตั้งแต่เริ่มโปรโมชัน |
| `promo_days_until_end` | integer | จำนวนวันที่เหลือจนสิ้นสุดโปรโมชัน |
| `is_promo_start_day` | boolean | เป็นวันแรกของโปรโมชันหรือไม่ |
| `is_promo_end_day` | boolean | เป็นวันสุดท้ายของโปรโมชันหรือไม่ |
| `lag_1` | float | `qty` ของสินค้า-ร้านเดียวกันย้อนหลัง 1 วัน |
| `lag_7` | float | `qty` ของสินค้า-ร้านเดียวกันย้อนหลัง 7 วัน |
| `lag_14` | float | `qty` ของสินค้า-ร้านเดียวกันย้อนหลัง 14 วัน |
| `lag_30` | float | `qty` ของสินค้า-ร้านเดียวกันย้อนหลัง 30 วัน |
| `rolling_mean_7` | float | ค่าเฉลี่ย `qty` ย้อนหลัง 7 วัน โดยไม่รวมวันปัจจุบัน |
| `rolling_mean_14` | float | ค่าเฉลี่ย `qty` ย้อนหลัง 14 วัน โดยไม่รวมวันปัจจุบัน |
| `rolling_mean_30` | float | ค่าเฉลี่ย `qty` ย้อนหลัง 30 วัน โดยไม่รวมวันปัจจุบัน |
| `rolling_std_7` | float | ส่วนเบี่ยงเบนมาตรฐาน `qty` ย้อนหลัง 7 วัน |
| `rolling_median_7` | float | median ของ `qty` ย้อนหลัง 7 วัน |
| `category_month` | string | interaction ระหว่าง `category` และ `month` |
| `store_type_category` | string | interaction ระหว่าง `store_type` และ `category` |
| `promo_category` | string | interaction ระหว่างสถานะโปรโมชันและ `category` |

### Leakage Control

Lag และ rolling features ถูกสร้างแยกตามกลุ่ม:

```text
store_id + product_id
```

Rolling features ใช้ `shift(1)` ก่อน rolling เพื่อไม่ให้ `qty` ของวันปัจจุบันรั่วเข้า feature ของวันเดียวกัน

## Modeling Outputs

Modeling pipeline ใช้ไฟล์:

- Input: `data/processed/retail_features.csv`
- Script: `src/train_model.py`
- Output folder: `output/modeling/`

Models:

- Baseline: Linear Regression
- Main model: Random Forest Regressor

Evaluation split:

- ใช้ time-based split
- Test period ปัจจุบันคือ `2026-10-03` ถึง `2026-12-31`

### `output/modeling/metrics.csv`

| Column | Type | Meaning |
|---|---|---|
| `model` | string | ชื่อโมเดล |
| `train_rows` | integer | จำนวนแถว train |
| `test_rows` | integer | จำนวนแถว test |
| `test_start_date` | date | วันแรกของ test set |
| `test_end_date` | date | วันสุดท้ายของ test set |
| `MAE` | float | Mean Absolute Error |
| `RMSE` | float | Root Mean Squared Error |

### `output/modeling/predictions.csv`

| Column | Type | Meaning |
|---|---|---|
| `date` | date | วันที่ forecast ใน test set |
| `store_id` | string | รหัสสาขา |
| `product_id` | string | รหัสสินค้า |
| `qty` | integer | actual quantity |
| `model` | string | ชื่อโมเดลที่สร้าง prediction |
| `prediction` | float | predicted quantity |
| `absolute_error` | float | ค่าสัมบูรณ์ของ error ระหว่าง actual และ prediction |

### `output/modeling/feature_importance.csv`

| Column | Type | Meaning |
|---|---|---|
| `feature` | string | ชื่อ feature หลัง preprocessing |
| `importance` | float | feature importance จาก Random Forest |

### Modeling Charts

| File | Meaning |
|---|---|
| `model_comparison.png` | เปรียบเทียบ MAE/RMSE ระหว่าง Linear Regression และ Random Forest |
| `feature_importance.png` | แสดง feature importance ของ Random Forest |
| `actual_vs_predicted.png` | เปรียบเทียบ actual vs predicted ของ Random Forest |

## Forecasting Outputs

Forecasting pipeline ใช้ไฟล์:

- Inputs: `data/processed/retail_dataset.csv`, `data/processed/retail_features.csv`
- Script: `src/forecast.py`
- Output folder: `output/forecast/`

Forecast setup:

- Forecast horizon: 7 วัน
- Forecast grain: `store-product-day`
- Forecast period ปัจจุบัน: `2027-01-01` ถึง `2027-01-07`
- Model: Random Forest Regressor

Assumptions:

- ไม่มี future promotion calendar หลัง `2026-12-31` จึงใช้ `PROMO00` สำหรับทุก forecast row
- current inventory เป็น mock snapshot จากยอดขาย 30 วันล่าสุด ไม่ใช่ข้อมูล inventory จริงจากระบบธุรกิจ
- recommendation ใช้ safety stock 15% ของ forecast quantity

### `output/forecast/demand_forecast.csv`

| Column | Type | Meaning |
|---|---|---|
| `date` | date | วันที่ forecast |
| `store_id` | string | รหัสสาขา |
| `store_name` | string | ชื่อสาขา |
| `store_type` | string | ประเภทร้าน |
| `product_id` | string | รหัสสินค้า |
| `product_name` | string | ชื่อสินค้า |
| `category` | string | หมวดหมู่สินค้า |
| `promotion_id` | string | รหัสโปรโมชันที่ใช้ใน forecast |
| `has_promo` | boolean | มีโปรโมชันหรือไม่ |
| `unit_price` | float | ราคาต่อหน่วย |
| `forecast_qty` | float | จำนวน demand ที่ forecast |
| `forecast_revenue` | float | revenue ที่คำนวณจาก forecast quantity |

### `output/forecast/forecast_summary.csv`

| Column | Type | Meaning |
|---|---|---|
| `date` | date | วันที่ forecast |
| `store_type` | string | ประเภทร้าน |
| `category` | string | หมวดหมู่สินค้า |
| `forecast_qty` | float | forecast quantity รวม |
| `forecast_revenue` | float | forecast revenue รวม |
| `product_count` | integer | จำนวนสินค้าที่นับในกลุ่ม |
| `store_count` | integer | จำนวนร้านที่นับในกลุ่ม |

### `output/forecast/inventory_recommendation.csv`

Grain:

- `store-product` ต่อหนึ่ง forecast horizon

หมายเหตุ:

- ไฟล์นี้ aggregate forecast 7 วันจาก `demand_forecast.csv`
- ใช้ current inventory จาก `data/raw/current_inventory.csv`
- `recommended_order_qty = max(recommended_stock_qty - current_inventory_qty, 0)`

| Column | Type | Meaning |
|---|---|---|
| `forecast_start_date` | date | วันแรกของ forecast horizon |
| `forecast_end_date` | date | วันสุดท้ายของ forecast horizon |
| `forecast_days` | integer | จำนวนวันใน forecast horizon |
| `forecast_qty` | float | forecast demand รวมตลอด horizon |
| `forecast_revenue` | float | forecast revenue รวมตลอด horizon |
| `inventory_date` | date | วันที่ snapshot inventory |
| `current_inventory_qty` | integer | inventory ที่มีอยู่ปัจจุบัน |
| `inventory_value` | float | มูลค่า inventory ปัจจุบัน |
| `recent_avg_daily_qty` | float | demand เฉลี่ย 30 วันล่าสุด |
| `recent_max_daily_qty` | integer | demand สูงสุดใน 30 วันล่าสุด |
| `inventory_coverage_days` | float | stock coverage เทียบ recent average demand |
| `safety_stock_qty` | integer | safety stock 15% ของ forecast quantity |
| `recommended_stock_qty` | integer | forecast quantity + safety stock |
| `recommended_order_qty` | integer | จำนวนที่ควรสั่งเพิ่ม |
| `projected_remaining_qty` | float | inventory คงเหลือโดยประมาณหลังเจอ forecast demand |
| `stock_status` | string | สถานะ stock เช่น `Need Order`, `Enough Stock`, `Overstock Risk` |
