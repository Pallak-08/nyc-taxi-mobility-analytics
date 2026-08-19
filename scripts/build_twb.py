"""
Generates tableau/nyc_taxi_dashboard.twb by assembling Tableau's workbook
XML from templates. Written this way (rather than by hand in the app)
because computer-use automation permissions weren't available for this
session; the repetitive column/metadata blocks are generated programmatically
to reduce hand-typing errors, while worksheet shelves/marks are hand-crafted.
"""
import os
import xml.etree.ElementTree as ET

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(PROJECT_ROOT, "exports")
OUT_PATH = os.path.join(PROJECT_ROOT, "tableau", "nyc_taxi_dashboard.twb")

DS1 = "federated.tabextract01"   # exports/tableau_extract.csv
DS2 = "federated.topzonesrev01"  # exports/top_zones_by_revenue.csv
DS3 = "federated.topzonesvol01"  # exports/top_zones_by_volume.csv

# (remote_name, local_type, role, type, remote_type_code)
DS1_COLS = [
    ("pickup_date", "date", "dimension", "ordinal", 133),
    ("pickup_hour", "integer", "measure", "quantitative", 20),
    ("service_type", "string", "dimension", "nominal", 129),
    ("payment_type", "real", "dimension", "nominal", 5),
    ("borough", "string", "dimension", "nominal", 129),
    ("zone", "string", "dimension", "nominal", 129),
    ("trip_count", "integer", "measure", "quantitative", 20),
    ("total_distance", "real", "measure", "quantitative", 5),
    ("total_duration_min", "real", "measure", "quantitative", 5),
    ("fare_revenue", "real", "measure", "quantitative", 5),
    ("tip_revenue", "real", "measure", "quantitative", 5),
    ("total_revenue", "real", "measure", "quantitative", 5),
    ("avg_passenger_count", "real", "measure", "quantitative", 5),
    ("day_name", "string", "dimension", "nominal", 129),
    ("month_name", "string", "dimension", "nominal", 129),
    ("payment_label", "string", "dimension", "nominal", 129),
]
DS2_COLS = [
    ("zone", "string", "dimension", "nominal", 129),
    ("borough", "string", "dimension", "nominal", 129),
    ("total_revenue", "real", "measure", "quantitative", 5),
]
DS3_COLS = [
    ("zone", "string", "dimension", "nominal", 129),
    ("borough", "string", "dimension", "nominal", 129),
    ("trip_count", "integer", "measure", "quantitative", 20),
]

CALCS = [
    ("Calculation_avgfare", "Avg Fare", "SUM([total_revenue])/SUM([trip_count])"),
    ("Calculation_avgtip", "Avg Tip %", "SUM([tip_revenue])/SUM([fare_revenue])"),
]


def col_decl(name, local_type, role, ctype, caption=None, calc=None):
    cap = f" caption='{caption}'" if caption else ""
    if calc:
        return (f"<column{cap} datatype='{local_type}' name='[{name}]' role='{role}' type='{ctype}'>"
                f"<calculation class='tableau' formula='{calc}' /></column>")
    return f"<column datatype='{local_type}' name='[{name}]' role='{role}' type='{ctype}' />"


def metadata_record(remote_name, local_type, remote_type_code, parent_table, ordinal):
    agg = "Year" if local_type == "date" else ("Sum" if local_type in ("integer", "real") else "Count")
    return f"""<metadata-record class='column'>
      <remote-name>{remote_name}</remote-name>
      <remote-type>{remote_type_code}</remote-type>
      <local-name>[{remote_name}]</local-name>
      <parent-name>[{parent_table}]</parent-name>
      <remote-alias>{remote_name}</remote-alias>
      <ordinal>{ordinal}</ordinal>
      <local-type>{local_type}</local-type>
      <aggregation>{agg}</aggregation>
      <contains-null>true</contains-null>
    </metadata-record>"""


def build_datasource(ds_name, caption, csv_filename, columns, calcs=None):
    table_ref = f"{csv_filename.replace('.csv','')}#csv"
    metadata = "\n      ".join(
        metadata_record(name, ltype, code, table_ref, i + 1)
        for i, (name, ltype, role, ctype, code) in enumerate(columns)
    )
    col_map = "\n      ".join(f"<map key='[{name}]' value='[{name}]' />" for name, *_ in columns)
    col_decls = "\n    ".join(col_decl(name, ltype, role, ctype) for name, ltype, role, ctype, _ in columns)
    calc_decls = ""
    if calcs:
        calc_decls = "\n    " + "\n    ".join(
            col_decl(cname, "real", "measure", "quantitative", caption=ccap, calc=cformula)
            for cname, ccap, cformula in calcs
        )

    return f"""<datasource caption='{caption}' inline='true' name='{ds_name}' version='18.1'>
    <connection class='federated'>
      <named-connections>
        <named-connection caption='{csv_filename}' name='textscan.{ds_name.split('.')[1]}'>
          <connection class='textscan' directory='{EXPORT_DIR}' filename='{csv_filename}' server='' />
        </named-connection>
      </named-connections>
      <relation connection='textscan.{ds_name.split('.')[1]}' name='{table_ref}' table='[{table_ref}]' type='table'>
      </relation>
      <cols>
      {col_map}
      </cols>
      <metadata-records>
      {metadata}
      </metadata-records>
    </connection>
    {col_decls}{calc_decls}
  </datasource>"""


