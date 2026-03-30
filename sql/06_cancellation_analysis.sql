-- ============================================================
-- QUERY 6: Cancellation Root Cause Analysis
-- Business Question: Where is revenue leaking and why?
-- File: sql/06_cancellation_analysis.sql
-- ============================================================

SELECT
    b.city,
    s.category                                    AS service_category,
    b.cancellation_reason,
    CASE
        WHEN b.price_charged <  100 THEN 'Budget (<$100)'
        WHEN b.price_charged <  200 THEN 'Mid ($100-$199)'
        WHEN b.price_charged <  400 THEN 'Premium ($200-$399)'
        ELSE                             'High-End ($400+)'
    END                                           AS price_tier,
    CASE
        WHEN p.avg_rating >= 4.5 THEN 'Excellent (4.5+)'
        WHEN p.avg_rating >= 4.0 THEN 'Good (4.0-4.4)'
        WHEN p.avg_rating >= 3.5 THEN 'Average (3.5-3.9)'
        ELSE                          'Poor (<3.5)'
    END                                           AS provider_quality,
    COUNT(*)                                      AS cancellations,
    ROUND(AVG(b.price_charged), 2)                AS avg_cancelled_price,
    ROUND(COUNT(*)::NUMERIC /
          SUM(COUNT(*)) OVER () * 100, 2)         AS pct_of_all_cancellations
FROM bookings b
JOIN services s  ON b.service_id  = s.service_id
JOIN providers p ON b.provider_id = p.provider_id
WHERE b.status = 'cancelled'
GROUP BY
    b.city, s.category, b.cancellation_reason,
    price_tier, provider_quality
ORDER BY cancellations DESC
LIMIT 20;

-- KEY FINDINGS:
-- Provider unavailability is #1 cancellation driver across all cities
-- Cleaning + Mid price ($100-$199) is most cancelled combination
-- Good-rated providers still show availability cancellations
-- RECOMMENDATION: 90-minute provider confirmation window with
--                 auto-reassignment if not accepted