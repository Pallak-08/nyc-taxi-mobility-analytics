#!/usr/bin/env bash
# Downloads the raw NYC TLC data this project runs on:
#   - Yellow + Green taxi trip records for all 12 months of 2023 (parquet)
#   - Taxi zone lookup table (LocationID -> Borough/Zone)
#   - Taxi zone shapefile (for spatial mapping in Tableau)
#
# Source: NYC TLC Trip Record Data (https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="$PROJECT_ROOT/raw_data"
BASE_URL="https://d37ci6vzurychx.cloudfront.net"

mkdir -p "$RAW_DIR"
cd "$RAW_DIR"

echo "Downloading Yellow + Green trip data for 2023 (24 files, ~630MB total)..."
for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
    curl -sS -o "yellow_tripdata_2023-$month.parquet" "$BASE_URL/trip-data/yellow_tripdata_2023-$month.parquet" &
    curl -sS -o "green_tripdata_2023-$month.parquet"  "$BASE_URL/trip-data/green_tripdata_2023-$month.parquet" &
done
wait

echo "Downloading taxi zone lookup table..."
curl -sS -o taxi_zone_lookup.csv "$BASE_URL/misc/taxi+_zone_lookup.csv"

echo "Downloading taxi zone shapefile..."
curl -sS -o taxi_zones.zip "$BASE_URL/misc/taxi_zones.zip"
mkdir -p "$PROJECT_ROOT/exports/taxi_zones_shapefile"
unzip -oq taxi_zones.zip -d "$PROJECT_ROOT/exports/taxi_zones_shapefile"
rm taxi_zones.zip

echo "Done. Raw data in $RAW_DIR"
