-- NYC TLC Trip Data — unified schema for Yellow + Green taxi trips (2023)
-- Yellow and Green use different pickup/dropoff column names and have a few
-- service-specific fields (airport_fee is yellow-only, trip_type is green-only).
-- We normalize both into one `trips` table with a service_type discriminator
-- so demand/revenue analysis can run across or within service types.

CREATE DATABASE IF NOT EXISTS nyc_taxi;
USE nyc_taxi;

DROP TABLE IF EXISTS trips;
CREATE TABLE trips (
    trip_id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    service_type            ENUM('yellow','green') NOT NULL,
    vendor_id                TINYINT,
    pickup_datetime          DATETIME NOT NULL,
    dropoff_datetime         DATETIME NOT NULL,
    passenger_count          TINYINT,
    trip_distance             DECIMAL(8,2),
    ratecode_id               TINYINT,
    store_and_fwd_flag        CHAR(1),
    pu_location_id            SMALLINT,
    do_location_id            SMALLINT,
    payment_type               TINYINT,
    fare_amount                DECIMAL(8,2),
    extra                       DECIMAL(6,2),
    mta_tax                     DECIMAL(6,2),
    tip_amount                  DECIMAL(8,2),
    tolls_amount                 DECIMAL(8,2),
    improvement_surcharge        DECIMAL(6,2),
    congestion_surcharge          DECIMAL(6,2),
    airport_fee                    DECIMAL(6,2),   -- yellow only
    trip_type                       TINYINT,         -- green only (1=street-hail, 2=dispatch)
    total_amount                     DECIMAL(8,2),
    -- Derived columns computed automatically at write time for fast slicing
    trip_duration_min DECIMAL(10,2)
        GENERATED ALWAYS AS (TIMESTAMPDIFF(SECOND, pickup_datetime, dropoff_datetime) / 60) STORED,
    pickup_hour  TINYINT GENERATED ALWAYS AS (HOUR(pickup_datetime)) STORED,
    pickup_dow   TINYINT GENERATED ALWAYS AS (DAYOFWEEK(pickup_datetime)) STORED,  -- 1=Sunday..7=Saturday
    pickup_month TINYINT GENERATED ALWAYS AS (MONTH(pickup_datetime)) STORED,
    pickup_date  DATE    GENERATED ALWAYS AS (DATE(pickup_datetime)) STORED,

    INDEX idx_pickup_datetime (pickup_datetime),
    INDEX idx_service_type (service_type),
    INDEX idx_pu_location (pu_location_id),
    INDEX idx_do_location (do_location_id),
    INDEX idx_pickup_hour (pickup_hour),
    INDEX idx_pickup_dow (pickup_dow),
    INDEX idx_pickup_month (pickup_month),
    INDEX idx_payment_type (payment_type)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS taxi_zones;
CREATE TABLE taxi_zones (
    location_id   SMALLINT PRIMARY KEY,
    borough       VARCHAR(30),
    zone          VARCHAR(100),
    service_zone  VARCHAR(30)
) ENGINE=InnoDB;
