-- ============================================================
-- PASSENGER / PAYMENT BEHAVIOR
-- Business questions:
--   Which payment methods are associated with higher tips?
--   How does passenger count relate to fare/trip characteristics?
-- ============================================================
USE nyc_taxi;

-- 1. Payment type distribution and average fare/tip
SELECT
    payment_type,
    CASE payment_type
        WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash' WHEN 3 THEN 'No charge'
        WHEN 4 THEN 'Dispute' WHEN 5 THEN 'Unknown' WHEN 6 THEN 'Voided trip'
        ELSE 'Other'
    END AS payment_label,
    COUNT(*) AS trip_count,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_trips,
    ROUND(AVG(fare_amount), 2) AS avg_fare,
    ROUND(AVG(tip_amount), 2) AS avg_tip,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct
FROM trips
GROUP BY payment_type
ORDER BY trip_count DESC;

-- 2. Passenger count distribution
SELECT
    passenger_count,
    COUNT(*) AS trip_count,
    ROUND(AVG(fare_amount), 2) AS avg_fare,
    ROUND(AVG(trip_distance), 2) AS avg_distance,
    ROUND(AVG(tip_amount), 2) AS avg_tip
FROM trips
WHERE passenger_count IS NOT NULL AND passenger_count BETWEEN 0 AND 9
GROUP BY passenger_count
ORDER BY passenger_count;

-- 3. Passenger count vs fare/trip characteristics (solo vs group rides)
SELECT
    CASE
        WHEN passenger_count = 1 THEN 'Solo (1)'
        WHEN passenger_count BETWEEN 2 AND 3 THEN 'Small group (2-3)'
        WHEN passenger_count >= 4 THEN 'Large group (4+)'
        ELSE 'Unknown'
    END AS group_size,
    COUNT(*) AS trip_count,
    ROUND(AVG(fare_amount), 2) AS avg_fare,
    ROUND(AVG(trip_distance), 2) AS avg_distance,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct
FROM trips
WHERE passenger_count IS NOT NULL
GROUP BY group_size
ORDER BY trip_count DESC;

-- 4. Tip behavior by service type (yellow vs green)
SELECT
    service_type,
    COUNT(*) AS trip_count,
    ROUND(AVG(tip_amount), 2) AS avg_tip,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct,
    ROUND(100 * SUM(CASE WHEN tip_amount > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_trips_tipped
FROM trips
GROUP BY service_type;

-- 5. Tip percentage by hour of day and payment type (credit card only,
--    since cash tips are typically not captured in the data)
SELECT
    pickup_hour,
    COUNT(*) AS trip_count,
    ROUND(AVG(tip_amount), 2) AS avg_tip,
    ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount END) * 100, 2) AS avg_tip_pct
FROM trips
WHERE payment_type = 1
GROUP BY pickup_hour
ORDER BY pickup_hour;
