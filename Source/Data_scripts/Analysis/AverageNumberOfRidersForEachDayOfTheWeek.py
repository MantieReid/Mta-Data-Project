import pandas as pd
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches
import os
from pathlib import Path

# Load the CSV file
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Data", "Raw", "MTA_Subway_Hourly_Ridership__2020-2024.csv")
if not os.path.exists(file_path):
    raise FileNotFoundError(f"CSV file not found at path: {file_path}")

# Read the data in chunks to handle large file size
chunk_size = 100000
daily_ridership = pd.DataFrame()

# Specify the date format for the transit_timestamp column
date_format = '%m/%d/%Y %I:%M:%S %p'

for chunk in pd.read_csv(file_path, 
                        chunksize=chunk_size,
                        low_memory=False,
                        parse_dates=['transit_timestamp'],
                        date_format=date_format):
    # Filter data for the year 2023 and create a copy
    mask_2023 = chunk["transit_timestamp"].dt.year == 2023
    chunk_2023 = chunk[mask_2023].copy()
    
    if not chunk_2023.empty:
        # Add new columns to the copy
        chunk_2023.loc[:, "date"] = chunk_2023["transit_timestamp"].dt.date
        chunk_2023.loc[:, "day_of_week"] = chunk_2023["transit_timestamp"].dt.day_name()
        
        # Sum ridership by date
        daily_sum = chunk_2023.groupby(["date", "day_of_week"])["ridership"].sum().reset_index()
        daily_ridership = pd.concat([daily_ridership, daily_sum])

# Group by date and sum to get true daily totals
daily_ridership = daily_ridership.groupby(["date", "day_of_week"])["ridership"].sum().reset_index()

# Calculate the average ridership for each day of the week
avg_ridership = daily_ridership.groupby("day_of_week")["ridership"].mean().reindex([
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
])

# Create output directories if they don't exist
for dir_path in [
    os.path.join(base_dir, "Data", "processed"),
    os.path.join(base_dir, "Data", "charts", "Powerpoint_format")
]:
    os.makedirs(dir_path, exist_ok=True)

# Save results to Excel with formatting
excel_path = os.path.join(base_dir, "Data", "processed", "average_ridership_2023.xlsx")
with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
    # Convert to DataFrame and format columns
    avg_ridership_df = avg_ridership.reset_index()
    avg_ridership_df.columns = ["Day of the Week", "Average Ridership"]
    
    # Write to Excel
    avg_ridership_df.to_excel(writer, index=False, sheet_name='Average Ridership')
    
    # Get the workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Average Ridership']
    
    # Add number formatting for the ridership column
    number_format = workbook.add_format({'num_format': '#,##0'})
    worksheet.set_column('B:B', 18, number_format)
    worksheet.set_column('A:A', 15)  # Width for day of week column

    # Add table formatting
    worksheet.add_table(0, 0, len(avg_ridership_df), 1, {
        'columns': [
            {'header': 'Day of the Week'},
            {'header': 'Average Ridership', 'format': number_format}
        ],
        'style': 'Table Style Medium 2'
    })

# Plot a bar chart with improved formatting
plt.figure(figsize=(12, 6))
bars = plt.bar(avg_ridership.index, avg_ridership.values, color='#1f77b4', alpha=0.8)
plt.xlabel("Day of the Week", fontsize=10, fontweight='bold')
plt.ylabel("Average Ridership", fontsize=10, fontweight='bold')
plt.title("Average Daily Subway Ridership by Day of Week (2023)", 
          fontsize=12, fontweight='bold', pad=20)
plt.xticks(rotation=45, ha="right")
plt.grid(axis="y", linestyle="--", alpha=0.7)

# Add value labels on top of bars
def format_with_commas(x):
    return f'{x:,.0f}'

for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             format_with_commas(height),
             ha='center', va='bottom')

plt.tight_layout()

# Save the chart
chart_path = os.path.join(base_dir, "Data", "processed", "ridership_chart.png")
plt.savefig(chart_path, dpi=300, bbox_inches='tight')
plt.close()

# Create PowerPoint presentation
ppt_path = os.path.join(base_dir, "Data", "charts", "Powerpoint_format", "average_ridership_2023.pptx")
prs = Presentation()
slide_layout = prs.slide_layouts[5]  # Title Only layout
slide = prs.slides.add_slide(slide_layout)
title = slide.shapes.title
title.text = "Average Daily Subway Ridership by Day of Week (2023)"

# Add the chart image to the PowerPoint slide
left = Inches(1)
top = Inches(1.5)
slide.shapes.add_picture(chart_path, left, top, width=Inches(8))

# Save the PowerPoint file
prs.save(ppt_path)

# Print output paths
print("✅ Excel file saved at:", excel_path)
print("✅ PowerPoint file saved at:", ppt_path)