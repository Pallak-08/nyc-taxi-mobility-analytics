# Data quality & cleaning notes

Applied during ingestion (`scripts/load_data.py`), not after — so every table in
`nyc_taxi` already reflects these filters.

**Rows dropped when loading each monthly file:**
- Null/unparseable `pickup_datetime` or `dropoff_datetime`
- `pickup_datetime` outside the file's stated year/month (TLC files contain a small
  number of trips with corrupted dates, e.g. year 2002 or 2088 — these are known
  data entry errors, not real trips)
- `dropoff_datetime < pickup_datetime`
- `trip_distance` negative or >= 500 miles (unrealistic for an in-city trip)
- `fare_amount` or `total_amount` outside [-200, 2000] (extreme outliers /
  data entry errors; small negative values are kept since they represent
  legitimate fare corrections/refunds per TLC documentation)

**Rows kept as-is (flagged, not dropped) — analyze with awareness of these:**
- `passenger_count = 0`: valid per TLC (dispatch-recorded trips without a
  passenger count entry), excluded only from passenger-count-specific queries
- Negative `fare_amount`/`total_amount` within the bounds above: fare corrections
- `payment_type` values 3-6 (no charge, dispute, unknown, voided): kept for
  completeness in payment-behavior analysis, but tip amounts on cash trips
  (`payment_type = 2`) are known to be under-reported since cash tips aren't
  captured in the meter

**Derived columns** (`trips` table, generated columns, always in sync with source):
`trip_duration_min`, `pickup_hour`, `pickup_dow`, `pickup_month`, `pickup_date`
