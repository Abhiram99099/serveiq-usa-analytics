-- ============================================================
-- QUERY 5: Provider Performance Ranking
-- Business Question: Which providers drive the most value
--                    and who are the risks?
-- File: sql/05_provider_performance.sql
-- ============================================================

WITH provider_stats AS (
    SELECT
        b.provider_id,
        p.city,
        p.service_category,
        p.avg_rating,
        p.experience_years,
        COUNT(*)                                                AS total_assigned,
        COUNT(CASE WHEN b.status = 'completed' THEN 1 END)     AS completed,
        COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END)     AS cancelled,
        ROUND(SUM(CASE WHEN b.status = 'completed'
              THEN b.price_charged ELSE 0 END), 2)             AS total_revenue,
        ROUND(AVG(CASE WHEN b.rating_given IS NOT NULL
              THEN b.rating_given END), 2)                     AS avg_customer_rating,
        ROUND(COUNT(CASE WHEN b.status = 'cancelled'
              THEN 1 END)::NUMERIC /
              NULLIF(COUNT(*), 0) * 100, 1)                    AS cancel_rate_pct
    FROM bookings b
    JOIN providers p ON b.provider_id = p.provider_id
    GROUP BY b.provider_id, p.city, p.service_category,
             p.avg_rating, p.experience_years
)
SELECT
    provider_id,
    city,
    service_category,
    avg_rating,
    completed,
    total_revenue,
    avg_customer_rating,
    cancel_rate_pct,
    NTILE(4) OVER (ORDER BY completed DESC)                    AS volume_quartile,
    RANK() OVER (PARTITION BY city
                 ORDER BY total_revenue DESC)                  AS city_revenue_rank,
    CASE NTILE(4) OVER (ORDER BY completed DESC)
        WHEN 1 THEN 'Top Performer'
        WHEN 2 THEN 'Above Average'
        WHEN 3 THEN 'Below Average'
        ELSE        'Low Performer'
    END                                                        AS performance_tier
FROM provider_stats
ORDER BY total_revenue DESC
LIMIT 15;

-- KEY FINDINGS:
-- Dallas providers dominate top 15 due to supply shortage
-- PRV00122: Rating 3.0 but Top Performer by volume -- quality risk
-- Provider unavailability drives most cancellations platform-wide
-- RECOMMENDATION: Minimum rating threshold of 3.5 for active status