# ============================================================
# ServeIQ USA — Python EDA & Visualization
# File: notebooks/analysis.py
# Run: python notebooks/analysis.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# ── Visual theme ─────────────────────────────────────────────
sns.set_theme(style='whitegrid', palette='muted')
BLUE   = '#1B4F72'
ORANGE = '#E67E22'
RED    = '#C0392B'
GREEN  = '#1E8449'
GRAY   = '#7F8C8D'

plt.rcParams.update({
    'figure.dpi':       130,
    'font.family':      'DejaVu Sans',
    'axes.titlesize':   13,
    'axes.titleweight': 'bold',
    'axes.spines.top':  False,
    'axes.spines.right':False,
})

os.makedirs('visuals', exist_ok=True)

# ============================================================
# SECTION 1: LOAD DATA
# ============================================================

print("Loading data...")
bookings  = pd.read_csv('data/raw/bookings.csv',
                         parse_dates=['booking_date', 'service_date'])
users     = pd.read_csv('data/raw/users.csv',
                         parse_dates=['signup_date'])
providers = pd.read_csv('data/raw/providers.csv',
                         parse_dates=['join_date'])
services  = pd.read_csv('data/raw/services.csv')

print(f"  Bookings:  {len(bookings):,}")
print(f"  Users:     {len(users):,}")
print(f"  Providers: {len(providers):,}")
print(f"  Services:  {len(services):,}")

# ============================================================
# SECTION 2: FEATURE ENGINEERING
# ============================================================

bookings['booking_month']   = bookings['booking_date'].dt.to_period('M')
bookings['booking_quarter'] = bookings['booking_date'].dt.to_period('Q')
bookings['booking_year']    = bookings['booking_date'].dt.year

bookings['price_band'] = pd.cut(
    bookings['price_charged'],
    bins=[0, 50, 100, 150, 200, 300, 500, 10000],
    labels=['<$50','$50-99','$100-149',
            '$150-199','$200-299','$300-499','$500+'],
    right=False
)

# Master enriched dataframe
df = (bookings
      .merge(users[['user_id','signup_date','acquisition_channel',
                     'age_group','gender']],
             on='user_id', how='left')
      .merge(services[['service_id','service_name',
                        'category','base_price']],
             on='service_id', how='left')
      .merge(providers[['provider_id','avg_rating',
                          'experience_years','is_active',
                          'service_category']],
             on='provider_id', how='left'))

print(f"\nEnriched dataframe: {df.shape[0]:,} rows x {df.shape[1]} columns")

# ============================================================
# CHART 1: DEMAND VS SUPPLY BY CITY
# ============================================================
print("\nGenerating Chart 1: Demand vs Supply...")

demand = (bookings.groupby('city')
          .agg(total_bookings=('booking_id','count'),
               completed=('status', lambda x: (x=='completed').sum()),
               cancelled=('status', lambda x: (x=='cancelled').sum()))
          .reset_index())

supply = (providers.groupby('city')
          .agg(active_providers=('is_active','sum'))
          .reset_index())

city_df = (demand.merge(supply, on='city')
           .assign(
               ratio       = lambda d: (d.total_bookings /
                                         d.active_providers).round(1),
               cancel_rate = lambda d: (d.cancelled /
                                         d.total_bookings * 100).round(1))
           .sort_values('ratio', ascending=False))

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Demand vs Supply — US Cities', fontsize=15, fontweight='bold')

# Left: grouped bar
x = np.arange(len(city_df))
w = 0.38
axes[0].bar(x - w/2, city_df['total_bookings'],
             width=w, color=BLUE, alpha=0.85, label='Total Bookings')
axes[0].bar(x + w/2, city_df['active_providers'] * 15,
             width=w, color=ORANGE, alpha=0.85,
             label='Active Providers (×15)')
axes[0].set_xticks(x)
axes[0].set_xticklabels(city_df['city'], rotation=35,
                          ha='right', fontsize=8)
