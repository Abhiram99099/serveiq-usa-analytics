-- ============================================================
-- QUERY 2: Price Band Analysis
-- Business Question: What price ranges drive bookings
--                    and where do cancellations spike?
-- File: sql/02_price_analysis.sql
-- ============================================================

SELECT
    CASE
        WHEN price_charged <  50  THEN '1. Under $50'
        WHEN price_charged <  100 THEN '2. $50-$99'
        WHEN price_charged <  150 THEN '3. $100-$149'
        WHEN price_charged <  200 THEN '4. $150-$199'
        WHEN price_charged <  300 THEN '5. $200-$299'
        WHEN price_charged <  500 THEN '6. $300-$499'
        ELSE                           '7. $500+'
    END                                                          AS price_band,
    COUNT(*)                                                     AS total_bookings,
    COUNT(CASE WHEN status = 'completed' THEN 1 END)             AS completed,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END)             AS cancelled,
    ROUND(COUNT(CASE WHEN status = 'cancelled' THEN 1 END)
          ::NUMERIC / COUNT(*) * 100, 1)                         AS cancel_rate_pct,
    ROUND(AVG(CASE WHEN status = 'completed'
              THEN price_charged END), 2)                        AS avg_price,
    ROUND(SUM(CASE WHEN status = 'completed'
              THEN price_charged ELSE 0 END), 2)                 AS total_revenue
FROM bookings
GROUP BY price_band
ORDER BY price_band;

-- KEY FINDINGS:
-- $100-$149: highest volume (3,794 bookings), cancel rate 17.3%
-- $150-$199: lowest cancel rate (15.3%) — most committed customers
-- $200+: cancellation jumps to 23%+ — 8pp above sweet spot
-- $500+: highest revenue ($771K) but 1 in 4 bookings cancels
-- RECOMMENDATION: $25 deposit required for bookings above $200