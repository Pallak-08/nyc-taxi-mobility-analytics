"""
Ingest NYC TLC Yellow + Green taxi parquet files (2023) into MySQL.

Normalizes both service schemas into the unified `trips` table, applies
baseline data-quality filters (TLC data is known to contain out-of-range
dates and a small number of corrupt rows), and bulk-loads via
LOAD DATA LOCAL INFILE for speed on ~41M rows.
"""
import os
import glob
import pymysql

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "raw_data")
TMP_DIR = os.path.join(RAW_DIR, "_tmp_csv")
SOCKET = os.path.join(PROJECT_ROOT, "mysql_data", "mysql.sock")
os.makedirs(TMP_DIR, exist_ok=True)

TRIP_COLUMNS = [
    "service_type", "vendor_id", "pickup_datetime", "dropoff_datetime",
    "passenger_count", "trip_distance", "ratecode_id", "store_and_fwd_flag",
    "pu_location_id", "do_location_id", "payment_type", "fare_amount",
    "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "congestion_surcharge", "airport_fee", "trip_type", "total_amount",
]

YELLOW_RENAME = {
    "VendorID": "vendor_id",
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "RatecodeID": "ratecode_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "PULocationID": "pu_location_id",
    "DOLocationID": "do_location_id",
    "payment_type": "payment_type",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "congestion_surcharge": "congestion_surcharge",
    "airport_fee": "airport_fee",
}

GREEN_RENAME = {
    "VendorID": "vendor_id",
    "lpep_pickup_datetime": "pickup_datetime",
    "lpep_dropoff_datetime": "dropoff_datetime",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "RatecodeID": "ratecode_id",
    "PULocationID": "pu_location_id",
    "DOLocationID": "do_location_id",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "payment_type": "payment_type",
    "trip_type": "trip_type",
    "congestion_surcharge": "congestion_surcharge",
}


def load_file(path, service_type, rename_map, year, month):
    import pandas as pd

    df = pd.read_parquet(path)
    df = df.rename(columns=rename_map)
    df["service_type"] = service_type

    for col in ("airport_fee", "trip_type"):
        if col not in df.columns:
            df[col] = pd.NA

    df = df[TRIP_COLUMNS]

    # --- data quality filters ---
    # TLC files contain a small number of rows with corrupt/out-of-range
    # pickup dates (e.g. year 2002 or 2088) and non-physical trips.
    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")

    mask = (
        df["pickup_datetime"].notna()
        & df["dropoff_datetime"].notna()
        & (df["pickup_datetime"].dt.year == year)
        & (df["pickup_datetime"].dt.month == month)
        & (df["dropoff_datetime"] >= df["pickup_datetime"])
        & (df["trip_distance"] >= 0)
        & (df["trip_distance"] < 500)
        & (df["fare_amount"].between(-200, 2000))
        & (df["total_amount"].between(-200, 2000))
    )
    df = df[mask].copy()

    # round nullable numeric/id columns that map to integer MySQL types
    for col in ("vendor_id", "passenger_count", "ratecode_id", "payment_type", "trip_type"):
        df[col] = pd.to_numeric(df[col], errors="coerce").round()

    csv_path = os.path.join(TMP_DIR, f"{service_type}_{year}-{month:02d}.csv")
    df.to_csv(csv_path, index=False, header=False, na_rep="\\N")
    return csv_path, len(df)


def bulk_load(conn, csv_path):
    cols = ", ".join(TRIP_COLUMNS)
    sql = f"""
        LOAD DATA LOCAL INFILE '{csv_path}'
        INTO TABLE trips
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        ({cols})
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def load_zones(conn):
    zone_csv = os.path.join(RAW_DIR, "taxi_zone_lookup.csv")
    if not os.path.exists(zone_csv):
        print("SKIP taxi_zone_lookup.csv not found (run scripts/download_data.sh first)")
        return
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE taxi_zones")
        cur.execute(f"""
            LOAD DATA LOCAL INFILE '{zone_csv}'
            INTO TABLE taxi_zones
            FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\\r\\n'
            IGNORE 1 LINES
            (location_id, borough, zone, service_zone)
        """)
    conn.commit()
    print("loaded taxi_zone_lookup.csv")


def main():
    conn = pymysql.connect(
        unix_socket=SOCKET, user="root", database="nyc_taxi",
        local_infile=True, autocommit=False,
    )
    with conn.cursor() as cur:
        cur.execute("SET GLOBAL local_infile = 1")

    load_zones(conn)

    total_rows = 0
    for month in range(1, 13):
        for service, rename_map in (("yellow", YELLOW_RENAME), ("green", GREEN_RENAME)):
            fname = f"{service}_tripdata_2023-{month:02d}.parquet"
            path = os.path.join(RAW_DIR, fname)
            if not os.path.exists(path):
                print(f"SKIP missing {fname}")
                continue
            csv_path, n = load_file(path, service, rename_map, 2023, month)
            bulk_load(conn, csv_path)
            os.remove(csv_path)
            total_rows += n
            print(f"loaded {fname}: {n:,} rows (running total {total_rows:,})")

    conn.close()
    print(f"DONE. total rows loaded: {total_rows:,}")


if __name__ == "__main__":
    main()
