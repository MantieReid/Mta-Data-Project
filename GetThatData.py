import dask.dataframe as dd
import pandas as pd
import matplotlib.pyplot as plt

# Define the path to your large CSV file
file_path = 'MTA_Subway_Hourly_Ridership__Beginning_July_2020.csv'

# Load the dataset using Dask for efficient processing of large files
ddf = dd.read_csv(file_path, assume_missing=True)

# Filter for the specified stations
filtered_ddf = ddf[ddf['station_complex'].isin(['Gun Hill Rd (5)', 'Gun Hill Rd (2,5)'])]

# Convert 'transit_timestamp' to datetime
filtered_ddf['transit_timestamp'] = dd.to_datetime(filtered_ddf['transit_timestamp'], errors='coerce')

# Drop rows with invalid or missing 'transit_timestamp'
filtered_ddf = filtered_ddf.dropna(subset=['transit_timestamp'])

# Extract the hour from the timestamp
filtered_ddf['hour'] = filtered_ddf['transit_timestamp'].dt.hour

# Aggregate ridership counts by hour
hourly_ridership = filtered_ddf.groupby('hour')['ridership_count'].sum().compute()

# Plot the bar chart
plt.figure(figsize=(10, 6))
hourly_ridership.plot(kind='bar', color='skyblue')
plt.xlabel('Hour of the Day')
plt.ylabel('Total Ridership Count')
plt.title('Hourly Ridership for Gun Hill Rd Stations')
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()