def shelf_ref(ds, name, kind):
    """kind: 'dim' (plain discrete dim), 'dim_forced' (numeric forced discrete),
    'measure' (SUM aggregated), 'agg_calc' (already-aggregated calc field)"""
    if kind == "dim":
        return f"[{ds}].[{name}]"
    if kind == "dim_forced":
        return f"[{ds}].[none:{name}:nk]"
    if kind == "measure":
        return f"[{ds}].[sum:{name}:qk]"
    if kind == "agg_calc":
        return f"[{ds}].[agg:{name}:qk]"
    raise ValueError(kind)


def dep_col(name, ltype, role, ctype, caption=None):
    cap = f" caption='{caption}'" if caption else ""
    return f"<column{cap} datatype='{ltype}' name='[{name}]' role='{role}' type='{ctype}' />"


def worksheet(name, ds, mark, rows, cols, encodings_xml, dep_cols_xml):
    return f"""<worksheet name='{name}'>
    <table>
      <view>
        <datasources>
          <datasource caption='{name}' name='{ds}' />
        </datasources>
        <datasource-dependencies datasource='{ds}'>
        {dep_cols_xml}
        </datasource-dependencies>
      </view>
      <style />
      <panes>
        <pane selection-relaxation-option='selection-relaxed'>
          <view>
            <breakdown value='auto' />
          </view>
          <mark class='{mark}' />
          <encodings>
          {encodings_xml}
          </encodings>
        </pane>
      </panes>
      <rows>{rows}</rows>
      <cols>{cols}</cols>
    </table>
  </worksheet>"""


