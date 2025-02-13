import pandas as pd
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches
import os

# Load the dataset
file_path = "MTA_Ridership_Data_02-07-2025_23-25-21.csv"  # Update this path
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

# Process data for both 2023 and 2024
for year in [2023, 2024]:
    df_year = df[df["year"] == year]

    # Get unique stations and months
    stations = df_year["station_complex_id"].unique()
    months = sorted(df_year["month"].unique())

    # Loop through each month
    for month in months:
        month_data = df_year[df_year["month"] == month]

        # Calculate average ridership per station per hour
        avg_ridership = month_data.groupby(["station_complex_id", "station_complex", "AM_PM"])["ridership"].mean().reset_index()

        # Create PowerPoint presentation
        ppt = Presentation()

        # Plot each station's data
        for station_id in stations:
            station_data = avg_ridership[avg_ridership["station_complex_id"] == station_id]

            if station_data.empty:
                continue

            station_name = station_data["station_complex"].iloc[0]

            # Sanitize station names for filenames
            sanitized_station_name = station_name.replace("/", "-").replace("\\", "-").replace("*", "-").replace("[", "(").replace("]", ")").replace(":", "-").replace("?", "-").replace("'", "-").replace(",", "-").replace(".", "-").strip()[:31]

            # Merge with all_hours to ensure all 24 hours are represented
            station_data = all_hours.merge(station_data, on="AM_PM", how="left")
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

        # Save PowerPoint for the month
        ppt_path = f"MTA_Ridership_{month}_{year}.pptx"
        ppt.save(ppt_path)
        print(f"PowerPoint generated: {ppt_path}")

        # Clean up images
        for station_id in stations:
            img_file = f"station_{station_id}_month_{month}_{year}.png"
            if os.path.exists(img_file):
                os.remove(img_file)
