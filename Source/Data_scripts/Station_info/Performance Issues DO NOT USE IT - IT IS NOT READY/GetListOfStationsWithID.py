import pandas as pd

# Load the dataset (update the file path if needed)
file_path = "MTA_Ridership_Data_02-07-2025_23-25-21.csv"
df = pd.read_csv(file_path)

# Extract unique stations and their IDs
station_list = df["station_complex"].unique()
stationID_list = df["station_complex_id"].unique()

# Create a DataFrame ensuring both columns are added to the CSV.
station_df = pd.DataFrame({
    "station_complex": station_list,
    "station_complex_id": stationID_list
})

# Save to a CSV file for easy review
station_df.to_csv("MTA_Station_List.csv", index=False)

# Display first few stations
print(station_df.head(10))