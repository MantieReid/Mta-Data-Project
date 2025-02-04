import requests
import pandas as pd
import os
import random

# Fetch data from the MTA link
url = "https://data.ny.gov/api/odata/v4/wujg-7c2s"
response = requests.get(url)
data = response.json()

# Convert the data to a pandas DataFrame
df = pd.DataFrame(data['value'])

# Ensure the datetime column is in datetime format
df['transit_timestamp'] = pd.to_datetime(df['transit_timestamp'])
# Ensure the datetime column is in datetime format
df['transit_timestamp'] = pd.to_datetime(df['transit_timestamp'])

# Extract date from the datetime column
df['date'] = df['transit_timestamp'].dt.date

# Extract hour from the datetime column
df['hour'] = df['transit_timestamp'].dt.hour

# Group by station_complex_ID, station_complex, latitude, longitude, and hour
grouped = df.groupby(['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour'])

# Calculate the average ridership amount for each group
average_ridership = grouped['ridership'].mean().reset_index()

# Rename the columns for clarity
average_ridership.columns = ['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour', 'average_ridership']

# Define the base file name
base_file_name = "average_ridership.csv"
file_name = base_file_name

# Check if the file already exists and add a random number if it does
while os.path.exists(file_name):
    random_number = random.randint(1, 1000)
    file_name = f"average_ridership_{random_number}.csv"

# Save the result to a CSV file
average_ridership.to_csv(file_name, index=False)

# Display the result
print(f"Results saved to {file_name}")