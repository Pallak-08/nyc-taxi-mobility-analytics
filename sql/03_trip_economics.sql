-- ============================================================
-- TRIP ECONOMICS
-- Business question: What trip characteristics are associated
-- with stronger revenue efficiency?
-- ============================================================
USE nyc_taxi;

-- 1. Short vs long trip segmentation
SELECT
    CASE
        WHEN trip_distance < 1  THEN '< 1 mi'
        WHEN trip_distance < 3  THEN '1-3 mi'
        WHEN trip_distance < 6  THEN '3-6 mi'
        WHEN trip_distance < 10 THEN '6-10 mi'
        ELSE '10+ mi'
    END AS distance_band,
    COUNT(*) AS trip_count,
    ROUND(AVG(total_amount), 2) AS avg_fare,
    ROUND(AVG(total_amount) / NULLIF(AVG(trip_distance), 0), 2) AS revenue_per_mile,
    ROUND(AVG(total_amount) / NULLIF(AVG(trip_duration_min), 0), 2) AS revenue_per_minute,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct
FROM trips
WHERE trip_distance > 0 AND trip_duration_min > 0
GROUP BY distance_band
ORDER BY MIN(trip_distance);

-- 2. Revenue per mile and per minute by hour (efficiency across the day)
SELECT
    pickup_hour,
    ROUND(AVG(trip_distance), 2) AS avg_distance,
    ROUND(AVG(trip_duration_min), 2) AS avg_duration_min,
    ROUND(SUM(total_amount) / NULLIF(SUM(trip_distance), 0), 2) AS revenue_per_mile,
    ROUND(SUM(total_amount) / NULLIF(SUM(trip_duration_min), 0), 2) AS revenue_per_minute
FROM trips
WHERE trip_distance > 0 AND trip_duration_min > 0
GROUP BY pickup_hour
ORDER BY pickup_hour;

-- 3. Average fare by distance decile (finer-grained relationship)
WITH ranked AS (
    SELECT trip_distance, total_amount,
           NTILE(10) OVER (ORDER BY trip_distance) AS distance_decile
    FROM trips
    WHERE trip_distance > 0 AND trip_distance < 50
)
SELECT
    distance_decile,
    ROUND(MIN(trip_distance), 2) AS min_dist,
    ROUND(MAX(trip_distance), 2) AS max_dist,
    ROUND(AVG(total_amount), 2) AS avg_fare
FROM ranked
GROUP BY distance_decile
ORDER BY distance_decile;

-- 4. Tip percentage by trip distance band and payment type
SELECT
    CASE
        WHEN trip_distance < 1  THEN '< 1 mi'
        WHEN trip_distance < 3  THEN '1-3 mi'
        WHEN trip_distance < 6  THEN '3-6 mi'
        WHEN trip_distance < 10 THEN '6-10 mi'
        ELSE '10+ mi'
    END AS distance_band,
    payment_type,
    COUNT(*) AS trip_count,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct
FROM trips
WHERE trip_distance > 0
GROUP BY distance_band, payment_type
ORDER BY distance_band, payment_type;

-- 5. Trip duration vs distance efficiency (identify slow, low-revenue trips
--    e.g. long duration relative to distance -> traffic-bound / low $/min)
SELECT
    CASE
        WHEN trip_duration_min <= 0 OR trip_distance <= 0 THEN 'invalid'
        WHEN (trip_distance / trip_duration_min) < 0.15 THEN 'slow (<9mph avg)'
        WHEN (trip_distance / trip_duration_min) < 0.35 THEN 'moderate (9-21mph avg)'
        ELSE 'fast (21mph+ avg)'
    END AS speed_band,
    COUNT(*) AS trip_count,
    ROUND(AVG(total_amount), 2) AS avg_fare,
    ROUND(AVG(total_amount) / NULLIF(AVG(trip_duration_min), 0), 2) AS revenue_per_minute
FROM trips
WHERE trip_distance > 0 AND trip_duration_min > 0
GROUP BY speed_band
ORDER BY revenue_per_minute DESC;