axes[0].set_ylabel('Count')
axes[0].set_title('Bookings vs Provider Supply by City')
axes[0].legend(fontsize=9)
axes[0].yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: f'{int(v):,}'))

# Right: ratio bar
colors = [RED if r > 150 else ORANGE if r > 80 else GREEN
           for r in city_df['ratio']]
bars = axes[1].barh(city_df['city'], city_df['ratio'],
                     color=colors, alpha=0.85)
axes[1].axvline(150, color=RED,    linestyle='--',
                 lw=1.5, alpha=0.8, label='Critical (>150)')
axes[1].axvline(80,  color=ORANGE, linestyle='--',
                 lw=1.5, alpha=0.8, label='Warning (>80)')
for bar, ratio in zip(bars, city_df['ratio']):
    axes[1].text(bar.get_width() + 2,
                  bar.get_y() + bar.get_height() / 2,
                  f'{ratio:.0f}x', va='center',
                  fontsize=9, fontweight='bold')
axes[1].set_xlabel('Bookings per Active Provider')
axes[1].set_title('Demand-to-Supply Ratio by City')
axes[1].legend(fontsize=9)

plt.tight_layout()
plt.savefig('visuals/01_demand_supply.png', bbox_inches='tight')
plt.close()
print("  Saved: visuals/01_demand_supply.png")

# ============================================================
# CHART 2: PRICE BAND ANALYSIS
# ============================================================
print("Generating Chart 2: Price Analysis...")

price_summary = (df.groupby('price_band', observed=True)
    .agg(
        total    =('booking_id','count'),
        completed=('status', lambda x: (x=='completed').sum()),
        cancelled=('status', lambda x: (x=='cancelled').sum()),
        revenue  =('price_charged',
                    lambda x: x[df.loc[x.index,'status']
                                =='completed'].sum()))
    .reset_index()
    .assign(cancel_rate=lambda d: d.cancelled / d.total * 100))

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle('Pricing Insights — USD Price Bands',
              fontsize=15, fontweight='bold')

# Completed bookings
axes[0].bar(price_summary['price_band'].astype(str),
             price_summary['completed'],
             color=BLUE, alpha=0.85)
axes[0].set_title('Completed Bookings by Price Band')
axes[0].set_xlabel('Price Band (USD)')
axes[0].set_ylabel('Completed Bookings')
plt.setp(axes[0].xaxis.get_majorticklabels(),
          rotation=30, ha='right')

# Revenue
axes[1].bar(price_summary['price_band'].astype(str),
             price_summary['revenue'] / 1000,
             color=GREEN, alpha=0.85)
axes[1].set_title('Total Revenue by Price Band ($000s)')
axes[1].set_xlabel('Price Band (USD)')
axes[1].set_ylabel('Revenue ($000s)')
plt.setp(axes[1].xaxis.get_majorticklabels(),
          rotation=30, ha='right')

# Cancellation rate
bar_colors = [RED if r > 22 else ORANGE if r > 17 else GREEN
               for r in price_summary['cancel_rate']]
axes[2].bar(price_summary['price_band'].astype(str),
             price_summary['cancel_rate'],
             color=bar_colors, alpha=0.85)
axes[2].axhline(price_summary['cancel_rate'].mean(),
                 color='black', linestyle='--', lw=1.5,
                 label=f"Avg: {price_summary['cancel_rate'].mean():.1f}%")
axes[2].set_title('Cancellation Rate by Price Band')
axes[2].set_xlabel('Price Band (USD)')
axes[2].set_ylabel('Cancellation Rate (%)')
axes[2].legend()
plt.setp(axes[2].xaxis.get_majorticklabels(),
          rotation=30, ha='right')

plt.tight_layout()
plt.savefig('visuals/02_pricing_analysis.png', bbox_inches='tight')
plt.close()
print("  Saved: visuals/02_pricing_analysis.png")

# ============================================================
# CHART 3: COHORT RETENTION HEATMAP
# ============================================================
print("Generating Chart 3: Cohort Retention...")

