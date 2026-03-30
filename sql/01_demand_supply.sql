-- ============================================================
-- QUERY 1: Demand vs Supply Analysis by US City
-- Business Question: Which cities are most undersupplied?
-- File: sql/01_demand_supply.sql
-- ============================================================

SELECT
    d.city,
    d.total_bookings,
    d.completed,
    d.cancelled,
    s.active_providers,
    ROUND(d.total_bookings::NUMERIC /
          NULLIF(s.active_providers, 0), 1)        AS demand_supply_ratio,
    ROUND(d.cancelled::NUMERIC /
          NULLIF(d.total_bookings, 0) * 100, 1)    AS cancel_rate_pct
FROM (
    SELECT
        city,
        COUNT(*)                                            AS total_bookings,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)   AS completed,
        COUNT(CASE WHEN status = 'cancelled' THEN 1 END)   AS cancelled
    FROM bookings
    GROUP BY city
) d
JOIN (
    SELECT
        city,
        COUNT(CASE WHEN is_active = TRUE THEN 1 END)       AS active_providers
    FROM providers
    GROUP BY city
) s ON d.city = s.city
ORDER BY demand_supply_ratio DESC;

-- KEY FINDINGS:
-- Dallas, TX:   238.6x ratio — CRITICAL (only 7 active providers)
-- Austin, TX:    99.7x ratio — WARNING  (only 13 active providers)
-- Both TX cities show 23.3% cancellation rate vs 17% platform average
-- RECOMMENDATION: Urgent provider recruitment in Dallas and Austin