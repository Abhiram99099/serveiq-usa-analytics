-- ============================================================
-- QUERY 3: Customer Segmentation by Repeat Usage
-- Business Question: How many customers return and what
--                    is their value vs one-time customers?
-- File: sql/03_repeat_customers.sql
-- ============================================================

WITH user_stats AS (
    SELECT
        user_id,
        COUNT(*)           AS total_bookings,
        SUM(price_charged) AS lifetime_value
    FROM bookings
    WHERE status = 'completed'
    GROUP BY user_id
),
segmented AS (
    SELECT
        user_id,
        total_bookings,
        lifetime_value,
        CASE
            WHEN total_bookings = 1  THEN '1. One-Time'
            WHEN total_bookings <= 4 THEN '2. Occasional (2-4)'
            WHEN total_bookings <= 9 THEN '3. Regular (5-9)'
            ELSE                          '4. Power User (10+)'
        END AS customer_segment
    FROM user_stats
)
SELECT
    customer_segment,
    COUNT(*)                                                   AS user_count,
    ROUND(COUNT(*)::NUMERIC /
          SUM(COUNT(*)) OVER () * 100, 1)                      AS pct_of_users,
    ROUND(AVG(total_bookings), 1)                              AS avg_bookings,
    ROUND(AVG(lifetime_value), 2)                              AS avg_lifetime_value,
    ROUND(SUM(lifetime_value), 2)                              AS segment_revenue,
    ROUND(SUM(lifetime_value) /
          SUM(SUM(lifetime_value)) OVER () * 100, 1)           AS pct_of_revenue
FROM segmented
GROUP BY customer_segment
ORDER BY customer_segment;

-- NOTE: Dataset has 600 users across 12,000 bookings (avg 20/user)
-- In production this would show more one-time vs repeat split
-- Key insight: Power User avg LTV = $3,655 vs platform avg