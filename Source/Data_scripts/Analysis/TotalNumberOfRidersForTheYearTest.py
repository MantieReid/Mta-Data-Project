import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Disable GPU acceleration to prevent BSOD
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches
from pathlib import Path

# Define base directory
base_dir = Path(__file__).resolve().parent.parent.parent.parent

# Define input and output directories
input_dir = base_dir / "Source" / "Data" / "Raw"
output_dir = base_dir / "Source" / "Data" / "reports"
output_dir.mkdir(parents=True, exist_ok=True)  # Create directories if they don't exist

# Load the dataset efficiently with chunks
file_path = input_dir / "MTA_Subway_Hourly_Ridership__2020-2024.csv"
chunks = pd.read_csv(file_path, chunksize=10000, parse_dates=["transit_timestamp"], infer_datetime_format=True, low_memory=False)  # Efficient datetime parsing

# Initialize empty DataFrame for incremental aggregation
agg_ridership = pd.DataFrame()
agg_stations = pd.DataFrame()

# Process chunks incrementally without storing all data in memory
for chunk in chunks:
    chunk.dropna(subset=["transit_timestamp"], inplace=True)  # Remove rows with missing timestamps
    chunk["year"] = chunk["transit_timestamp"].dt.year
    chunk["hour"] = chunk["transit_timestamp"].dt.hour
    chunk["AM_PM"] = chunk["hour"].apply(lambda x: f"{x % 12 if x % 12 != 0 else 12} {'AM' if x < 12 else 'PM'}")
    
    # Incremental aggregation for ridership per hour
    chunk_agg = chunk.groupby(["year", "AM_PM"])['ridership'].mean().reset_index()
    agg_ridership = pd.concat([agg_ridership, chunk_agg]).groupby(["year", "AM_PM"]).mean().reset_index()
    
    # Incremental aggregation for station ridership
    chunk_station_agg = chunk.groupby(["year", "station_complex"])['ridership'].sum().reset_index()
    agg_stations = pd.concat([agg_stations, chunk_station_agg]).groupby(["year", "station_complex"]).sum().reset_index()

# Define all possible hours for completeness
all_hours = pd.DataFrame({"AM_PM": [f"{h % 12 if h % 12 != 0 else 12} {'AM' if h < 12 else 'PM'}" for h in range(1, 25)]})

# Merge to ensure all hours are represented
avg_ridership = all_hours.merge(agg_ridership, on="AM_PM", how="left")

# Calculate total ridership per year
total_ridership = agg_stations.groupby("year")["ridership"].sum().reset_index()

# Compute percentage contribution per station
agg_stations = agg_stations.merge(total_ridership, on="year", suffixes=("", "_total"))
agg_stations["ridership_percentage"] = (agg_stations["ridership"] / agg_stations["ridership_total"]) * 100

# Get top 5 stations for each year
top_stations_2023 = agg_stations[agg_stations["year"] == 2023].nlargest(5, "ridership")
top_stations_2024 = agg_stations[agg_stations["year"] == 2024].nlargest(5, "ridership")

# Save aggregated data to Excel
excel_path = output_dir / "Average_Ridership_Data.xlsx"
with pd.ExcelWriter(excel_path) as writer:
    avg_ridership.to_excel(writer, sheet_name="Avg Ridership", index=False)
    agg_stations.to_excel(writer, sheet_name="All Stations Ridership", index=False)
    top_stations_2023.to_excel(writer, sheet_name="Top 5 Stations 2023", index=False)
    top_stations_2024.to_excel(writer, sheet_name="Top 5 Stations 2024", index=False)

# Create PowerPoint presentation
ppt = Presentation()

for year in [2023, 2024]:
    year_data = avg_ridership[avg_ridership["year"] == year]
    
    # Create line chart
    plt.figure(figsize=(10, 6))
    plt.plot(year_data["AM_PM"], year_data["ridership"], marker='o', linestyle='-', label=f"{year}")
    plt.title(f"Average Ridership Per Hour (All Stations) - {year}", fontsize=16)
    plt.xlabel("Time (EST)", fontsize=14)
    plt.ylabel("Avg Riders", fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    # Save chart as an image
    chart_filename = output_dir / f"Average_Ridership_Per_Hour_{year}.png"
    plt.savefig(chart_filename)
    plt.close('all')  # Close all open figures to prevent memory leak
    
    # Add slide to PowerPoint
    slide = ppt.slides.add_slide(ppt.slide_layouts[5])  # Blank slide
    title = slide.shapes.title
    if title:
        title.text = f"Average Ridership Per Hour - {year}"
    
    # Add chart image to PowerPoint
    left = Inches(1)
    top = Inches(1.5)
    height = Inches(5)
    slide.shapes.add_picture(str(chart_filename), left, top, height=height)

# Save PowerPoint file
ppt_path = output_dir / "Average_Ridership_Presentation.pptx"
ppt.save(ppt_path)

print(f"PowerPoint generated: {ppt_path}")
print(f"Excel file saved: {excel_path}")
