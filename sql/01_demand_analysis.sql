-- ============================================================
-- DEMAND ANALYSIS
-- Business question: When and where is demand concentrated?
-- ============================================================
USE nyc_taxi;

-- 1. Trips by hour of day
SELECT
    pickup_hour,
    COUNT(*) AS trip_count,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;

-- 2. Trips by day of week (1=Sunday ... 7=Saturday)
SELECT
    pickup_dow,
    CASE pickup_dow
        WHEN 1 THEN 'Sunday' WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday'
        WHEN 7 THEN 'Saturday'
    END AS day_name,
    COUNT(*) AS trip_count,
    ROUND(AVG(total_amount), 2) AS avg_fare
FROM trips
GROUP BY pickup_dow
ORDER BY pickup_dow;

-- 3. Trips by month (seasonality)
SELECT
    pickup_month,
    COUNT(*) AS trip_count,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM trips
GROUP BY pickup_month
ORDER BY pickup_month;

-- 4. Peak vs off-peak demand
-- Peak defined as weekday AM rush (7-9) and PM rush (16-19); everything else off-peak
SELECT
    CASE
        WHEN pickup_dow BETWEEN 2 AND 6 AND pickup_hour BETWEEN 7 AND 9  THEN 'AM Peak'
        WHEN pickup_dow BETWEEN 2 AND 6 AND pickup_hour BETWEEN 16 AND 19 THEN 'PM Peak'
        ELSE 'Off-Peak'
    END AS demand_period,
    COUNT(*) AS trip_count,
    ROUND(AVG(total_amount), 2) AS avg_fare,
    ROUND(AVG(trip_duration_min), 2) AS avg_duration_min
FROM trips
GROUP BY demand_period
ORDER BY trip_count DESC;

-- 5. Pickup hotspots (top 15 zones by trip volume)
SELECT
    z.borough,
    z.zone,
    COUNT(*) AS pickup_trips,
    ROUND(SUM(t.total_amount), 2) AS total_revenue
FROM trips t
JOIN taxi_zones z ON t.pu_location_id = z.location_id
GROUP BY z.borough, z.zone
ORDER BY pickup_trips DESC
LIMIT 15;

-- 6. Drop-off hotspots (top 15 zones by trip volume)
SELECT
    z.borough,
    z.zone,
    COUNT(*) AS dropoff_trips,
    ROUND(SUM(t.total_amount), 2) AS total_revenue
FROM trips t
JOIN taxi_zones z ON t.do_location_id = z.location_id
GROUP BY z.borough, z.zone
ORDER BY dropoff_trips DESC
LIMIT 15;

-- 7. Demand concentration by borough (pickup) with ranking
SELECT
    z.borough,
    COUNT(*) AS trip_count,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS demand_rank
FROM trips t
JOIN taxi_zones z ON t.pu_location_id = z.location_id
GROUP BY z.borough
ORDER BY demand_rank;

-- 8. Seasonal pattern: month x demand-period heatmap source
SELECT
    pickup_month,
    pickup_hour,
    COUNT(*) AS trip_count
FROM trips
GROUP BY pickup_month, pickup_hour
ORDER BY pickup_month, pickup_hour;
