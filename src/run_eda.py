"""
EDA Script - รันการวิเคราะห์ข้อมูลเบื้องต้น
=============================================
Run เพื่อสร้าง Charts ทั้งหมด

Usage:
    python src/run_eda.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from pathlib import Path

from data_preprocessing import OUTPUT_PATH, prepare_retail_dataset, save_processed_data

warnings.filterwarnings('ignore')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12

# Restore default matplotlib settings (removed Thai font workaround)

sns.set_style("whitegrid")

# Create output directory
os.makedirs('output/charts', exist_ok=True)

print("="*60)
print("Starting EDA - Exploratory Data Analysis")
print("="*60)

# ============================================================================
# Load Data
# ============================================================================

print("\n[1/8] Loading data...")

if Path(OUTPUT_PATH).exists():
    df = pd.read_csv(OUTPUT_PATH, encoding='utf-8')
    print(f"   Loaded processed dataset: {OUTPUT_PATH}")
else:
    print("   Processed dataset not found. Running preprocessing pipeline...")
    df = prepare_retail_dataset()
    save_processed_data(df)
    print(f"   Saved processed dataset: {OUTPUT_PATH}")

df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.dayofweek
df['is_weekend'] = df['day_of_week'] >= 5
df['has_promo'] = df['promotion_id'] != 'PROMO00'

# English mapping for product names (original Thai preserved in product_name)
product_name_en = {
    'น้ำดื่ม 500ml': 'Water 500ml',
    'น้ำดื่ม 1.5L': 'Water 1.5L',
    'น้ำหวาน 350ml': 'Sweet Drink 350ml',
    'น้ำผลไม้ 500ml': 'Juice 500ml',
    'ข้าวเกรียบ': 'Rice Crisps',
    'มันช่วย': 'Potato Chips',
    'ถั่วเกลียว': 'Seasoned Nuts',
    'คุกกี้': 'Cookies',
    'มาม่า': 'Instant Noodles',
    'ยำ่ไง่': 'Spicy Salad',
    'ข้าวแกง': 'Curry Rice',
    'แชมพู': 'Shampoo',
    'สบู่': 'Soap',
    'น้ำยาล้างจาน': 'Dish Soap',
    'น้ำยาซักผ้า': 'Laundry Detergent'
}

print(f"   Loaded {len(df)} records")

# ============================================================================
# Data Quality Check
# ============================================================================

print("\n[2/8] Data Quality Check...")

# Missing values
missing = df.isnull().sum().sum()
print(f"   Missing values: {missing}")

# Duplicates
duplicates = df.duplicated(subset=['date', 'store_id', 'product_id']).sum()
print(f"   Duplicate records: {duplicates}")

# ============================================================================
# 1. Revenue Trend
# ============================================================================

print("\n[3/8] Generating Revenue Trend chart...")

monthly_revenue = df.groupby(['year', 'month'])['revenue'].sum().reset_index()
monthly_revenue['date'] = pd.to_datetime(
    monthly_revenue['year'].astype(str) + '-' +
    monthly_revenue['month'].astype(str) + '-01'
)

plt.figure(figsize=(14, 6))
plt.plot(monthly_revenue['date'], monthly_revenue['revenue'] / 1e6,
         marker='o', linewidth=2, markersize=6, color='#2E86AB')
plt.fill_between(monthly_revenue['date'], monthly_revenue['revenue'] / 1e6,
                 alpha=0.3, color='#2E86AB')
plt.title('Revenue Trend Over Time (2025-2026)', fontsize=14, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Revenue (Million THB)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('output/charts/revenue_trend.png', dpi=150, bbox_inches='tight')
plt.close()

print("   Saved: output/charts/revenue_trend.png")

# ============================================================================
# 2. Sales Trend
# ============================================================================

print("\n[4/8] Generating Sales Trend chart...")

monthly_qty = df.groupby(['year', 'month'])['qty'].sum().reset_index()
monthly_qty['date'] = pd.to_datetime(
    monthly_qty['year'].astype(str) + '-' +
    monthly_qty['month'].astype(str) + '-01'
)

plt.figure(figsize=(14, 6))
plt.bar(monthly_qty['date'], monthly_qty['qty'] / 1000,
        color='#A23B72', alpha=0.8, width=20)
plt.title('Sales Quantity Trend Over Time', fontsize=14, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Quantity (Thousands)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('output/charts/sales_trend.png', dpi=150, bbox_inches='tight')
plt.close()

print("   Saved: output/charts/sales_trend.png")

# ============================================================================
# 3. Top Products
# ============================================================================

print("\n[5/8] Generating Top Products chart...")

top_products = df.groupby('product_name')['qty'].sum().sort_values(ascending=False).head(15)

plt.figure(figsize=(12, 8))
colors = plt.cm.RdYlGn(np.linspace(0.8, 0.2, len(top_products)))
plt.barh(range(len(top_products)), top_products.values, color=colors)
plt.yticks(range(len(top_products)), top_products.index.map(product_name_en))
plt.xlabel('Total Quantity Sold', fontsize=12)
plt.title('Top 15 Best Selling Products', fontsize=14, fontweight='bold')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('output/charts/top_products.png', dpi=150, bbox_inches='tight')
plt.close()

print("   Saved: output/charts/top_products.png")

# ============================================================================
# 4. Category Performance
# ============================================================================

print("\n[6/8] Generating Category Performance chart...")

category_perf = df.groupby('category').agg({
    'revenue': 'sum',
    'qty': 'sum'
}).sort_values('revenue', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

colors = plt.cm.Set3(np.linspace(0, 1, len(category_perf)))
axes[0].pie(category_perf['revenue'], labels=category_perf.index,
           autopct='%1.1f%%', colors=colors, startangle=90)
axes[0].set_title('Revenue by Category', fontsize=12, fontweight='bold')

axes[1].bar(category_perf.index, category_perf['qty'], color=colors)
axes[1].set_xlabel('Category', fontsize=12)
axes[1].set_ylabel('Quantity Sold', fontsize=12)
axes[1].set_title('Quantity by Category', fontsize=12, fontweight='bold')
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
plt.savefig('output/charts/category_performance.png', dpi=150, bbox_inches='tight')
plt.close()

print("   Saved: output/charts/category_performance.png")

# ============================================================================
# 5. Store Performance
# ============================================================================

store_perf = df.groupby('store_type').agg({
    'revenue': 'sum',
    'qty': 'sum'
}).sort_values('revenue', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

store_colors = {'Central': '#2E86AB', 'Community': '#A23B72', 'Express': '#F18F01'}
colors = [store_colors.get(x, '#888888') for x in store_perf.index]

axes[0].bar(store_perf.index, store_perf['revenue'] / 1e6, color=colors)
axes[0].set_ylabel('Revenue (Million THB)', fontsize=12)
axes[0].set_title('Revenue by Store Type', fontsize=12, fontweight='bold')

axes[1].bar(store_perf.index, store_perf['qty'] / 1000, color=colors)
axes[1].set_ylabel('Quantity (Thousands)', fontsize=12)
axes[1].set_title('Quantity by Store Type', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('output/charts/store_performance.png', dpi=150, bbox_inches='tight')
plt.close()

print("   Saved: output/charts/store_performance.png")

# ============================================================================
# 6. Weekend vs Weekday
# ============================================================================

daily_sales = df.groupby(['date', 'is_weekend']).agg({
    'revenue': 'sum',
    'qty': 'sum'
}).reset_index()

weekend_weekday = daily_sales.groupby('is_weekend').agg({
    'revenue': 'mean',
    'qty': 'mean'
}).reset_index()

weekend_weekday['day_type'] = weekend_weekday['is_weekend'].map({True: 'Weekend', False: 'Weekday'})

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

colors = ['#F18F01', '#2E86AB']
axes[0].bar(weekend_weekday['day_type'], weekend_weekday['revenue'] / 1e6, color=colors)
axes[0].set_ylabel('Average Daily Revenue (Million THB)', fontsize=12)
axes[0].set_title('Avg Daily Revenue: Weekend vs Weekday', fontsize=12, fontweight='bold')

axes[1].bar(weekend_weekday['day_type'], weekend_weekday['qty'] / 1000, color=colors)
axes[1].set_ylabel('Average Daily Quantity (Thousands)', fontsize=12)
axes[1].set_title('Avg Daily Quantity: Weekend vs Weekday', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('output/charts/weekend_weekday.png', dpi=150, bbox_inches='tight')
plt.close()

weekend_qty = weekend_weekday[weekend_weekday['day_type'] == 'Weekend']['qty'].values[0]
weekday_qty = weekend_weekday[weekend_weekday['day_type'] == 'Weekday']['qty'].values[0]
print(f"   Saved: output/charts/weekend_weekday.png (Weekend Effect: +{(weekend_qty/weekday_qty - 1)*100:.1f}%)")

# ============================================================================
# 7. Promotion Effectiveness
# ============================================================================

df['has_promo'] = df['promotion_id'] != 'PROMO00'

promo_effect = df.groupby('has_promo').agg({
    'revenue': 'mean',
    'qty': 'mean'
}).reset_index()

promo_effect['promo_status'] = promo_effect['has_promo'].map({True: 'With Promotion', False: 'No Promotion'})

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

colors = ['#888888', '#2E86AB']

axes[0].bar(promo_effect['promo_status'], promo_effect['revenue'], color=colors)
axes[0].set_ylabel('Average Revenue per Row (THB)', fontsize=12)
axes[0].set_title('Avg Revenue: Promotion vs No Promotion', fontsize=12, fontweight='bold')

axes[1].bar(promo_effect['promo_status'], promo_effect['qty'], color=colors)
axes[1].set_ylabel('Average Quantity per Row', fontsize=12)
axes[1].set_title('Avg Quantity: Promotion vs No Promotion', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('output/charts/promo_effectiveness.png', dpi=150, bbox_inches='tight')
plt.close()

with_promo = promo_effect[promo_effect['has_promo'] == True]['qty'].values[0]
without_promo = promo_effect[promo_effect['has_promo'] == False]['qty'].values[0]
print(f"   Saved: output/charts/promo_effectiveness.png (Promo Effect: +{(with_promo/without_promo - 1)*100:.1f}%)")

# ============================================================================
# 8. Monthly Seasonality
# ============================================================================

monthly_cat = df.groupby(['month', 'category'])['qty'].sum().unstack()

plt.figure(figsize=(14, 7))
monthly_cat.plot(kind='line', marker='o', linewidth=2, ax=plt.gca())

plt.title('Monthly Seasonality by Product Category', fontsize=14, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Quantity Sold', fontsize=12)
plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.legend(title='Category', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('output/charts/monthly_seasonality.png', dpi=150, bbox_inches='tight')
plt.close()

print("   Saved: output/charts/monthly_seasonality.png")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*60)
print("EDA Complete!")
print("="*60)

print("\nSummary:")
print(f"  - Total Records: {len(df):,}")
print(f"  - Date Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
print(f"  - Total Revenue: {df['revenue'].sum():,.2f} THB")
print(f"  - Total Quantity: {df['qty'].sum():,}")

print("\nCharts saved to: output/charts/")
print("  1. revenue_trend.png")
print("  2. sales_trend.png")
print("  3. top_products.png")
print("  4. category_performance.png")
print("  5. store_performance.png")
print("  6. weekend_weekday.png")
print("  7. promo_effectiveness.png")
print("  8. monthly_seasonality.png")
