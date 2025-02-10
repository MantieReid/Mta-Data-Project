import pandas as pd

# Load the dataset
file_path = "MTA_Ridership_Data_02-07-2025_23-25-21.csv"  # Update the path as needed

# Ensure station_complex_id is treated as an integer
df = pd.read_csv(file_path)

# Ensure station_complex_id is treated as an integer
df["station_complex_id"] = pd.to_numeric(df["station_complex_id"], errors='coerce')

# Convert transit_timestamp to datetime format and extract year and month
df["transit_timestamp"] = pd.to_datetime(df["transit_timestamp"], errors='coerce')
df.dropna(subset=["transit_timestamp"], inplace=True)  # Drop rows with invalid timestamps
df["year"] = df["transit_timestamp"].dt.year
df["month"] = df["transit_timestamp"].dt.month

# Get the first year and month of a specific station (e.g., station_complex_id = 444)
if not df[df["station_complex_id"] == 444].empty:
    first_year_month = df[df["station_complex_id"] == 444][["year", "month"]].drop_duplicates().sort_values(by=["year", "month"]).iloc[0]
    first_year, first_month = first_year_month["year"], first_year_month["month"]
    
    # Get all data for the first recorded month of the station
    first_month_data = df[(df["station_complex_id"] == 444) & (df["year"] == first_year) & (df["month"] == first_month)]
    
    # Save to CSV
    first_month_data.to_csv("first_month.csv", index=False)
    
    # Display the results
    print(first_month_data)
else:
    print("No data found for station_complex_id 444.")