completed_df = df[df['status'] == 'completed'].copy()
completed_df['cohort_month'] = (
    completed_df.groupby('user_id')['booking_date']
    .transform('min')
    .dt.to_period('M'))
completed_df['booking_period'] = (
    completed_df['booking_date'].dt.to_period('M'))
completed_df['period_number'] = (
    (completed_df['booking_period'].dt.year -
     completed_df['cohort_month'].dt.year) * 12 +
    (completed_df['booking_period'].dt.month -
     completed_df['cohort_month'].dt.month))

cohort_data = (completed_df
    .groupby(['cohort_month','period_number'])['user_id']
    .nunique()
    .reset_index(name='active_users'))

retention_matrix = cohort_data.pivot(
    index='cohort_month',
    columns='period_number',
    values='active_users')

cohort_sizes  = retention_matrix[0]
retention_pct = retention_matrix.divide(cohort_sizes, axis=0) * 100

fig, ax = plt.subplots(figsize=(16, 8))
sns.heatmap(
    retention_pct.iloc[:, :10],
    annot=True, fmt='.0f',
    cmap='RdYlGn',
    linewidths=0.4,
    linecolor='white',
    ax=ax,
    vmin=0, vmax=100,
    cbar_kws={'label': 'Retention Rate (%)'},
    annot_kws={'size': 9})
ax.set_title('Monthly Cohort Retention Matrix — ServeIQ USA',
              fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Months Since First Booking', fontsize=12)
ax.set_ylabel('Customer Cohort Month', fontsize=12)

plt.tight_layout()
plt.savefig('visuals/03_cohort_retention.png', bbox_inches='tight')
plt.close()
print("  Saved: visuals/03_cohort_retention.png")

# ============================================================
# CHART 4: PROVIDER PARETO
# ============================================================
print("Generating Chart 4: Provider Pareto...")

prov_perf = (df[df['status'] == 'completed']
    .groupby('provider_id')
    .agg(total_bookings=('booking_id','count'),
         total_revenue =('price_charged','sum'),
         avg_rating    =('rating_given','mean'))
    .reset_index()
    .dropna(subset=['avg_rating'])
    .sort_values('total_revenue', ascending=False))

prov_perf['cum_revenue_pct'] = (
    prov_perf['total_revenue'].cumsum() /
    prov_perf['total_revenue'].sum() * 100)
prov_perf['provider_pct'] = (
    np.arange(1, len(prov_perf) + 1) /
    len(prov_perf) * 100)

top20_rev = prov_perf[
    prov_perf['provider_pct'] <= 20]['total_revenue'].sum()
top20_pct = top20_rev / prov_perf['total_revenue'].sum() * 100

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Provider Performance Analysis',
              fontsize=15, fontweight='bold')

# Scatter: rating vs bookings
sc = axes[0].scatter(
    prov_perf['avg_rating'],
    prov_perf['total_bookings'],
    c=prov_perf['total_revenue'],
    cmap='YlOrRd', alpha=0.7, s=70,
    edgecolors='white', linewidth=0.5)
plt.colorbar(sc, ax=axes[0], label='Total Revenue ($)')
axes[0].set_xlabel('Average Customer Rating')
axes[0].set_ylabel('Total Completed Bookings')
axes[0].set_title('Provider Rating vs Bookings')
axes[0].axvline(4.0, color=GRAY, linestyle='--',
                 alpha=0.6, label='Rating = 4.0')
axes[0].legend()

# Pareto curve
axes[1].plot(prov_perf['provider_pct'],
              prov_perf['cum_revenue_pct'],
              color=BLUE, linewidth=2.5)
axes[1].fill_between(prov_perf['provider_pct'],
                      prov_perf['cum_revenue_pct'],
                      alpha=0.12, color=BLUE)
axes[1].axvline(20, color=RED,    linestyle='--',
                 lw=1.5, label='Top 20% Providers')
axes[1].axhline(80, color=ORANGE, linestyle='--',
                 lw=1.5, label='80% Revenue Mark')
