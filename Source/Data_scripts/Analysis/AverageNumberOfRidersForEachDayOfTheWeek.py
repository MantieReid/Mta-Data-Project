import pandas as pd
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches
import os

# Load the CSV file
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Data", "Raw", "MTA_Subway_Hourly_Ridership__2020-2024.csv")
if not os.path.exists(file_path):
    raise FileNotFoundError(f"CSV file not found at path: {file_path}")
df = pd.read_csv(file_path)

# Convert transit_timestamp to datetime format
df["transit_timestamp"] = pd.to_datetime(df["transit_timestamp"])

# Filter data for the year 2023
df_2023 = df[df["transit_timestamp"].dt.year == 2023]

# Extract day of the week
df_2023["day_of_week"] = df_2023["transit_timestamp"].dt.day_name()

daily_ridership = df_2023.groupby(["transit_timestamp", "day_of_week"])["ridership"].sum().reset_index()



# Calculate the average ridership for each day of the week
avg_ridership = daily_ridership.groupby("day_of_week")["ridership"].mean().reindex(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
)

# Save results to Excel
excel_path = os.path.join(base_dir, "Data", "processed", "average_ridership_2023.xlsx")
avg_ridership_df = avg_ridership.reset_index()
avg_ridership_df.columns = ["Day of the Week", "Average Ridership"]
avg_ridership_df.to_excel(excel_path, index=False)


# Plot a bar chart
plt.figure(figsize=(10, 5))
plt.bar(avg_ridership.index, avg_ridership.values)
plt.xlabel("Day of the Week")
plt.ylabel("Average Ridership")
plt.title("Average Ridership for Each Day of the Week in 2023")
plt.xticks(rotation=45, ha="right")  # Adjust rotation and alignment for better visibility
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

# Save the updated chart image
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
chart_path = os.path.join(base_dir, "Data", "processed", "ridership_chart.png")
plt.savefig(chart_path)
plt.close()

# Create a PowerPoint presentation
ppt_path = os.path.join(base_dir, "Data", "charts", "Powerpoint_format", "average_ridership_2023.pptx")
prs = Presentation()
slide_layout = prs.slide_layouts[5]  # Title Only layout
slide = prs.slides.add_slide(slide_layout)
title = slide.shapes.title
title.text = "Average Ridership for Each Day of the Week (2023)"

# Add the chart image to the PowerPoint slide
left = Inches(1.5)
top = Inches(1.5)
slide.shapes.add_picture(chart_path, left, top, width=Inches(7))

# Save the PowerPoint file
prs.save(ppt_path)

# Provide output paths
print("Excel file saved at:", excel_path)
print("PowerPoint file saved at:", ppt_path)
