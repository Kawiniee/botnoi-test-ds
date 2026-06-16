# AI-Powered Demand Forecasting for Retail Inventory Optimization

โปรเจกต์นี้เป็น Data Science / AI solution proposal สำหรับธุรกิจ Retail SME โดยใช้ mock data เพื่อออกแบบแนวทางพยากรณ์ความต้องการสินค้า (`qty`) และสนับสนุนการวางแผนสต๊อกสินค้าให้ลดโอกาส stockout และ overstock ซึ่งเชื่อมโยงกับเป้าหมายหลักคือเพิ่มโอกาสสร้างรายได้จากการมีสินค้าพร้อมขายในเวลาที่เหมาะสม

## Business Problem

ร้านค้าปลีกมักวางแผนเติมสินค้าโดยอาศัยประสบการณ์หรือยอดขายย้อนหลังแบบ manual ทำให้เกิดปัญหา:

- สินค้าขาดสต๊อกและเสียโอกาสขาย
- สินค้าเกินสต๊อกและมีต้นทุนจัดเก็บ
- วางแผน promotion และ inventory ไม่สัมพันธ์กัน
- มองไม่เห็น demand pattern แยกตามสินค้า สาขา ฤดูกาล และโปรโมชัน

Solution ที่เสนอคือ demand forecasting ระดับ `store-product-day` เพื่อช่วยให้ทีมวางแผนสินค้ารู้ว่าสินค้าใดควรมี stock เท่าไรในแต่ละร้านและแต่ละช่วงเวลา

## Project Status

สถานะปัจจุบัน:

- Mock raw data สร้างแล้วครบ 4 ตาราง
- EDA เสร็จแล้ว มี charts และ business insights
- Data preprocessing pipeline ถูกแยกออกมาเป็น stage กลางของโปรเจกต์
- Feature engineering pipeline ถูกสร้างแล้ว และ output อยู่ที่ `data/processed/retail_features.csv`
- Modeling baseline และ main model ทำเสร็จแล้ว โดยเปรียบเทียบ Linear Regression กับ Random Forest Regressor
- Forecasting stage ทำเสร็จแล้ว โดย forecast 7 วันถัดไปที่ระดับ `store-product-day`
- Inventory recommendation ทำเสร็จแล้วโดยใช้ current inventory mock data
- Slide proposal ยังไม่ได้ทำ และตั้งใจทำหลังจัดระเบียบ repo เสร็จ

## Current Architecture

```text
Raw Data
    -> Data Preprocessing
    -> Feature Engineering
    -> Modeling
    -> Forecasting
```

คำอธิบายแต่ละ stage:

- Raw Data: mock CSV files ใน `data/raw/`
- Data Preprocessing: รวมตาราง ตรวจคุณภาพข้อมูล และสร้าง `data/processed/retail_dataset.csv`
- Feature Engineering: สร้าง time, promotion, lag และ rolling features แล้วบันทึกเป็น `data/processed/retail_features.csv`
- Modeling: train และ evaluate Linear Regression baseline กับ Random Forest Regressor ด้วย MAE/RMSE
- Forecasting: forecast 7 วันถัดไป และสร้าง inventory recommendation จาก current inventory mock data

## Folder Structure

```text
.
├── data/
│   ├── raw/                 # mock source data
│   └── processed/           # clean merged dataset for next stages
├── docs/
│   ├── original_requirement.docx
│   ├── project_spec.md
│   └── architecture.md
├── notebooks/
│   └── eda.ipynb
├── output/
│   ├── charts/              # canonical chart outputs
│   ├── modeling/            # model metrics, predictions, and model charts
│   └── forecast/            # forecast and inventory recommendation outputs
├── src/
│   ├── generate_mock_data.py
│   ├── generate_inventory_mock.py
│   ├── data_preprocessing.py
│   ├── run_eda.py
│   ├── feature_engineering.py
│   ├── train_model.py
│   └── forecast.py
├── README.md
└── data_dictionary.md
```

หมายเหตุ: Notebook ใช้สำหรับ EDA เท่านั้น ส่วน pipeline หลักของ preprocessing, feature engineering, modeling และ forecasting อยู่ใน `src/` เพื่อให้รันซ้ำได้เป็นลำดับชัดเจน

## Data

Raw data อยู่ใน `data/raw/`:

- `product_master.csv`: ข้อมูลสินค้า 15 รายการ
- `store_master.csv`: ข้อมูลร้าน 5 สาขา
- `promotion_master.csv`: ข้อมูลโปรโมชัน 63 รายการ
- `sales_transaction.csv`: ยอดขายรายวัน 54,750 แถว
- `current_inventory.csv`: mock inventory snapshot ระดับ `store-product`

