import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as ticker

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

# Define date format
date_format = '%m/%d/%Y %I:%M:%S %p'

total_ridership_per_year = {}
stations_2023 = {}
stations_2024 = {}

for chunk in pd.read_csv(
    file_path, 
    chunksize=chunksize, 
    parse_dates=[date_column],
    date_format=date_format,
    low_memory=False
):
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

print(f"✅ Total Subway Ridership in 2023: {official_ridership_2023:,}")
print(f"✅ Total Subway Ridership in 2024: {official_ridership_2024:,}")

stations_2023 = pd.DataFrame(list(stations_2023.items()), columns=[station_column, ridership_column])
stations_2024 = pd.DataFrame(list(stations_2024.items()), columns=[station_column, ridership_column])

stations_2023["percentage"] = (stations_2023[ridership_column] / official_ridership_2023) * 100 if official_ridership_2023 > 0 else 0
stations_2024["percentage"] = (stations_2024[ridership_column] / official_ridership_2024) * 100 if official_ridership_2024 > 0 else 0

# Format ridership numbers with commas
stations_2023[ridership_column] = stations_2023[ridership_column].apply(lambda x: '{:,.0f}'.format(x))
stations_2024[ridership_column] = stations_2024[ridership_column].apply(lambda x: '{:,.0f}'.format(x))

# Create copies with numeric values for sorting
stations_2023_numeric = stations_2023.copy()
stations_2024_numeric = stations_2024.copy()
stations_2023_numeric[ridership_column] = pd.to_numeric(stations_2023[ridership_column].str.replace(',', ''))
stations_2024_numeric[ridership_column] = pd.to_numeric(stations_2024[ridership_column].str.replace(',', ''))

# Sort and select top stations using numeric values but keep formatted strings
top5_2023 = stations_2023.loc[stations_2023_numeric.sort_values(by=ridership_column, ascending=False).index].head(15)
top5_2024 = stations_2024.loc[stations_2024_numeric.sort_values(by=ridership_column, ascending=False).index].head(15)
top10_2023 = stations_2023.loc[stations_2023_numeric.sort_values(by=ridership_column, ascending=False).index].head(10)
top10_2024 = stations_2024.loc[stations_2024_numeric.sort_values(by=ridership_column, ascending=False).index].head(10)

with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    workbook = writer.book

    def write_as_table(df, sheet_name, writer, use_color=False):
        # Write DataFrame to Excel
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        
        # Get the range for the table
        end_row = len(df)
        end_col = len(df.columns) - 1
        table_range = f'A1:{chr(65 + end_col)}{end_row + 1}'
        
        # Add a table to the worksheet
        table_style = 'Table Style Medium 2' if not use_color else 'Table Style Medium 4'
        worksheet.add_table(table_range, {
            'columns': [{'header': col} for col in df.columns],
            'style': table_style,
            'first_column': True
        })
        
        # Adjust column widths
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.set_column(idx, idx, max_length + 2)

    # Write main station sheets as tables
    write_as_table(stations_2023, "2023 Ridership", writer)
    write_as_table(stations_2024, "2024 Ridership", writer)

    # Write top stations sheets as tables with different style
    write_as_table(top5_2023, "Top 5 Stations 2023", writer, use_color=True)
    write_as_table(top5_2024, "Top 5 Stations 2024", writer, use_color=True)

    # Create and save the chart
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Convert formatted strings back to numbers for plotting
    top10_2023_plot = top10_2023.copy()
    top10_2024_plot = top10_2024.copy()
    top10_2023_plot[ridership_column] = pd.to_numeric(top10_2023[ridership_column].str.replace(',', ''))
    top10_2024_plot[ridership_column] = pd.to_numeric(top10_2024[ridership_column].str.replace(',', ''))
    
    ax.barh(top10_2023_plot[station_column], top10_2023_plot[ridership_column], label="2023", color="blue")
    ax.barh(top10_2024_plot[station_column], top10_2024_plot[ridership_column], label="2024", color="red", alpha=0.7)
    
    # Format x-axis with commas
    def format_with_commas(x, p):
        return f"{x:,.0f}"
    
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_with_commas))
    
    ax.set_xlabel("Ridership")
    ax.set_ylabel("Station Complex")
    ax.set_title("Top 10 Subway Stations Ridership (2023 vs 2024)")
    ax.legend()
    plt.gca().invert_yaxis()

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    chart_path = output_dir / "top_10_ridership_chart.png"
    plt.savefig(chart_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    # Create hourly ridership analysis
    hourly_data = pd.Series(0, index=range(24))
    total_chunks = 0
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        # Convert timestamp to datetime and extract hour
        chunk['hour'] = pd.to_datetime(chunk[date_column], format=date_format).dt.hour
        # Calculate average ridership by hour
        hourly_chunk = chunk.groupby('hour')[ridership_column].mean()
        hourly_data = hourly_data.add(hourly_chunk, fill_value=0)
        total_chunks += 1
    
    # Calculate the final average
    hourly_data = hourly_data / total_chunks

    # Reorder hours to start from 1 AM (hour 1) to midnight (hour 0)
    hours = list(range(1, 24)) + [0]
    hourly_data = hourly_data.reindex(hours)

    # Create the line chart
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(range(24), hourly_data, marker='o')

    # Customize x-axis labels
    hour_labels = [f'{h}:00' for h in (hours)]
    ax.set_xticks(range(24))
    ax.set_xticklabels(hour_labels, rotation=45)

    # Add labels and title
    ax.set_xlabel('Hour (EST)')
    ax.set_ylabel('Average Ridership')
    ax.set_title('Average Hourly Subway Ridership')

    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.7)

    # Save the chart
    hourly_chart_path = output_dir / "hourly_ridership_chart.png"
    plt.savefig(hourly_chart_path, bbox_inches="tight", dpi=300)
    plt.close(fig)

    # Add hourly chart to workbook
    worksheet_hourly = workbook.add_worksheet("Hourly Chart")
    worksheet_hourly.insert_image("B2", str(hourly_chart_path))
    # Add the chart to the workbook
    worksheet_chart = workbook.add_worksheet("Top 10 Chart")
    worksheet_chart.insert_image("B2", str(chart_path))

print(f"✅ Updated file with full ridership data, percentages, top stations, and charts saved to: {output_file}")