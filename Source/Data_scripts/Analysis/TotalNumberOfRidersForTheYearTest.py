import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. Define Paths ---
base_dir = Path(__file__).resolve().parents[3]
input_dir = base_dir / "Source" / "Data" / "Raw"
file_path = input_dir / "MTA_Subway_Hourly_Ridership__2020-2024.csv"
output_dir = base_dir / "Source" / "Data" / "reports"
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "MTA_Station_Ridership_Analysis.xlsx"

if not file_path.exists():
    raise FileNotFoundError(f"🚨 File not found: {file_path}")

# --- 2. Load Data from CSV in Chunks ---
chunksize = 100000
date_column = "transit_timestamp"
ridership_column = "ridership"
station_column = "station_complex"

total_ridership_per_year = {}
stations_2023 = {}
stations_2024 = {}

for chunk in pd.read_csv(file_path, chunksize=chunksize, parse_dates=[date_column]):
    chunk["year"] = chunk[date_column].dt.year
    yearly_ridership = chunk.groupby("year")[ridership_column].sum()
    for year, ridership in yearly_ridership.items():
        total_ridership_per_year[year] = total_ridership_per_year.get(year, 0) + ridership

    stations_2023_chunk = chunk[chunk["year"] == 2023].groupby(station_column)[ridership_column].sum()
    for station, ridership in stations_2023_chunk.items():
        stations_2023[station] = stations_2023.get(station, 0) + ridership

    stations_2024_chunk = chunk[chunk["year"] == 2024].groupby(station_column)[ridership_column].sum()
    for station, ridership in stations_2024_chunk.items():
        stations_2024[station] = stations_2024.get(station, 0) + ridership

official_ridership_2023 = total_ridership_per_year.get(2023, 0)
official_ridership_2024 = total_ridership_per_year.get(2024, 0)

print(f"✅ Total Subway Ridership in 2023: {official_ridership_2023}")
print(f"✅ Total Subway Ridership in 2024: {official_ridership_2024}")

stations_2023 = pd.DataFrame(list(stations_2023.items()), columns=[station_column, ridership_column])
stations_2024 = pd.DataFrame(list(stations_2024.items()), columns=[station_column, ridership_column])

stations_2023["percentage"] = (stations_2023[ridership_column] / official_ridership_2023) * 100 if official_ridership_2023 > 0 else 0
stations_2024["percentage"] = (stations_2024[ridership_column] / official_ridership_2024) * 100 if official_ridership_2024 > 0 else 0

top5_2023 = stations_2023.sort_values(by=ridership_column, ascending=False).head(15)
top5_2024 = stations_2024.sort_values(by=ridership_column, ascending=False).head(15)
top10_2023 = stations_2023.sort_values(by=ridership_column, ascending=False).head(10)
top10_2024 = stations_2024.sort_values(by=ridership_column, ascending=False).head(10)

with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    workbook = writer.book
    
    # Create formats
    header_format = workbook.add_format({
        "bold": True,
        "fg_color": "#D3D3D3",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
    })
    
    data_format = workbook.add_format({
        "border": 1,
        "border_color": "#000000"
    })
    
    top5_data_format = workbook.add_format({
        "bg_color": "#C6EFCE",
        "border": 1,
        "border_color": "#000000"
    })

    def write_sheet_with_borders(df, sheet_name, writer, use_color=False):
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        
        # Format headers
        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_format)
        
        # Format data cells and apply borders only to cells with data
        format_to_use = top5_data_format if use_color else data_format
        for row_num in range(len(df)):
            for col_num in range(len(df.columns)):
                value = df.iloc[row_num, col_num]
                if pd.notna(value):  # Only format cells that contain data
                    worksheet.write(row_num + 1, col_num, value, format_to_use)

    # Write main station sheets with borders
    write_sheet_with_borders(stations_2023, "2023 Ridership", writer)
    write_sheet_with_borders(stations_2024, "2024 Ridership", writer)

    # Write top stations sheets with colored background
    write_sheet_with_borders(top5_2023, "Top 5 Stations 2023", writer, use_color=True)
    write_sheet_with_borders(top5_2024, "Top 5 Stations 2024", writer, use_color=True)

    # Create and save the chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top10_2023[station_column], top10_2023[ridership_column], label="2023", color="blue")
    ax.barh(top10_2024[station_column], top10_2024[ridership_column], label="2024", color="red", alpha=0.7)
    ax.set_xlabel("Ridership")
    ax.set_ylabel("Station Complex")
    ax.set_title("Top 10 Subway Stations Ridership (2023 vs 2024)")
    ax.legend()
    plt.gca().invert_yaxis()

    chart_path = output_dir / "top_10_ridership_chart.png"
    plt.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)

    # Add the chart to the workbook
    worksheet_chart = workbook.add_worksheet("Top 10 Chart")
    worksheet_chart.insert_image("B2", str(chart_path))

print(f"✅ Updated file with full ridership data, percentages, top stations, and charts saved to: {output_file}")