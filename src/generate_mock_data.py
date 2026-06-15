"""
Mock Data Generator สำหรับ Retail Demand Forecasting
=====================================================

Purpose: สร้างข้อมูลจำลองที่สมจริงสำหรับการทำ Demand Forecasting
Author: Data Science Team
Date: 2026-06-14

This script generates:
- Product Master Table
- Store Master Table
- Promotion Master Table
- Sales Transaction Table

Date Range: 2025-01-01 to 2026-12-31 (2 ปี)

Business Logic:
qty = base_demand × demand_multiplier × seasonal_effect ×
      weekend_effect × promotion_effect × random_noise
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION - ตั้งค่า Config หลัก
# ============================================================================

RANDOM_SEED = 42  # ใช้ seed เดียวกันเพื่อความ reproducible
START_DATE = '2025-01-01'
END_DATE = '2026-12-31'

# จำนวนข้อมูลที่ต้องการสร้าง
NUM_PRODUCTS = 15      # จำนวนสินค้า (ลดจาก 40)
NUM_STORES = 5         # จำนวนร้าน (ลดจาก 12)
PROMOTION_COVERAGE = 0.2  # 20% ของวันมีโปรโมชัน

np.random.seed(RANDOM_SEED)


# ============================================================================
# STEP 1: สร้าง Product Master
# ============================================================================

def generate_product_master():
    """
    สร้าง Product Master Table

    Columns:
    - product_id: รหัสสินค้า
    - product_name: ชื่อสินค้า
    - category: หมวดหมู่สินค้า
    - unit_price: ราคาต่อหน่วย
    - base_demand: ความต้องการพื้นฐานต่อวัน (ก่อนปรับ effects)

    หมวดหมู่สินค้าที่เหมาะสมกับ Convenience Store:
    """

    # หมวดหมู่สินค้าแบบ Convenience Store (รวม 15 ชนิด)
    categories = {
        'Beverage': 4,       # เครื่องดื่ม 4 ชนิด (เหลือ 15 รวม)
        'Snack': 4,          # ขนม 4 ชนิด
        'Instant Food': 3,   # อาหารแห้ง/Instant 3 ชนิด
        'Personal Care': 2,  # ของใช้ส่วนตัว 2 ชนิด
        'Household': 2       # ของใช้ในบ้าน 2 ชนิด
    }

    products = []
    product_id = 1

    # สร้างสินค้าตามหมวดหมู่
    for category, count in categories.items():
        for i in range(count):
            # ชื่อสินค้าตามหมวดหมู่
            if category == 'Beverage':
                names = ['น้ำดื่ม 500ml', 'น้ำดื่ม 1.5L', 'น้ำหวาน 350ml',
                        'น้ำผลไม้ 500ml', 'กาแฟพร้อมดื่ม', 'ชาเขียว 500ml',
                        'น้ำโซดา 350ml', 'น้ำมะนาว 500ml', 'เบียร์ 0%', 'น้ำผึ้ง 350ml',
                        'น้ำส้ม 500ml', 'น้ำมะม่วง 350ml']
                name = names[i] if i < len(names) else f'{category} {i+1}'
            elif category == 'Snack':
                names = ['ข้าวเกรียบ', 'มันช่วย', 'ถั่วเกลียว', 'คุกกี้', 'ช็อคโกแลต',
                        'ลูกชุบ', 'ขนมปัง', 'ไส้กรอก', 'ลูกชิ้น', 'หมูปิ้ง']
                name = names[i] if i < len(names) else f'{category} {i+1}'
            elif category == 'Instant Food':
                names = ['มาม่า', 'ยำ่ไง่', 'ข้าวแกง', 'โรตีสำเร็จ', 'สตูว์',
                        'ไข่ต้ม', 'ข้าวต้ม', 'สปาเก็ตตี้']
                name = names[i] if i < len(names) else f'{category} {i+1}'
            elif category == 'Personal Care':
                names = ['แชมพู', 'สบู่', 'ยาสีฟัน', 'ครีมอาบน้ำ', 'ลิปบาล์ม']
                name = names[i] if i < len(names) else f'{category} {i+1}'
            else:  # Household
                names = ['น้ำยาล้างจาน', 'น้ำยาซักผ้า', 'ทิชชู่', 'ถุงขยะ', 'แว็กซ์']
                name = names[i] if i < len(names) else f'{category} {i+1}'

            # ราคาต่อหน่วยตามหมวดหมู่ (บาท)
            if category == 'Beverage':
                price = np.random.uniform(10, 30)
            elif category == 'Snack':
                price = np.random.uniform(10, 25)
            elif category == 'Instant Food':
                price = np.random.uniform(25, 60)
            elif category == 'Personal Care':
                price = np.random.uniform(30, 100)
            else:  # Household
                price = np.random.uniform(20, 80)

            # ความต้องการพื้นฐาน (units/day)
            # ของที่ขายเร็ว (เครื่องดื่ม, ขนม) มี base_demand สูงกว่า
            if category in ['Beverage', 'Snack']:
                base_demand = np.random.randint(30, 100)
            else:
                base_demand = np.random.randint(10, 50)

            products.append({
                'product_id': f'P{product_id:03d}',
                'product_name': name,
                'category': category,
                'unit_price': round(price, 2),
                'base_demand': base_demand
            })
            product_id += 1

    return pd.DataFrame(products)


# ============================================================================
# STEP 2: สร้าง Store Master
# ============================================================================

def generate_store_master():
    """
    สร้าง Store Master Table

    Columns:
    - store_id: รหัสร้าน
    - store_name: ชื่อร้าน
    - store_type: ประเภทร้าน
    - demand_multiplier: ตัวคูณความต้องการ

    Store Types:
    - Central: ร้านในห้าง/ตลาดกลาง (demand สูง)
    - Community: ร้านในชุมชน (demand ปานกลาง)
    - Express: ร้านสะดวกซื้อริมทาง (demand ต่ำ-ปานกลาง)
    - Kiosk: ร้านเล็ก/แผงลอย (demand ต่ำ)
    """

    store_types = {
        'Central': 2,        # 2 ร้านในห้าง (ลดจาก 12 รวม)
        'Community': 2,      # 2 ร้านในชุมชน
        'Express': 1         # 1 ร้านสะดวกซื้อ
    }

    type_names = {
        'Central': ['ห้างสยาม', 'ห้างเซ็นทรัล'],
        'Community': ['ชุมชนเจริญ', 'ชุมชนราษฎร์'],
        'Express': ['ปั๊มน้ำมัน']
    }

    stores = []
    store_id = 1

    for store_type, count in store_types.items():
        for i in range(count):
            # กำหนด demand multiplier ตามประเภทร้าน
            if store_type == 'Central':
                multiplier = np.random.uniform(1.5, 2.0)
                name = type_names['Central'][i] if i < len(type_names['Central']) else f'{store_type} {i+1}'
            elif store_type == 'Community':
                multiplier = np.random.uniform(1.0, 1.2)
                name = type_names['Community'][i] if i < len(type_names['Community']) else f'{store_type} {i+1}'
            elif store_type == 'Express':
                multiplier = np.random.uniform(0.8, 1.0)
                name = type_names['Express'][i] if i < len(type_names['Express']) else f'{store_type} {i+1}'
            else:  # Kiosk
                multiplier = np.random.uniform(0.5, 0.7)
                name = type_names['Kiosk'][i] if i < len(type_names['Kiosk']) else f'{store_type} {i+1}'

            stores.append({
                'store_id': f'S{store_id:03d}',
                'store_name': name,
                'store_type': store_type,
                'demand_multiplier': round(multiplier, 2)
            })
            store_id += 1

    return pd.DataFrame(stores)


# ============================================================================
# STEP 3: สร้าง Promotion Master
# ============================================================================

def generate_promotion_master():
    """
    สร้าง Promotion Master Table

    Columns:
    - promotion_id: รหัสโปรโมชัน
    - promotion_name: ชื่อโปรโมชัน
    - discount_percent: เปอร์เซ็นต์ส่วนลด
    - demand_boost: ตัวคูณเพิ่มความต้องการ
    - start_date: วันเริ่มโปร
    - end_date: วันสิ้นสุดโปร

    Promotion Types:
    - No Discount: ไม่ลดราคา
    - Small Promo: ลด 5-15%
    - Medium Promo: ลด 15-30%
    - Big Promo: ลด 30-50%
    """

    promotions = []

    # Promotion แรก: ไม่มีโปร (baseline)
    promotions.append({
        'promotion_id': 'PROMO00',
        'promotion_name': 'No Promotion',
        'discount_percent': 0,
        'demand_boost': 0,
        'start_date': START_DATE,
        'end_date': END_DATE
    })

    # สร้างโปรแบบต่างๆ (ปรับ demand_boost ให้สมจริงขึ้น)
    # Small: +10% to +20%, Medium: +20% to +40%, Large: +40% to +60%
    promo_configs = [
        {'name_prefix': 'ลด 10%', 'discount': (5, 15), 'boost': (0.10, 0.20)},   # Small: 10-20%
        {'name_prefix': 'ลด 20%', 'discount': (15, 25), 'boost': (0.20, 0.40)},   # Medium: 20-40%
        {'name_prefix': 'ลด 30%', 'discount': (25, 35), 'boost': (0.40, 0.60)},   # Large: 40-60%
    ]

    promo_id = 1

    # สร้าง promotions หลายๆ แบบ โดยกระจายตลอดปี
    for year in [2025, 2026]:
        for month in range(1, 13):
            # เดือนละ 2-3 โปร
            num_promos = np.random.randint(2, 4)

            for _ in range(num_promos):
                config = np.random.choice(promo_configs)

                # สุ่มวันเริ่ม-สิ้นสุด (ประมาณ 7-14 วัน)
                start_day = np.random.randint(1, 25)
                duration = np.random.randint(7, 15)

                start_date = f'{year}-{month:02d}-{start_day:02d}'
                end_day = min(start_day + duration, 28)
                end_date = f'{year}-{month:02d}-{end_day:02d}'

                discount = np.random.uniform(*config['discount'])
                boost = np.random.uniform(*config['boost'])

                promotions.append({
                    'promotion_id': f'PROMO{promo_id:02d}',
                    'promotion_name': f"{config['name_prefix']} {year}",
                    'discount_percent': round(discount, 1),
                    'demand_boost': round(boost, 2),
                    'start_date': start_date,
                    'end_date': end_date
                })
                promo_id += 1

    return pd.DataFrame(promotions)


# ============================================================================
# STEP 4: สร้าง Sales Transaction พร้อม Effects ทั้งหมด
# ============================================================================

def generate_sales_transaction(product_df, store_df, promo_df):
    """
    สร้าง Sales Transaction Table

    Business Logic:
    qty = base_demand × demand_multiplier × seasonal_effect ×
          weekend_effect × promotion_effect × random_noise

    Effects ที่ต้องใส่:
    1. Seasonal Effect: ความต้องการตามฤดูกาล
    2. Weekend Effect: ยอดขายวันหยุด vs วันธรรมดา
    3. Promotion Effect: โปรโมชันเพิ่มยอดขาย
    4. Random Noise: ความสุ่มตามธรรมชาติ

    Parameters:
    - product_df: Product Master DataFrame
    - store_df: Store Master DataFrame
    - promo_df: Promotion Master DataFrame
    """

    # สร้าง date range
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='D')

    print(f"Generating sales for {len(date_range)} days...")
    print(f"   {len(product_df)} products x {len(store_df)} stores = {len(date_range) * len(product_df) * len(store_df):,} combinations")

    # เตรียมข้อมูลสำหรับ merge
    products = product_df.copy()
    stores = store_df.copy()
    promotions = promo_df.copy()

    # แปลง date columns
    promotions['start_date'] = pd.to_datetime(promotions['start_date'])
    promotions['end_date'] = pd.to_datetime(promotions['end_date'])

    all_sales = []

    # =====================================================================
    # Category-Specific Seasonality Configuration
    # =====================================================================
    # กำหนดว่า category ไหนมี peak ในเดือนไหน
    category_seasonality = {
        'Beverage': {'peak_months': [3, 4, 5], 'peak_effect': (1.15, 1.30)},      # ร้อน (Mar-May)
        'Instant Food': {'peak_months': [6, 7, 8, 9, 10], 'peak_effect': (1.15, 1.30)},  # ฝน (Jun-Oct)
        'Snack': {'peak_months': [11, 12], 'peak_effect': (1.20, 1.35)},           # ปีใหม่ (Nov-Dec)
        'Personal Care': {'peak_months': list(range(1, 13)), 'peak_effect': (0.98, 1.05)}, # คงที่ตลอดปี
        'Household': {'peak_months': [11, 12], 'peak_effect': (1.05, 1.15)}        # ปลายปี +10%
    }

    # Generate sales for each date
    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        month = date.month
        day_of_week = date.dayofweek  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5  # Saturday=5, Sunday=6

        # =====================================================================
        # EFFECT 1: Overall Seasonal Factor (ตามฤดูกาลทั่วไป)
        # =====================================================================
        # สมมติฐาน:
        # - ปลายปี (11-12): สูงสุด เพราะวันหยุดเยอะ
        # - กลางปี (5-10): สูงขึ้นเล็กน้อย เพราะฝน คนอยู่บ้าน
        # - ต้นปี (1-4): ต่ำสุด หลังปีใหม่

        if month in [11, 12]:
            overall_seasonal = np.random.uniform(1.1, 1.3)  # สูงสุด
        elif month in [5, 6, 7, 8, 9, 10]:
            overall_seasonal = np.random.uniform(1.0, 1.15)  # กลางๆ
        else:  # 1-4
            overall_seasonal = np.random.uniform(0.85, 1.0)  # ต่ำสุด

        # =====================================================================
        # EFFECT 2: Weekend Effect (วันหยุดสุดสัปดาห์)
        # =====================================================================
        # สมมติฐาน:
        # - วันธรรมดา: คนทำงาน ซื้อเครื่องดื่ม/อาหารเช้า-กลางวัน
        # - วันหยุด: ยอดขายสูงขึ้น 15-30% เพราะคนว่าง

        if is_weekend:
            weekend_factor = np.random.uniform(1.15, 1.30)
        else:
            weekend_factor = np.random.uniform(0.90, 1.05)

        # =====================================================================
        # EFFECT 3: Promotion Effect (โปรโมชัน)
        # =====================================================================
        # หาโปรที่ active ในวันนี้
        active_promos = promotions[
            (promotions['start_date'] <= date) &
            (promotions['end_date'] >= date)
        ]

        # สำหรับแต่ละ store-product combination
        for _, product in products.iterrows():
            for _, store in stores.iterrows():
                # พื้นฐาน demand
                base_qty = product['base_demand']

                # คูณด้วย store multiplier
                store_multiplier = store['demand_multiplier']

                # =====================================================================
                # EFFECT 4: Category-Specific Seasonality (ตามฤดูกาลเฉพาะหมวด)
                # =====================================================================
                # Beverage: Peak during hot season (Mar-May)
                # Instant Food: Peak during rainy season (Jun-Oct)
                # Snack: Peak during holiday season (Nov-Dec)
                # Personal Care: Stable throughout the year
                # Household: Slight increase during year-end
                category = product['category']

                # ดึง config ของ category นี้
                cat_config = category_seasonality.get(category, {'peak_months': [], 'peak_effect': (1.0, 1.0)})

                # ถ้าเดือนปัจจุบันตรงกับ peak months ของ category → ใช้ peak_effect
                if month in cat_config['peak_months']:
                    category_seasonal_factor = np.random.uniform(*cat_config['peak_effect'])
                else:
                    # ถ้าไม่ตรง → ใช้ baseline หรือต่ำลงเล็กน้อย
                    category_seasonal_factor = np.random.uniform(0.90, 1.05)

                # =====================================================================
                # EFFECT 5: Category-Weekend Pattern (pattern วันหยุดเฉพาะหมวด)
                # =====================================================================
                # เครื่องดื่มขายเยอะวันจันทร์-ศุกร์ (คนทำงาน)
                # ขนมขายเยอะวันหยุด
                if category == 'Beverage':
                    if is_weekend:
                        category_weekend_factor = np.random.uniform(0.8, 0.95)
                    else:
                        category_weekend_factor = np.random.uniform(1.0, 1.2)
                elif category == 'Snack':
                    if is_weekend:
                        category_weekend_factor = np.random.uniform(1.1, 1.3)
                    else:
                        category_weekend_factor = np.random.uniform(0.9, 1.05)
                else:
                    category_weekend_factor = np.random.uniform(0.95, 1.1)

                # =====================================================================
                # EFFECT 6: Promotion (ถ้ามีโปรใช้โปร ถ้าไม่มีใช้ baseline)
                # =====================================================================
                if len(active_promos) > 0:
                    # สุ่มเลือกโปร (20% ว่างเปล่า, 80% มีโปร)
                    if np.random.random() < 0.2:
                        promotion_id = 'PROMO00'  # ไม่มีโปร
                        promo_discount = 0
                        promo_effect = 1.0
                    else:
                        promo = active_promos.sample(1).iloc[0]
                        promotion_id = promo['promotion_id']
                        promo_discount = promo['discount_percent']
                        # Demand boost ตาม discount
                        promo_effect = 1.0 + promo['demand_boost']
                else:
                    promotion_id = 'PROMO00'
                    promo_discount = 0
                    promo_effect = 1.0

                # =====================================================================
                # EFFECT 7: Random Noise (ความสุ่มธรรมชาติ)
                # =====================================================================
                # สุ่ม noise ±15% ของ demand
                noise = np.random.uniform(0.85, 1.15)

                # =====================================================================
                # คำนวณ final qty
                # =====================================================================
                # ใช้สูตรใหม่ที่รวม category-specific seasonality
                qty = (base_qty * store_multiplier * overall_seasonal *
                       weekend_factor * category_seasonal_factor *
                       category_weekend_factor * promo_effect * noise)

                # ปัดเศษเป็นจำนวนเต็ม (ขั้นต่ำ 0)
                qty = max(0, int(round(qty)))

                # =====================================================================
                # คำนวณ revenue
                # =====================================================================
                # Revenue = qty × unit_price × (1 - discount/100)
                unit_price = product['unit_price']
                revenue = qty * unit_price * (1 - promo_discount / 100)

                # =====================================================================
                # บันทึกข้อมูล
                # =====================================================================
                all_sales.append({
                    'date': date_str,
                    'store_id': store['store_id'],
                    'product_id': product['product_id'],
                    'promotion_id': promotion_id,
                    'qty': qty,
                    'revenue': round(revenue, 2)
                })

    return pd.DataFrame(all_sales)


# ============================================================================
# STEP 5: บันทึกข้อมูลลง CSV
# ============================================================================

def save_to_csv(df, filename):
    """
    บันทึก DataFrame เป็น CSV

    Parameters:
    - df: DataFrame ที่ต้องการบันทึก
    - filename: ชื่อไฟล์ (ไม่รวม path)
    """
    output_dir = 'data/raw'
    output_path = os.path.join(output_dir, filename)

    # บันทึก (ไม่ต้องการ index column) - ใช้ UTF-8 encoding
    df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"Saved: {output_path} ({len(df):,} rows)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main Function: รันทั้งหมดตามลำดับ

    Step 1: Generate Product Master
    Step 2: Generate Store Master
    Step 3: Generate Promotion Master
    Step 4: Generate Sales Transaction
    Step 5: Save to CSV
    """

    print("=" * 70)
    print("Starting Mock Data Generation for Demand Forecasting")
    print("=" * 70)
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"Random Seed: {RANDOM_SEED}")
    print()

    # Step 1: Generate Product Master
    print("Step 1: Generating Product Master...")
    product_df = generate_product_master()
    save_to_csv(product_df, 'product_master.csv')
    print(f"   Created {len(product_df)} products in {product_df['category'].nunique()} categories")
    print()

    # Step 2: Generate Store Master
    print("Step 2: Generating Store Master...")
    store_df = generate_store_master()
    save_to_csv(store_df, 'store_master.csv')
    print(f"   Created {len(store_df)} stores: {store_df['store_type'].value_counts().to_dict()}")
    print()

    # Step 3: Generate Promotion Master
    print("Step 3: Generating Promotion Master...")
    promo_df = generate_promotion_master()
    save_to_csv(promo_df, 'promotion_master.csv')
    print(f"   Created {len(promo_df)} promotions (including no-promo baseline)")
    print()

    # Step 4: Generate Sales Transaction
    print("Step 4: Generating Sales Transaction...")
    sales_df = generate_sales_transaction(product_df, store_df, promo_df)
    save_to_csv(sales_df, 'sales_transaction.csv')
    print()

    # Summary Statistics
    print("=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    print(f"   Total Sales Records: {len(sales_df):,}")
    print(f"   Total Revenue: THB {sales_df['revenue'].sum():,.2f}")
    print(f"   Total Quantity Sold: {sales_df['qty'].sum():,}")
    print(f"   Average Daily Sales: {sales_df.groupby('date')['qty'].sum().mean():.0f} units")
    print(f"   Date Range: {sales_df['date'].min()} to {sales_df['date'].max()}")
    print()

    # Effect Analysis
    print("Effect Breakdown (Sample):")
    print("-" * 40)

    # Weekend vs Weekday
    sales_df['date_dt'] = pd.to_datetime(sales_df['date'])
    sales_df['is_weekend'] = sales_df['date_dt'].dt.dayofweek >= 5
    weekend_sales = sales_df[sales_df['is_weekend']].groupby('date')['qty'].sum().mean()
    weekday_sales = sales_df[~sales_df['is_weekend']].groupby('date')['qty'].sum().mean()
    print(f"   Weekend Avg Daily: {weekend_sales:,.0f} units")
    print(f"   Weekday Avg Daily: {weekday_sales:,.0f} units")
    print(f"   Weekend Effect: +{(weekend_sales/weekday_sales - 1)*100:.1f}%")
    print()

    # Promotion Effect (compare same day types)
    # Calculate weekday-only promotion effect
    weekday_sales_df = sales_df[~sales_df['is_weekend']]
    promo_on_weekday = weekday_sales_df[weekday_sales_df['promotion_id'] != 'PROMO00'].groupby('date')['qty'].sum().mean()
    no_promo_on_weekday = weekday_sales_df[weekday_sales_df['promotion_id'] == 'PROMO00'].groupby('date')['qty'].sum().mean()
    print(f"   Weekday with Promo: {promo_on_weekday:,.0f} units")
    print(f"   Weekday without Promo: {no_promo_on_weekday:,.0f} units")
    print(f"   Promotion Effect (weekday): +{(promo_on_weekday/no_promo_on_weekday - 1)*100:.1f}%")
    print()

    print("=" * 70)
    print("Mock Data Generation Complete!")
    print("=" * 70)

    return product_df, store_df, promo_df, sales_df


# รัน main function ถ้าเรียก script นี้โดยตรง
if __name__ == "__main__":
    product_df, store_df, promo_df, sales_df = main()