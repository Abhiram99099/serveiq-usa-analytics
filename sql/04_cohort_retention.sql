-- ============================================================
-- QUERY 4: Monthly Cohort Retention Matrix
-- Business Question: What percentage of each signup cohort
--                    is still active in subsequent months?
-- File: sql/04_cohort_retention.sql
-- ============================================================

WITH first_booking AS (
    SELECT
        user_id,
        DATE_TRUNC('month', MIN(booking_date))    AS cohort_month
    FROM bookings
    WHERE status = 'completed'
    GROUP BY user_id
),
user_activity AS (
    SELECT
        b.user_id,
        f.cohort_month,
        DATE_TRUNC('month', b.booking_date)       AS activity_month,
        EXTRACT(YEAR FROM AGE(
            DATE_TRUNC('month', b.booking_date),
            f.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(
            DATE_TRUNC('month', b.booking_date),
            f.cohort_month))                      AS period_number
    FROM bookings b
    JOIN first_booking f ON b.user_id = f.user_id
    WHERE b.status = 'completed'
),
cohort_counts AS (
    SELECT
        cohort_month,
        period_number,
        COUNT(DISTINCT user_id)                   AS active_users
    FROM user_activity
    GROUP BY cohort_month, period_number
),
cohort_sizes AS (
    SELECT cohort_month, active_users             AS cohort_size
    FROM cohort_counts
    WHERE period_number = 0
)
SELECT
    TO_CHAR(cc.cohort_month, 'YYYY-MM')           AS cohort,
    cs.cohort_size,
    cc.period_number                              AS month_number,
    cc.active_users,
    ROUND(cc.active_users::NUMERIC /
          cs.cohort_size * 100, 1)                AS retention_pct
FROM cohort_counts cc
JOIN cohort_sizes cs ON cc.cohort_month = cs.cohort_month
WHERE cc.period_number <= 6
ORDER BY cc.cohort_month, cc.period_number;

-- KEY FINDINGS:
-- Platform retains 54-65% of customers through Month 6
-- Retention INCREASES after Month 1 -- habitual usage pattern
-- January cohort largest (365 users) -- strong new year demand
-- This is exceptionally strong retention for a services marketplace