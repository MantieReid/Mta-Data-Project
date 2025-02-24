import pandas as pd
import os
from pathlib import Path

# --- 1. Define Paths ---
# Get the directory where the script is located
base_dir = Path(__file__).resolve().parent  

# Define the input file path (from "Source/Data/Raw")
input_dir = base_dir / "Source" / "Data" / "Raw"
file_path = input_dir / "mta_data.csv"  # Change filename if needed

# Define the output directory path (to "Source/Data/reports")
output_dir = base_dir / "Source" / "Data" / "reports"
output_dir.mkdir(parents=True, exist_ok=True)  # Create directories if they don't exist

# Define the output file path
output_file = output_dir / "MTA_Station_Ridership_Percentage.xlsx"

# Check if file exists
if not file_path.exists():
    raise FileNotFoundError(f"🚨 File not found: {file_path}")

# --- 2. Load Data ---
df = pd.read_csv(file_path)  # Use read_excel(file_path) if it's an Excel file

# Ensure the dataset has the correct column names
date_column = "transit_timestamp"  # Change if needed
ridership_column = "ridership"  # Change if needed
station_column = "station_complex"  # Change if needed

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

# --- 5. Calculate Each Station's Percentage of Total Ridership ---
if official_ridership_2023 > 0:
    stations_2023["percentage"] = (stations_2023[ridership_column] / official_ridership_2023) * 100
else:
    stations_2023["percentage"] = 0

if official_ridership_2024 > 0:
    stations_2024["percentage"] = (stations_2024[ridership_column] / official_ridership_2024) * 100
else:
    stations_2024["percentage"] = 0

# --- 6. Save Results to Excel in Custom Directory ---
with pd.ExcelWriter(output_file) as writer:
    stations_2023.to_excel(writer, sheet_name="2023 Ridership", index=False)
    stations_2024.to_excel(writer, sheet_name="2024 Ridership", index=False)

print(f"✅ Analysis complete! Results saved to {output_file}")