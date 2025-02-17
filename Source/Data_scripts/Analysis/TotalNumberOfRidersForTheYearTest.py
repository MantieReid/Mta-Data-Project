import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Disable GPU acceleration to prevent BSOD
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches
from pathlib import Path

# --- 1. Define Paths ---
base_dir = Path(__file__).resolve().parents[3]
input_dir = base_dir / "Source" / "Data" / "Raw"
output_dir = base_dir / "Source" / "Data" / "reports"
output_dir.mkdir(parents=True, exist_ok=True)

# Define file paths
file_path = input_dir / "MTA_Subway_Hourly_Ridership__2020-2024.csv"
output_file = output_dir / "MTA_Station_Ridership_Analysis.xlsx"
ppt_path = output_dir / "Average_Ridership_Presentation.pptx"

if not file_path.exists():
    raise FileNotFoundError(f"🚨 File not found: {file_path}")

# --- 2. Load Data Efficiently ---
chunk_size = 100000  # Further optimized chunk size
agg_ridership = []
agg_stations = []

# Process chunks incrementally
def process_chunk(chunk):
    chunk.dropna(subset=["transit_timestamp"], inplace=True)
    chunk["transit_timestamp"] = pd.to_datetime(chunk["transit_timestamp"], errors='coerce')
    chunk.dropna(subset=["transit_timestamp"], inplace=True)
    chunk["year"] = chunk["transit_timestamp"].dt.year
    chunk["hour"] = chunk["transit_timestamp"].dt.hour
    chunk["AM_PM"] = chunk["hour"].map(lambda x: f"{x % 12 or 12} {'AM' if x < 12 else 'PM'}")
    
    agg_ridership.append(chunk.groupby(["year", "AM_PM"])['ridership'].mean().reset_index())
    agg_stations.append(chunk.groupby(["year", "station_complex"])['ridership'].sum().reset_index())

for chunk in pd.read_csv(file_path, chunksize=chunk_size, usecols=["transit_timestamp", "ridership", "station_complex"], low_memory=False):
    process_chunk(chunk)

df_ridership = pd.concat(agg_ridership).groupby(["year", "AM_PM"]).mean().reset_index()
df_stations = pd.concat(agg_stations).groupby(["year", "station_complex"]).sum().reset_index()

total_ridership_per_year = df_stations.groupby("year")["ridership"].sum()
df_stations["percentage"] = df_stations.apply(lambda row: (row["ridership"] / total_ridership_per_year.get(row["year"], 1)) * 100, axis=1)

# --- 3. Save to Excel Efficiently ---
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    df_ridership.to_excel(writer, sheet_name="Avg Ridership", index=False)
    df_stations.to_excel(writer, sheet_name="All Stations Ridership", index=False)

# --- 4. Generate Charts Efficiently ---
def generate_chart(data, year, output_dir):
    plt.figure(figsize=(10, 6))
    plt.plot(data["AM_PM"], data["ridership"], marker='o', linestyle='-', label=f"{year}")
    plt.title(f"Average Ridership Per Hour - {year}")
    plt.xlabel("Time (EST)")
    plt.ylabel("Avg Riders")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    chart_filename = output_dir / f"Average_Ridership_Per_Hour_{year}.png"
    plt.savefig(chart_filename, bbox_inches="tight")
    plt.close()
    return chart_filename

# --- 5. Create PowerPoint ---
ppt = Presentation()
for year in [2023, 2024]:
    year_data = df_ridership[df_ridership["year"] == year]
    chart_filename = generate_chart(year_data, year, output_dir)
    slide = ppt.slides.add_slide(ppt.slide_layouts[5])
    slide.shapes.add_picture(str(chart_filename), Inches(1), Inches(1.5), height=Inches(5))
ppt.save(ppt_path)

print(f"✅ Data analysis complete. Excel and PowerPoint reports saved.")
