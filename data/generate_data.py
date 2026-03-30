# ============================================================
# ServeIQ USA — Synthetic Data Generator
# File: data/generate_data.py
# Run: python data/generate_data.py
# ============================================================

import pandas as pd
import numpy as np
import os
import random

# Setting seeds means every run produces IDENTICAL data.
# This matters because your SQL and Python analysis must match.
np.random.seed(42)
random.seed(42)

os.makedirs('data/raw', exist_ok=True)

print("=" * 55)
print("  ServeIQ USA — Data Generation Starting")
print("=" * 55)

# ============================================================
# CONFIGURATION
# ============================================================

# Demand weight = how many bookings come from each city
# Supply weight = how many providers are based in each city
# Austin and Dallas are intentionally undersupplied —
# this creates the business problem we will analyze later

CITY_CONFIG = {
    'New York, NY':      {'demand': 0.22, 'supply': 0.20},
    'Los Angeles, CA':   {'demand': 0.18, 'supply': 0.17},
    'Chicago, IL':       {'demand': 0.13, 'supply': 0.14},
    'Dallas, TX':        {'demand': 0.14, 'supply': 0.08},
    'Austin, TX':        {'demand': 0.12, 'supply': 0.07},
    'San Francisco, CA': {'demand': 0.08, 'supply': 0.10},
    'Seattle, WA':       {'demand': 0.07, 'supply': 0.12},
    'Miami, FL':         {'demand': 0.04, 'supply': 0.06},
    'Denver, CO':        {'demand': 0.01, 'supply': 0.03},
    'Boston, MA':        {'demand': 0.01, 'supply': 0.03},
}

CITIES         = list(CITY_CONFIG.keys())
DEMAND_WEIGHTS = [CITY_CONFIG[c]['demand'] for c in CITIES]
SUPPLY_WEIGHTS = [CITY_CONFIG[c]['supply'] for c in CITIES]

CATEGORIES   = ['Cleaning', 'Plumbing', 'Electrical',
                 'Handyman', 'Moving', 'Lawn Care', 'HVAC', 'Painting']

CHANNELS     = ['Organic Search', 'Paid Search',
                 'Referral', 'Social Media', 'App Store']
CHAN_WEIGHTS = [0.30, 0.28, 0.20, 0.15, 0.07]

CANCEL_REASONS = ['user_request', 'provider_unavailable',
                   'no_show', 'pricing_issue', 'scheduling_conflict']
REASON_WEIGHTS = [0.28, 0.30, 0.18, 0.14, 0.10]

PAYMENTS     = ['Credit Card', 'Debit Card', 'PayPal',
                 'Apple Pay', 'Venmo']
PAY_WEIGHTS  = [0.38, 0.22, 0.18, 0.14, 0.08]

# ============================================================
# TABLE 1: SERVICES
# ============================================================

services_raw = [
    ('SVC001', 'Standard House Cleaning',  'Cleaning',    99.00, 2.5,  79.00,  149.00),
    ('SVC002', 'Deep House Cleaning',      'Cleaning',   149.00, 4.0, 119.00,  199.00),
    ('SVC003', 'Move-Out Cleaning',        'Cleaning',   199.00, 5.0, 169.00,  269.00),
    ('SVC004', 'Office Cleaning',          'Cleaning',   129.00, 3.0,  99.00,  179.00),
    ('SVC005', 'Pipe Repair',              'Plumbing',   149.00, 2.0, 119.00,  229.00),
    ('SVC006', 'Drain Unclogging',         'Plumbing',    89.00, 1.0,  69.00,  139.00),
    ('SVC007', 'Water Heater Install',     'Plumbing',   399.00, 4.0, 329.00,  499.00),
    ('SVC008', 'Outlet Installation',      'Electrical', 119.00, 1.5,  89.00,  169.00),
    ('SVC009', 'Breaker Box Repair',       'Electrical', 249.00, 3.0, 199.00,  349.00),
    ('SVC010', 'Ceiling Fan Install',      'Electrical',  99.00, 1.5,  79.00,  139.00),
    ('SVC011', 'Furniture Assembly',       'Handyman',    79.00, 2.0,  59.00,  129.00),
    ('SVC012', 'TV Mounting',              'Handyman',    89.00, 1.0,  69.00,  119.00),
    ('SVC013', 'Drywall Repair',           'Handyman',   149.00, 3.0, 119.00,  229.00),
    ('SVC014', 'Local Moving (2 Movers)',  'Moving',     299.00, 4.0, 249.00,  399.00),
    ('SVC015', 'Long-Distance Moving',     'Moving',     799.00, 8.0, 649.00,  999.00),
    ('SVC016', 'Lawn Mowing',              'Lawn Care',   59.00, 1.5,  45.00,   89.00),
    ('SVC017', 'Full Lawn Service',        'Lawn Care',  129.00, 3.0,  99.00,  179.00),
    ('SVC018', 'AC Tune-Up',              'HVAC',        129.00, 2.0,  99.00,  179.00),
    ('SVC019', 'HVAC Installation',       'HVAC',        899.00, 6.0, 749.00, 1099.00),
    ('SVC020', 'Interior Room Painting',  'Painting',    299.00, 6.0, 249.00,  399.00),
]

