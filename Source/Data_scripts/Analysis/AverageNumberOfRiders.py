

#Gets the average amount of riders per hour for each station and saves it to a CSV file. 


import pandas as pd

# Load the dataset
first_month_file_path = "MTA_Ridership_Data_02-07-2025_23-25-21.csv"  # Update path as needed
df_ridership = pd.read_csv(first_month_file_path)

# Convert transit_timestamp to datetime and extract hour
df_ridership["transit_timestamp"] = pd.to_datetime(df_ridership["transit_timestamp"], errors='coerce')
df_ridership.dropna(subset=["transit_timestamp"], inplace=True)  # Drop invalid timestamps
df_ridership["hour"] = df_ridership["transit_timestamp"].dt.hour

# Calculate the average number of riders for each hour for each station
avg_ridership_per_hour = df_ridership.groupby(["station_complex_id", "station_complex", "hour"])["ridership"].mean().reset_index()

# Save to CSV
avg_ridership_per_hour.to_csv("avg_ridership_per_hour.csv", index=False)

# Display the results
print(avg_ridership_per_hour)
