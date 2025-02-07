import pandas as pd

# Define file path
file_path = "MTA_Ridership_Data_02-06-2025_21-51-02.csv"

# Load CSV data
print("Loading data...")
df = pd.read_csv(file_path)

# Ensure column names are stripped of whitespace
df.columns = df.columns.str.strip()

# Check required columns
required_columns = {"station_complex_id", "transit_timestamp"}
missing_columns = required_columns - set(df.columns)
if missing_columns:
    print(f"Error: Missing columns {missing_columns}")
    exit()

# Convert columns to correct types
df["station_complex_id"] = pd.to_numeric(df["station_complex_id"], errors="coerce")
df["transit_timestamp"] = pd.to_datetime(df["transit_timestamp"], errors="coerce")

# Debug: Check earliest and latest timestamps
print("Earliest timestamp:", df["transit_timestamp"].min())
print("Latest timestamp:", df["transit_timestamp"].max())

# Sort by date to ensure correct ordering
df = df.sort_values(by="transit_timestamp")

# Filter data for station_complex_id 444 and full 2023-2024 date range
filtered_df = df[
    (df["station_complex_id"] == 444) &
    (df["transit_timestamp"] >= pd.Timestamp("2023-01-01")) &
    (df["transit_timestamp"] <= pd.Timestamp("2024-12-31 23:59:59"))
]

# Debug: Check filtered range
print("Filtered earliest timestamp:", filtered_df["transit_timestamp"].min())
print("Filtered latest timestamp:", filtered_df["transit_timestamp"].max())

# Save to CSV if data is found
if filtered_df.empty:
    print("No matching records found for station_complex_id 444 within 2023-2024.")
else:
    output_filename = "Filtered_Station_Data.csv"
    filtered_df.to_csv(output_filename, index=False)
    print(f"Filtered data saved to {output_filename}")
