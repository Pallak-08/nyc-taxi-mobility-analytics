-- ============================================================
-- OPERATIONAL EFFICIENCY
-- Framed around fleet utilization patterns visible in trip data
-- (pickup concentration, duration, distance, demand timing).
-- Note: this dataset has no vehicle-supply/availability data, so we
-- describe *demand-side* utilization signals, not actual shortages.
-- ============================================================
USE nyc_taxi;

-- 1. Pickup concentration: share of trips from top 10 zones vs rest
WITH zone_counts AS (
    SELECT pu_location_id, COUNT(*) AS trip_count
    FROM trips
    GROUP BY pu_location_id
),
ranked AS (
    SELECT *, RANK() OVER (ORDER BY trip_count DESC) AS rnk
    FROM zone_counts
)
SELECT
    CASE WHEN rnk <= 10 THEN 'Top 10 zones' ELSE 'All other zones' END AS zone_group,
    SUM(trip_count) AS trip_count,
    ROUND(100 * SUM(trip_count) / SUM(SUM(trip_count)) OVER (), 2) AS pct_of_total
FROM ranked
GROUP BY zone_group;

-- 2. Average trip duration and distance by hour (fleet cycle time proxy)
SELECT
    pickup_hour,
    COUNT(*) AS trip_count,
    ROUND(AVG(trip_duration_min), 2) AS avg_duration_min,
    ROUND(AVG(trip_distance), 2) AS avg_distance
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;

-- 3. High-demand vs low-demand periods (by trip volume decile across hour-of-week)
WITH hourly AS (
    SELECT pickup_dow, pickup_hour, COUNT(*) AS trip_count
    FROM trips
    GROUP BY pickup_dow, pickup_hour
)
SELECT
    pickup_dow, pickup_hour, trip_count,
    NTILE(5) OVER (ORDER BY trip_count) AS demand_quintile   -- 1=lowest demand, 5=highest
FROM hourly
ORDER BY demand_quintile, pickup_dow, pickup_hour;

-- 4. Imbalance between pickups and dropoffs by zone
--    (positive net = more trips end there than start there -> potential
--     accumulation point; negative = zone drains faster than it fills)
WITH pu AS (
    SELECT pu_location_id AS location_id, COUNT(*) AS pickups FROM trips GROUP BY pu_location_id
),
do AS (
    SELECT do_location_id AS location_id, COUNT(*) AS dropoffs FROM trips GROUP BY do_location_id
)
SELECT
    z.borough, z.zone,
    COALESCE(pu.pickups, 0) AS pickups,
    COALESCE(do.dropoffs, 0) AS dropoffs,
    COALESCE(do.dropoffs, 0) - COALESCE(pu.pickups, 0) AS net_imbalance
FROM taxi_zones z
LEFT JOIN pu ON pu.location_id = z.location_id
LEFT JOIN do ON do.location_id = z.location_id
WHERE COALESCE(pu.pickups,0) + COALESCE(do.dropoffs,0) > 0
ORDER BY net_imbalance DESC
LIMIT 20;

-- 5. Low-demand time windows worth flagging for fleet reallocation
SELECT
    pickup_dow, pickup_hour,
    COUNT(*) AS trip_count,
    ROUND(AVG(total_amount), 2) AS avg_fare
FROM trips
GROUP BY pickup_dow, pickup_hour
ORDER BY trip_count ASC
LIMIT 20;