services = pd.DataFrame(
    services_raw,
    columns=['service_id', 'service_name', 'category', 'base_price',
             'duration_hours', 'min_price', 'max_price']
)

POPULAR_SVCS = {'SVC001','SVC002','SVC005','SVC008','SVC010',
                 'SVC011','SVC012','SVC014','SVC016','SVC018'}
services['is_popular'] = services['service_id'].isin(POPULAR_SVCS)

services.to_csv('data/raw/services.csv', index=False)
print(f"\n✓ services.csv       — {len(services):>6,} rows")

# ============================================================
# TABLE 2: USERS
# ============================================================

N_USERS = 600

users = pd.DataFrame({
    'user_id': [f'USR{str(i).zfill(5)}' for i in range(1, N_USERS + 1)],
    'city': np.random.choice(CITIES, N_USERS, p=DEMAND_WEIGHTS),
    'signup_date': (
        pd.Timestamp('2023-01-01') +
        pd.to_timedelta(np.random.randint(0, 548, N_USERS), unit='D')
    ),
    'age_group': np.random.choice(
        ['18-25', '26-35', '36-45', '46-55', '55+'],
        N_USERS, p=[0.12, 0.38, 0.28, 0.14, 0.08]
    ),
    'gender': np.random.choice(
        ['Female', 'Male', 'Non-binary/Other'],
        N_USERS, p=[0.54, 0.44, 0.02]
    ),
    'acquisition_channel': np.random.choice(
        CHANNELS, N_USERS, p=CHAN_WEIGHTS
    ),
    'zip_code': [str(np.random.randint(10000, 99999)) for _ in range(N_USERS)],
})

users.to_csv('data/raw/users.csv', index=False)
print(f"✓ users.csv          — {len(users):>6,} rows")

# ============================================================
# TABLE 3: PROVIDERS
# ============================================================

N_PROVIDERS = 160

providers = pd.DataFrame({
    'provider_id': [f'PRV{str(i).zfill(5)}' for i in range(1, N_PROVIDERS + 1)],
    'city': np.random.choice(CITIES, N_PROVIDERS, p=SUPPLY_WEIGHTS),
    'join_date': (
        pd.Timestamp('2022-06-01') +
        pd.to_timedelta(np.random.randint(0, 610, N_PROVIDERS), unit='D')
    ),
    'service_category': np.random.choice(CATEGORIES, N_PROVIDERS),
    'avg_rating': np.clip(
        np.random.normal(4.2, 0.45, N_PROVIDERS), 1.0, 5.0
    ).round(1),
    'total_jobs_completed': np.random.randint(10, 600, N_PROVIDERS),
    'is_active': np.random.choice(
        [True, False], N_PROVIDERS, p=[0.80, 0.20]
    ),
    'experience_years': np.random.randint(1, 20, N_PROVIDERS),
    'background_check_passed': np.random.choice(
        [True, False], N_PROVIDERS, p=[0.94, 0.06]
    ),
})

providers.to_csv('data/raw/providers.csv', index=False)
print(f"✓ providers.csv      — {len(providers):>6,} rows")

# ============================================================
# TABLE 4: BOOKINGS
# ============================================================

N_BOOKINGS = 12000

