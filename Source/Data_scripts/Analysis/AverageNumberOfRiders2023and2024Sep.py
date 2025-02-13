#Gets the results for 2023 and 2024 of average number of riders for each station for each hour.  
# Saves them to two separate CSV file.


import pandas as pd



# Load the dataset
first_month_file_path = "MTA_Ridership_Data_02-07-2025_23-25-21.csv"  # Update path as needed
df_ridership = pd.read_csv(first_month_file_path)

# Convert transit_timestamp to datetime and extract year and hour
df_ridership["transit_timestamp"] = pd.to_datetime(df_ridership["transit_timestamp"], errors='coerce')
df_ridership.dropna(subset=["transit_timestamp"], inplace=True)  # Drop invalid timestamps
df_ridership["year"] = df_ridership["transit_timestamp"].dt.year
df_ridership["hour"] = df_ridership["transit_timestamp"].dt.hour

# Separate data for 2023 and 2024
df_2023 = df_ridership[df_ridership["year"] == 2023]
df_2024 = df_ridership[df_ridership["year"] == 2024]
# Calculate the average number of riders for each hour for each station
avg_ridership_2023 = df_2023.groupby(["station_complex_id",  "station_complex", "hour", "latitude", "longitude", "georeference"])["ridership"].mean().reset_index()
avg_ridership_2024 = df_2024.groupby(["station_complex_id", "station_complex", "hour", "latitude", "longitude", "georeference"])["ridership"].mean().reset_index()

# Save to separate CSV files
avg_ridership_2023.to_csv("avg_ridership_2023.csv", index=False)
avg_ridership_2024.to_csv("avg_ridership_2024.csv", index=False)

# Display the results
print("Average ridership for 2023 saved to avg_ridership_2023.csv")
print("Average ridership for 2024 saved to avg_ridership_2024.csv")