Prediction target:

- `qty`: จำนวนหน่วยสินค้าที่ขายได้

Prediction grain:

- `store-product-day`
- Primary key เชิงธุรกิจคือ `date + store_id + product_id`

## How To Run

สร้าง mock data:

```bash
python src/generate_mock_data.py
```

สร้าง current inventory mock data:

```bash
python src/generate_inventory_mock.py
```

สร้าง processed dataset:

```bash
python src/data_preprocessing.py
```

รัน EDA และสร้าง charts:

```bash
python src/run_eda.py
```

สร้าง feature dataset สำหรับ modeling:

```bash
python src/feature_engineering.py
```

train และ evaluate models:

```bash
python src/train_model.py
```

สร้าง demand forecast 7 วันถัดไป:

```bash
python src/forecast.py
```

Expected outputs:

- `data/processed/retail_dataset.csv`
- `data/processed/retail_features.csv`
- charts ใน `output/charts/`
- model outputs ใน `output/modeling/`
- forecast outputs ใน `output/forecast/`

## EDA Summary

EDA ที่ทำแล้วพบ insight หลัก:

- ยอดขายมี seasonal pattern ชัดเจน โดยช่วงปลายปีสูงกว่าช่วงต้นปี
- Weekend มียอดขายต่างจาก weekday
- Category แต่ละกลุ่มมี seasonality ต่างกัน
- Store type มีผลต่อยอดขาย
- Promotion ช่วยเพิ่ม volume แต่ต้องระวัง margin และ stock planning

Charts ที่สร้างแล้ว:

- `revenue_trend.png`
- `sales_trend.png`
- `top_products.png`
- `category_performance.png`
- `store_performance.png`
- `weekend_weekday.png`
- `promo_effectiveness.png`
- `monthly_seasonality.png`

## Modeling Summary

Modeling ใช้ time-based split โดยทดสอบกับช่วง `2026-10-03` ถึง `2026-12-31`

| Model | MAE | RMSE |
|---|---:|---:|
| Random Forest Regressor | 12.16 | 19.12 |
| Linear Regression | 14.15 | 21.68 |

Random Forest ทำผลลัพธ์ดีกว่า baseline จากทั้ง MAE และ RMSE

Modeling outputs:

- `output/modeling/metrics.csv`
- `output/modeling/predictions.csv`
- `output/modeling/feature_importance.csv`
- `output/modeling/model_comparison.png`
- `output/modeling/feature_importance.png`
- `output/modeling/actual_vs_predicted.png`

## Forecasting Summary

Forecasting stage ใช้ Random Forest Regressor เป็นโมเดลหลัก และ forecast ช่วง `2027-01-01` ถึง `2027-01-07`

Forecast outputs:

- `output/forecast/demand_forecast.csv`
- `output/forecast/forecast_summary.csv`
- `output/forecast/inventory_recommendation.csv`

ผลรวม forecast ล่าสุด:

- Forecast rows: 525 แถว
- Total forecast qty: 47,530.14 units
- Total forecast revenue: 1,197,415.07 THB
- Recommendation rows: 75 แถว
- Need Order items: 46 store-product combinations
- Total recommended order qty: 10,973 units

Assumptions:

- ยังไม่มี future promotion calendar หลัง `2026-12-31` จึง forecast ด้วย `PROMO00`
- current inventory เป็น mock snapshot ที่สร้างจากยอดขายเฉลี่ย 30 วันล่าสุด
- recommendation ใช้ safety stock 15% จาก forecast demand

## Important Assumptions

ข้อมูลในโปรเจกต์นี้เป็น synthetic data เพราะไม่มี real operational data ให้ใช้

คอลัมน์ต่อไปนี้ถูกสร้างขึ้นเพื่อจำลองพฤติกรรมธุรกิจและควรระวังหากนำไปใช้เป็น model features:

- `base_demand`
- `demand_multiplier`
- `demand_boost`

คอลัมน์เหล่านี้ช่วยอธิบาย data generation logic แต่ในธุรกิจจริงมักไม่มีให้ใช้งานตรง ๆ จึงอาจทำให้เกิด leakage เชิงแนวคิดถ้าใช้ train model โดยไม่ระวัง

## Next Steps

ลำดับงานที่ควรทำต่อ:

1. ตรวจ sanity ของ recommendation output และเลือก insight สำคัญสำหรับ slide
2. เตรียม slide proposal เป็นขั้นสุดท้าย
