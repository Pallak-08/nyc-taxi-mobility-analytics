-- ============================================================
-- REVENUE ANALYSIS
-- Business question: Which periods and locations generate the
-- strongest revenue?
-- ============================================================
USE nyc_taxi;

-- 1. Total fare revenue (overall summary)
SELECT
    COUNT(*) AS total_trips,
    ROUND(SUM(fare_amount), 2) AS total_fare_revenue,
    ROUND(SUM(tip_amount), 2) AS total_tip_revenue,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_fare_per_trip
FROM trips;

-- 2. Revenue by month
SELECT
    pickup_month,
    COUNT(*) AS trip_count,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(SUM(total_amount) / COUNT(*), 2) AS revenue_per_trip
FROM trips
GROUP BY pickup_month
ORDER BY pickup_month;

-- 3. Revenue by hour of day
SELECT
    pickup_hour,
    COUNT(*) AS trip_count,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(SUM(total_amount) / NULLIF(SUM(trip_duration_min), 0) * 60, 2) AS revenue_per_hour_driven
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;

-- 4. Revenue by pickup location (top 20 by total revenue)
SELECT
    z.borough,
    z.zone,
    COUNT(*) AS trip_count,
    ROUND(SUM(t.total_amount), 2) AS revenue,
    ROUND(AVG(t.total_amount), 2) AS avg_fare
FROM trips t
JOIN taxi_zones z ON t.pu_location_id = z.location_id
GROUP BY z.borough, z.zone
ORDER BY revenue DESC
LIMIT 20;

-- 5. Revenue per mile and per minute, overall and by service type
SELECT
    service_type,
    ROUND(SUM(total_amount) / NULLIF(SUM(trip_distance), 0), 2) AS revenue_per_mile,
    ROUND(SUM(total_amount) / NULLIF(SUM(trip_duration_min), 0), 2) AS revenue_per_minute,
    ROUND(AVG(total_amount), 2) AS avg_fare
FROM trips
WHERE trip_distance > 0 AND trip_duration_min > 0
GROUP BY service_type;

-- 6. Average fare and revenue efficiency by demand period
SELECT
    CASE
        WHEN pickup_dow BETWEEN 2 AND 6 AND pickup_hour BETWEEN 7 AND 9  THEN 'AM Peak'
        WHEN pickup_dow BETWEEN 2 AND 6 AND pickup_hour BETWEEN 16 AND 19 THEN 'PM Peak'
        ELSE 'Off-Peak'
    END AS demand_period,
    ROUND(AVG(total_amount), 2) AS avg_fare,
    ROUND(SUM(total_amount) / NULLIF(SUM(trip_distance), 0), 2) AS revenue_per_mile
FROM trips
WHERE trip_distance > 0
GROUP BY demand_period;

-- 7. Tip revenue: total, average, and tip % by payment type
SELECT
    payment_type,
    CASE payment_type
        WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash' WHEN 3 THEN 'No charge'
        WHEN 4 THEN 'Dispute' WHEN 5 THEN 'Unknown' WHEN 6 THEN 'Voided trip'
        ELSE 'Other'
    END AS payment_label,
    COUNT(*) AS trip_count,
    ROUND(SUM(tip_amount), 2) AS total_tips,
    ROUND(AVG(tip_amount), 2) AS avg_tip,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct
FROM trips
GROUP BY payment_type
ORDER BY total_tips DESC;

-- 8. Top 3 revenue-generating pickup zones within each borough
SELECT * FROM (
    SELECT
        z.borough,
        z.zone,
        SUM(t.total_amount) AS revenue,
        COUNT(*) AS trip_count,
        RANK() OVER (PARTITION BY z.borough ORDER BY SUM(t.total_amount) DESC) AS rank_in_borough
    FROM trips t
    JOIN taxi_zones z ON t.pu_location_id = z.location_id
    GROUP BY z.borough, z.zone
) ranked
WHERE rank_in_borough <= 3
ORDER BY borough, rank_in_borough;
