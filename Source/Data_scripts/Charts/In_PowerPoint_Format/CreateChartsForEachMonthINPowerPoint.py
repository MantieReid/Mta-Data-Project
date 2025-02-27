import pandas as pd
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches
import os


current_dir = os.getcwd()
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
file_path = os.path.join(project_root, "Source", "Data", "Raw", "MTA_Subway_Hourly_Ridership__2020-2024.csv")

# Load the dataset
df = pd.read_csv(file_path)

# Convert transit_timestamp to datetime format
df["transit_timestamp"] = pd.to_datetime(df["transit_timestamp"], errors="coerce")

# Extract year, month, and hour
df["year"] = df["transit_timestamp"].dt.year
df["month"] = df["transit_timestamp"].dt.month
df["hour"] = df["transit_timestamp"].dt.hour

# Convert military time to 12-hour AM/PM format
df["AM_PM"] = df["hour"].apply(lambda x: f"{x % 12 if x % 12 != 0 else 12} {'AM' if x < 12 else 'PM'}")

# Define all possible hours for completeness
all_hours = pd.DataFrame({"AM_PM": [f"{h % 12 if h % 12 != 0 else 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]})

# Create a tracking dictionary for processed stations
processed_stations = {}

# Process data for both 2023 and 2024
for year in [2023, 2024]:
    df_year = df[df["year"] == year]
    
    # Skip if no data for this year
    if df_year.empty:
        print(f"No data available for year {year}")
        continue

    # Get unique months with data
    months = sorted(df_year["month"].unique())
    
    # Loop through each month
    for month in months:
        month_data = df_year[df_year["month"] == month]
        
        # Skip if no data for this month
        if month_data.empty:
            print(f"No data available for month {month}/{year}")
            continue
            
        print(f"Processing {month}/{year}")
        
        # Get stations that actually have data for this month
        stations_with_data = month_data["station_complex_id"].unique()
        print(f"Found {len(stations_with_data)} stations with data for {month}/{year}")
        
        # Calculate average ridership per station per hour
        avg_ridership = month_data.groupby(["station_complex_id", "station_complex", "AM_PM"])["ridership"].mean().reset_index()

        # Create PowerPoint presentation
        ppt = Presentation()
        chart_count = 0

        # Plot only stations with actual data
        for station_id in stations_with_data:
            station_data = avg_ridership[avg_ridership["station_complex_id"] == station_id]

            # Skip stations with insufficient data
            if len(station_data) < 12:  # Require at least half the hours to have data
                print(f"Skipping station {station_id} due to insufficient data points ({len(station_data)} hours)")
                continue

            station_name = station_data["station_complex"].iloc[0]
            
            # Track processed stations to detect duplicates
            station_key = f"{station_id}_{month}_{year}"
            if station_key in processed_stations:
                print(f"Skipping duplicate station: {station_name} (ID: {station_id}) for {month}/{year}")
                continue
            processed_stations[station_key] = True
            
            # Sanitize station names for filenames
            sanitized_station_name = station_name.replace("/", "-").replace("\\", "-").replace("*", "-").replace("[", "(").replace("]", ")").replace(":", "-").replace("?", "-").replace("'", "-").replace(",", "-").replace(".", "-").strip()[:31]

            # Merge with all_hours to ensure all 24 hours are represented
            station_data = all_hours.merge(station_data, on="AM_PM", how="left")
            
            # Check if we have enough non-null data points after merging
            valid_data_points = station_data["ridership"].count()
            if valid_data_points < 12:  # Require at least half the hours to have valid data
                print(f"Skipping station {station_name} due to insufficient valid data points ({valid_data_points} hours)")
                continue
                
            station_data["ridership"] = station_data["ridership"].interpolate(method="linear")  # Fill missing values

            # Create a line chart
            plt.figure(figsize=(10, 6))
            plt.plot(station_data["AM_PM"], station_data["ridership"], marker='o', linestyle='-', label=f"Avg Riders: {station_data['ridership'].mean():.2f}")
            plt.title(f"Avg Ridership for {sanitized_station_name} - {month}/{year}", fontsize=16)
            plt.xlabel("Time (EST)", fontsize=14)
            plt.ylabel("Avg Riders", fontsize=14)
            plt.xticks(rotation=45)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.legend()
            plt.tight_layout()

            # Save chart as an image
            img_name = f"station_{station_id}_month_{month}_{year}.png"
            plt.savefig(img_name)
            plt.close()

            # Add slide to PowerPoint
            slide = ppt.slides.add_slide(ppt.slide_layouts[5])  # Blank slide
            title = slide.shapes.title
            title.text = f"{sanitized_station_name} - {month}/{year}"

            # Position and size image
            left = Inches(1)
            top = Inches(1.5)
            height = Inches(5)
            slide.shapes.add_picture(img_name, left, top, height=height)
            
            chart_count += 1

        # Only save PowerPoint if charts were created
        if chart_count > 0:
            ppt_path = f"MTA_Ridership_{month}_{year}.pptx"
            ppt.save(ppt_path)
            print(f"PowerPoint generated with {chart_count} charts: {ppt_path}")
        else:
            print(f"No charts generated for {month}/{year}, skipping PowerPoint creation")

        # Clean up images
        for station_id in stations_with_data:
            img_file = f"station_{station_id}_month_{month}_{year}.png"
            if os.path.exists(img_file):
                os.remove(img_file)

# Print summary
print(f"Total unique station-month combinations processed: {len(processed_stations)}")