axes[1].annotate(
    f'Top 20% providers\n→ {top20_pct:.0f}% of revenue',
    xy=(20, top20_pct), xytext=(35, 50),
    arrowprops=dict(arrowstyle='->', color='black'),
    fontsize=10, fontweight='bold')
axes[1].set_xlabel('Cumulative % of Providers')
axes[1].set_ylabel('Cumulative % of Revenue')
axes[1].set_title('Pareto: Provider Revenue Concentration')
axes[1].legend(fontsize=9)
axes[1].set_xlim(0, 100)
axes[1].set_ylim(0, 105)

plt.tight_layout()
plt.savefig('visuals/04_provider_pareto.png', bbox_inches='tight')
plt.close()
print("  Saved: visuals/04_provider_pareto.png")

# ============================================================
# CHART 5: CANCELLATION ANALYSIS
# ============================================================
print("Generating Chart 5: Cancellation Analysis...")

cancelled_df = df[df['status'] == 'cancelled'].copy()

fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.suptitle('Cancellation Analysis — ServeIQ USA',
              fontsize=15, fontweight='bold')

# By city
cancel_city = (cancelled_df.groupby('city')
               .size().reset_index(name='count')
               .sort_values('count', ascending=True))
axes[0,0].barh(cancel_city['city'], cancel_city['count'],
                color=RED, alpha=0.8)
axes[0,0].set_title('Cancellations by City')
axes[0,0].set_xlabel('Number of Cancellations')

# By reason
cancel_reason = (cancelled_df.groupby('cancellation_reason')
                  .size().reset_index(name='count'))
axes[0,1].pie(
    cancel_reason['count'],
    labels=cancel_reason['cancellation_reason'],
    autopct='%1.1f%%', startangle=140,
    colors=[BLUE,ORANGE,RED,GREEN,GRAY])
axes[0,1].set_title('Cancellation Reason Breakdown')

# By service category
cancel_cat = (cancelled_df.groupby('category')
              .size().reset_index(name='count')
              .sort_values('count', ascending=False))
axes[1,0].bar(cancel_cat['category'], cancel_cat['count'],
               color=BLUE, alpha=0.85)
axes[1,0].set_title('Cancellations by Service Category')
axes[1,0].set_ylabel('Count')
plt.setp(axes[1,0].xaxis.get_majorticklabels(),
          rotation=25, ha='right')

# By provider rating bucket
df['rating_bucket'] = pd.cut(
    df['avg_rating'],
    bins=[0, 3.5, 4.0, 4.3, 5.1],
    labels=['<3.5','3.5-3.9','4.0-4.2','4.3-5.0'])
cancel_rating = (df.groupby('rating_bucket', observed=True)
    .apply(lambda x: (x['status']=='cancelled').mean() * 100)
    .reset_index(name='cancel_rate'))
bar_c = [RED if r > 22 else ORANGE if r > 17 else GREEN
          for r in cancel_rating['cancel_rate']]
axes[1,1].bar(cancel_rating['rating_bucket'].astype(str),
               cancel_rating['cancel_rate'],
               color=bar_c, alpha=0.85)
axes[1,1].set_title('Cancellation Rate by Provider Rating')
axes[1,1].set_xlabel('Provider Avg Rating')
axes[1,1].set_ylabel('Cancellation Rate (%)')

plt.tight_layout()
plt.savefig('visuals/05_cancellation_analysis.png',
             bbox_inches='tight')
plt.close()
print("  Saved: visuals/05_cancellation_analysis.png")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 50)
print("  All 5 charts saved to visuals/")
print("=" * 50)
print("\nKey numbers from your dataset:")
print(f"  Total bookings:    {len(bookings):,}")
print(f"  Completion rate:   {(bookings['status']=='completed').mean()*100:.1f}%")
print(f"  Cancellation rate: {(bookings['status']=='cancelled').mean()*100:.1f}%")
print(f"  Total revenue:     ${bookings.loc[bookings['status']=='completed','price_charged'].sum():,.2f}")
print(f"  Cities covered:    {bookings['city'].nunique()}")
print(f"  Active providers:  {providers['is_active'].sum()}")