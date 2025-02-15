import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. Define Paths ---
# Get the project root directory where the script is located
base_dir = Path(__file__).resolve().parents[3]

# Define the input file path (from "Source/Data/Raw")
input_dir = base_dir / "Source" / "Data" / "Raw"
file_path = input_dir / "MTA_Subway_Hourly_Ridership__2020-2024.csv"  # Change filename if needed

# Define the output directory path (to "Source/Data/reports")
output_dir = base_dir / "Source" / "Data" / "reports"
output_dir.mkdir(parents=True, exist_ok=True)  # Create directories if they don't exist

# Define the output file path
output_file = output_dir / "MTA_Station_Top_Ridership.xlsx"

# Check if file exists
if not file_path.exists():
    raise FileNotFoundError(f"🚨 File not found: {file_path}")

# --- 2. Load Data from CSV ---
df = pd.read_csv(file_path)

# Ensure the dataset has the correct column names
date_column = "transit_timestamp"  # Adjust if needed
ridership_column = "ridership"  # Adjust if needed
station_column = "station_complex"  # Adjust if needed

# Convert date column to datetime
df[date_column] = pd.to_datetime(df[date_column])

# Extract year for filtering
df["year"] = df[date_column].dt.year

# --- 3. Calculate Total Ridership Per Year ---
total_ridership_per_year = df.groupby("year")[ridership_column].sum()

# Get total ridership numbers for 2023 and 2024
official_ridership_2023 = total_ridership_per_year.get(2023, 0)  # Default to 0 if year not found
official_ridership_2024 = total_ridership_per_year.get(2024, 0)  # Default to 0 if year not found

print(f"✅ Total Subway Ridership in 2023: {official_ridership_2023}")
print(f"✅ Total Subway Ridership in 2024: {official_ridership_2024}")

# --- 4. Calculate Total Ridership Per Station ---
stations_2023 = df[df["year"] == 2023].groupby(station_column)[ridership_column].sum().reset_index()
stations_2024 = df[df["year"] == 2024].groupby(station_column)[ridership_column].sum().reset_index()

# --- 5. Get Top 5 Stations for Each Year ---
top5_2023 = stations_2023.sort_values(by=ridership_column, ascending=False).head(5)
top5_2024 = stations_2024.sort_values(by=ridership_column, ascending=False).head(5)

# --- 6. Get Top 10 Stations for Charting ---
top10_2023 = stations_2023.sort_values(by=ridership_column, ascending=False).head(10)
top10_2024 = stations_2024.sort_values(by=ridership_column, ascending=False).head(10)

# --- 7. Save Results to Excel with Formatting ---
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    workbook = writer.book

    # Define table styling
    table_style = {
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "bold": True,
        "fg_color": "#D3D3D3",
    }

    # Function to format and highlight top 5 stations
    def write_top5(sheet_name, df, writer):
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        format_green = workbook.add_format({"bg_color": "#90EE90", "bold": True, "border": 1})
        
        for row in range(1, len(df) + 1):
            worksheet.set_row(row, cell_format=format_green)
        
        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, workbook.add_format(table_style))

    # Save top 5 stations in separate sheets with formatting
    write_top5("Top 5 Stations 2023", top5_2023, writer)
    write_top5("Top 5 Stations 2024", top5_2024, writer)

    # --- 8. Create and Insert Bar Chart ---
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top10_2023[station_column], top10_2023[ridership_column], label="2023", color="blue")
    ax.barh(top10_2024[station_column], top10_2024[ridership_column], label="2024", color="red", alpha=0.7)
    ax.set_xlabel("Ridership")
    ax.set_ylabel("Station Complex")
    ax.set_title("Top 10 Subway Stations Ridership (2023 vs 2024)")
    ax.legend()
    plt.gca().invert_yaxis()  # Invert y-axis for better readability

    # Save the chart as an image
    chart_path = output_dir / "top_10_ridership_chart.png"
    plt.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)

    # Insert chart into a new sheet
    worksheet_chart = workbook.add_worksheet("Top 10 Chart")
    worksheet_chart.insert_image("B2", str(chart_path))

print(f"✅ Updated file with top 5 and top 10 ridership analysis saved to: {output_file}")