def main():
    ds1_xml = build_datasource(DS1, "tableau_extract", "tableau_extract.csv", DS1_COLS, CALCS)
    ds2_xml = build_datasource(DS2, "top_zones_by_revenue", "top_zones_by_revenue.csv", DS2_COLS)
    ds3_xml = build_datasource(DS3, "top_zones_by_volume", "top_zones_by_volume.csv", DS3_COLS)

    worksheets = []

    # 1-3: KPI tiles
    worksheets.append(worksheet(
        "KPI - Total Trips", DS1, "Text", "", shelf_ref(DS1, "trip_count", "measure"),
        f"<text column='{shelf_ref(DS1, 'trip_count', 'measure')}' />",
        dep_col("trip_count", "integer", "measure", "quantitative"),
    ))
    worksheets.append(worksheet(
        "KPI - Total Revenue", DS1, "Text", "", shelf_ref(DS1, "total_revenue", "measure"),
        f"<text column='{shelf_ref(DS1, 'total_revenue', 'measure')}' />",
        dep_col("total_revenue", "real", "measure", "quantitative"),
    ))
    worksheets.append(worksheet(
        "KPI - Avg Fare", DS1, "Text", "", shelf_ref(DS1, "Calculation_avgfare", "agg_calc"),
        f"<text column='{shelf_ref(DS1, 'Calculation_avgfare', 'agg_calc')}' />",
        dep_col("Calculation_avgfare", "real", "measure", "quantitative", caption="Avg Fare"),
    ))

    # 4: Demand heatmap
    worksheets.append(worksheet(
        "Demand Heatmap", DS1, "Square",
        shelf_ref(DS1, "day_name", "dim"),
        shelf_ref(DS1, "pickup_hour", "dim_forced"),
        f"<color column='{shelf_ref(DS1, 'trip_count', 'measure')}' />"
        f"<text column='{shelf_ref(DS1, 'trip_count', 'measure')}' />",
        dep_col("day_name", "string", "dimension", "nominal") +
        dep_col("pickup_hour", "integer", "measure", "quantitative") +
        dep_col("trip_count", "integer", "measure", "quantitative"),
    ))

    # 5: Revenue by pickup zone
    worksheets.append(worksheet(
        "Revenue by Pickup Zone", DS2, "Bar",
        shelf_ref(DS2, "zone", "dim"),
        shelf_ref(DS2, "total_revenue", "measure"),
        f"<color column='{shelf_ref(DS2, 'borough', 'dim')}' />",
        dep_col("zone", "string", "dimension", "nominal") +
        dep_col("borough", "string", "dimension", "nominal") +
        dep_col("total_revenue", "real", "measure", "quantitative"),
    ))

    # 6: Trip volume by pickup zone
    worksheets.append(worksheet(
        "Trip Volume by Pickup Zone", DS3, "Bar",
        shelf_ref(DS3, "zone", "dim"),
        shelf_ref(DS3, "trip_count", "measure"),
        f"<color column='{shelf_ref(DS3, 'borough', 'dim')}' />",
        dep_col("zone", "string", "dimension", "nominal") +
        dep_col("borough", "string", "dimension", "nominal") +
        dep_col("trip_count", "integer", "measure", "quantitative"),
    ))

    # 7: Monthly revenue trend
    worksheets.append(worksheet(
        "Monthly Revenue Trend", DS1, "Line",
        shelf_ref(DS1, "total_revenue", "measure"),
        shelf_ref(DS1, "month_name", "dim"),
        "",
        dep_col("month_name", "string", "dimension", "nominal") +
        dep_col("total_revenue", "real", "measure", "quantitative"),
    ))

    # 8: Payment & tip behavior
    worksheets.append(worksheet(
        "Payment and Tip Behavior", DS1, "Bar",
        shelf_ref(DS1, "payment_label", "dim"),
        shelf_ref(DS1, "Calculation_avgtip", "agg_calc"),
        "",
        dep_col("payment_label", "string", "dimension", "nominal") +
        dep_col("Calculation_avgtip", "real", "measure", "quantitative", caption="Avg Tip %"),
    ))

    worksheets_xml = "\n  ".join(worksheets)

    ws_names = [
        "KPI - Total Trips", "KPI - Total Revenue", "KPI - Avg Fare", "Demand Heatmap",
        "Revenue by Pickup Zone", "Trip Volume by Pickup Zone", "Monthly Revenue Trend",
        "Payment and Tip Behavior",
    ]

    # Dashboard layout: 3 KPI tiles on top, heatmap below, 2 zone bars, then trend + payment
    zones = f"""<zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='12000' id='10' param='vert' type-v2='layout-flow' w='100000' x='0' y='0'>
            <zone h='12000' id='11' name='KPI - Total Trips' w='33333' x='0' y='0' />
            <zone h='12000' id='12' name='KPI - Total Revenue' w='33333' x='33333' y='0' />
            <zone h='12000' id='13' name='KPI - Avg Fare' w='33334' x='66666' y='0' />
          </zone>
          <zone h='30000' id='14' name='Demand Heatmap' w='100000' x='0' y='12000' />
          <zone h='29000' id='15' param='horz' type-v2='layout-flow' w='100000' x='0' y='42000'>
            <zone h='29000' id='16' name='Revenue by Pickup Zone' w='50000' x='0' y='42000' />
            <zone h='29000' id='17' name='Trip Volume by Pickup Zone' w='50000' x='50000' y='42000' />
          </zone>
          <zone h='29000' id='18' param='horz' type-v2='layout-flow' w='100000' x='0' y='71000'>
            <zone h='29000' id='19' name='Monthly Revenue Trend' w='50000' x='0' y='71000' />
            <zone h='29000' id='20' name='Payment and Tip Behavior' w='50000' x='50000' y='71000' />
          </zone>
        </zone>
      </zones>"""

    dashboard = f"""<dashboard name='NYC Taxi Mobility Dashboard'>
    <style />
    <size maxheight='1200' maxwidth='1600' minheight='1200' minwidth='1600' sizing-mode='automatic' />
    {zones}
  </dashboard>"""

    windows = "\n  ".join(
        f"<window class='worksheet' name='{n}'><viewpoints /></window>" for n in ws_names
    )
    windows += f"\n  <window class='dashboard' maximized='true' name='NYC Taxi Mobility Dashboard'><viewpoints /></window>"

    workbook = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version='18.1' source-build='2023.1.0' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
  </preferences>
  <datasources>
    {ds1_xml}
    {ds2_xml}
    {ds3_xml}
  </datasources>
  <worksheets>
  {worksheets_xml}
  </worksheets>
  <dashboards>
  {dashboard}
  </dashboards>
  <windows source-height='42'>
  {windows}
  </windows>
</workbook>
"""

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(workbook)

    # Validate well-formed XML
    ET.parse(OUT_PATH)
    print(f"wrote and validated {OUT_PATH}")


if __name__ == "__main__":
    main()
