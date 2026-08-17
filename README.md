# Urban Mobility Demand, Revenue & Operational Efficiency

An analysis of NYC TLC taxi trip data framed as a business problem: **how can a mobility business
understand demand, revenue performance, and operational patterns to identify opportunities for
improving utilization and revenue?**

Rather than treating this as a generic "explore the taxi dataset" exercise, every query and chart here
is built to answer one of five business questions:

1. **Demand** — when and where is demand concentrated?
2. **Revenue** — which periods and locations generate the strongest revenue?
3. **Trip economics** — what trip characteristics are associated with stronger revenue efficiency?
4. **Operational efficiency** — what do demand patterns suggest about fleet utilization?
5. **Passenger/payment behavior** — which payment methods and group sizes tip more, and how?

## Dataset

[NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) — Yellow +
Green taxi trips, full year 2023. ~39.1M trips after cleaning (see `sql/README_data_quality.md` for the
exact filters applied at ingestion — corrupt dates, negative distances, and other known TLC data issues).

## Stack

- **MySQL** — 39M+ rows loaded locally; all heavy aggregation (GROUP BY, CTEs, window functions,
  ranking, joins against the taxi zone lookup) happens here rather than in pandas.
- **Python** (pandas, matplotlib, seaborn) — EDA notebook that queries MySQL directly, with a 1M-row
  random sample pulled for correlation/outlier/distribution work that needs row-level data.
- **Tableau** — business-facing dashboard, built from the pre-aggregated CSV extracts the notebook
  generates. *(In progress — dashboard link to be added here.)*

## Repo structure

```
sql/
  00_schema.sql              unified trips + taxi_zones schema (yellow/green normalized into one table)
  01_demand_analysis.sql
  02_revenue_analysis.sql
  03_trip_economics.sql
  04_operational_efficiency.sql
  05_payment_behavior.sql
  README_data_quality.md     cleaning rules applied during ingestion
notebooks/
  nyc_taxi_eda.ipynb         full EDA with visualizations, run against the full 39M-row dataset
scripts/
  download_data.sh           pulls the raw parquet + zone lookup + shapefile from the TLC CDN
  load_data.py                cleans and bulk-loads everything into MySQL
```

`raw_data/`, `mysql_data/`, and `exports/` are gitignored — they're regenerated locally (see below)
rather than committed, since the raw data alone is ~630MB and the loaded database is ~13GB.

## Reproducing this locally

```bash
pip install -r requirements.txt

# 1. Download raw data (~630MB, 24 monthly parquet files + zone lookup + shapefile)
./scripts/download_data.sh

# 2. Set up a local MySQL instance and load the schema
mysql -u root -e "CREATE DATABASE IF NOT EXISTS nyc_taxi;"
mysql -u root nyc_taxi < sql/00_schema.sql

# 3. Clean and bulk-load ~39M trips (takes a few minutes)
python3 scripts/load_data.py

# 4. Run the notebook
jupyter notebook notebooks/nyc_taxi_eda.ipynb
```

## Key findings

- **Demand** is concentrated at evening rush (peaking 5–7pm) and in a small footprint — just 31 of 263
  zones (12%) account for 80% of all pickups. JFK Airport is the single busiest pickup zone.
- **Revenue** totaled $1.11B across the year ($761.7M fares + $136.8M tips), averaging $28.36/trip.
  Airports punch above their trip-volume weight on revenue due to long, higher-fare trips — JFK alone
  generated $155.7M.
- **Trip economics**: revenue efficiency is highest on short trips — sub-1-mile trips earn $20.42/mile
  vs. $5.27/mile for 10+ mile trips — while $/minute stays comparatively flat across distance bands.
- **Operational efficiency**: demand concentration (12% of zones = 80% of pickups) suggests utilization
  is more a *distribution* problem than a *volume* problem; the lowest-demand windows (weekday 2–5am)
  see ~20x fewer trips than peak hours.
- **Payment/passenger behavior**: credit card trips tip far more than cash (27.4% vs. ~0% recorded —
  cash tips aren't captured in the meter, a known TLC data limitation). Tip rates are broadly similar
  across solo riders and groups.

Full breakdown with charts in [`notebooks/nyc_taxi_eda.ipynb`](notebooks/nyc_taxi_eda.ipynb).
