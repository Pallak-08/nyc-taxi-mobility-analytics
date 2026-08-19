"""
Build a single flattened CSV for the Tableau dashboard.

Joins zone names, and precomputes day-of-week / month labels and payment
labels in pandas rather than in Tableau calculated fields, so the .twb
workbook only needs to reference plain columns plus two simple ratio
calculations (avg fare, avg tip %). Labels are prefixed with a sort key
(e.g. "1-Sun", "01-Jan") so Tableau's default alphabetical sort already
puts them in chronological order without any custom sort config.
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOCKET = os.path.join(PROJECT_ROOT, "mysql_data", "mysql.sock")
EXPORT_DIR = os.path.join(PROJECT_ROOT, "exports")

engine = create_engine(f"mysql+pymysql://root@localhost/nyc_taxi?unix_socket={SOCKET}")

DAY_NAMES = {1: "1-Sun", 2: "2-Mon", 3: "3-Tue", 4: "4-Wed", 5: "5-Thu", 6: "6-Fri", 7: "7-Sat"}
MONTH_NAMES = {
    1: "01-Jan", 2: "02-Feb", 3: "03-Mar", 4: "04-Apr", 5: "05-May", 6: "06-Jun",
    7: "07-Jul", 8: "08-Aug", 9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}
PAYMENT_LABELS = {
    1: "Credit card", 2: "Cash", 3: "No charge", 4: "Dispute", 5: "Unknown", 6: "Voided trip",
}

df = pd.read_sql(text("""
    SELECT
        t.pickup_date, t.pickup_hour, t.pickup_dow, t.pickup_month, t.service_type,
        t.payment_type, z.borough, z.zone,
        COUNT(*) AS trip_count,
        SUM(t.trip_distance) AS total_distance,
        SUM(t.trip_duration_min) AS total_duration_min,
        SUM(t.fare_amount) AS fare_revenue,
        SUM(t.tip_amount) AS tip_revenue,
        SUM(t.total_amount) AS total_revenue,
        AVG(t.passenger_count) AS avg_passenger_count
    FROM trips t
    JOIN taxi_zones z ON t.pu_location_id = z.location_id
    GROUP BY t.pickup_date, t.pickup_hour, t.pickup_dow, t.pickup_month, t.service_type,
             t.payment_type, z.borough, z.zone
"""), engine)

df["day_name"] = df["pickup_dow"].map(DAY_NAMES)
df["month_name"] = df["pickup_month"].map(MONTH_NAMES)
df["payment_label"] = df["payment_type"].map(PAYMENT_LABELS).fillna("Other")
df = df.drop(columns=["pickup_dow", "pickup_month"])

out_path = os.path.join(EXPORT_DIR, "tableau_extract.csv")
df.to_csv(out_path, index=False)
print(f"wrote {out_path}: {len(df):,} rows, columns: {list(df.columns)}")