def generate_bookings(n, users_df, providers_df, services_df):

    rows = []
    user_booking_count = {}

    users_list    = users_df.to_dict('records')
    services_list = services_df.to_dict('records')

    city_providers = {}
    for p in providers_df.to_dict('records'):
        city_providers.setdefault(p['city'], []).append(p)

    active_by_city = {
        city: [p for p in provs if p['is_active']]
        for city, provs in city_providers.items()
    }
    all_providers = providers_df.to_dict('records')

    for i in range(n):

        user = random.choice(users_list)
        uid  = user['user_id']

        local_active = active_by_city.get(user['city'], [])
        if local_active and random.random() < 0.72:
            provider = random.choice(local_active)
        else:
            provider = random.choice(all_providers)

        service = random.choice(services_list)

        booking_date = (
            pd.Timestamp('2023-01-01') +
            pd.Timedelta(days=int(np.random.randint(0, 548)))
        )
        days_ahead   = int(np.random.randint(1, 10))
        service_date = booking_date + pd.Timedelta(days=days_ahead)

        raw_price     = service['base_price'] * np.random.uniform(0.82, 1.22)
        price         = round(raw_price / 5) * 5
        price         = max(price, service['min_price'])

        discount = float(np.random.choice(
            [0, 5, 10, 15, 20, 25, 30],
            p=[0.55, 0.10, 0.12, 0.10, 0.07, 0.04, 0.02]
        ))
        price_charged = max(round(price - discount, 2), service['min_price'])

        cancel_prob = 0.14

        if price_charged > 400:             cancel_prob += 0.09
        elif price_charged > 200:           cancel_prob += 0.04
        if provider['avg_rating'] < 3.5:    cancel_prob += 0.08
        elif provider['avg_rating'] < 4.0:  cancel_prob += 0.03
        if user['city'] in ('Austin, TX', 'Dallas, TX'):
                                            cancel_prob += 0.05
        if days_ahead >= 7:                 cancel_prob += 0.03
        if service['category'] == 'Moving': cancel_prob += 0.04

        cancel_prob = min(cancel_prob, 0.55)

        status = np.random.choice(
            ['completed', 'cancelled'],
            p=[1 - cancel_prob, cancel_prob]
        )

        cancel_reason = None
        rating        = None

        if status == 'cancelled':
            cancel_reason = np.random.choice(CANCEL_REASONS, p=REASON_WEIGHTS)
        else:
            rating = round(
                float(np.clip(np.random.normal(4.15, 0.65), 1.0, 5.0)), 1
            )

        is_repeat = user_booking_count.get(uid, 0) > 0
        user_booking_count[uid] = user_booking_count.get(uid, 0) + 1

        rows.append({
            'booking_id':          f'BKG{str(i + 1).zfill(6)}',
            'user_id':             uid,
            'provider_id':         provider['provider_id'],
            'service_id':          service['service_id'],
            'city':                user['city'],
            'booking_date':        booking_date.date(),
            'service_date':        service_date.date(),
            'status':              status,
            'price_charged':       price_charged,
            'discount_applied':    discount,
            'payment_method':      np.random.choice(PAYMENTS, p=PAY_WEIGHTS),
            'cancellation_reason': cancel_reason,
            'rating_given':        rating,
            'is_repeat_booking':   is_repeat,
            'days_to_service':     days_ahead,
        })

    return pd.DataFrame(rows)


print("\nGenerating 12,000 bookings — this takes about 15 seconds...")
bookings = generate_bookings(N_BOOKINGS, users, providers, services)
bookings.to_csv('data/raw/bookings.csv', index=False)

completed = (bookings['status'] == 'completed').sum()
cancelled = (bookings['status'] == 'cancelled').sum()
repeats   = bookings['is_repeat_booking'].sum()
total_rev = bookings.loc[
    bookings['status'] == 'completed', 'price_charged'].sum()

print(f"✓ bookings.csv       — {len(bookings):>6,} rows")
print()
print("── Booking Summary ──────────────────────────────────")
print(f"  Completed:       {completed:>6,}  ({completed/N_BOOKINGS*100:.1f}%)")
print(f"  Cancelled:       {cancelled:>6,}  ({cancelled/N_BOOKINGS*100:.1f}%)")
print(f"  Repeat bookings: {repeats:>6,}  ({repeats/N_BOOKINGS*100:.1f}%)")
print(f"  Total Revenue:   ${total_rev:>12,.2f}")
print()
print("── City Distribution (Bookings) ─────────────────────")
city_counts = bookings['city'].value_counts()
for city, count in city_counts.items():
    bar = '█' * (count // 80)
    print(f"  {city:<22} {count:>5,}  {bar}")
print()
print("=" * 55)
print("  All 4 tables saved to data/raw/")
print("  Next step: load into PostgreSQL")
print("=" * 55)
