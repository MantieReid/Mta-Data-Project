import requests
import pandas as pd
import os
import random
import concurrent.futures

# Base API URL
base_url = "https://data.ny.gov/api/odata/v4/wujg-7c2s"

# Set a large number of records to fetch
# Fetch the total number of records from the API
count_url = f"{base_url}/$count"
response = requests.get(count_url)
try:
    total_records = int(response.text)
except ValueError:
    print(f"Error fetching total records: {response.text}")
    total_records = 1000000  # Default to a large number if there's an error

batch_size = 50000  # Fetch 50,000 records per request

print(f"Fetching data in batches of {batch_size} records...")

# Function to fetch a batch of data
def fetch_batch(skip):
    url = f"{base_url}?$top={batch_size}&$skip={skip}"
    response = requests.get(url)
    return response.json().get('value', [])

# Use multithreading to fetch pages concurrently
all_data = []
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(fetch_batch, range(0, total_records, batch_size)))

# Flatten the list of lists into a single dataset
all_data = [item for sublist in results for item in sublist]

print(f"Total records fetched: {len(all_data)}")

# Convert data to DataFrame
df = pd.DataFrame(all_data)

# Ensure the datetime column is in datetime format
df['transit_timestamp'] = pd.to_datetime(df['transit_timestamp'])

# Extract date and hour
df['date'] = df['transit_timestamp'].dt.date
df['hour'] = df['transit_timestamp'].dt.hour

# Group by station_complex_ID, station_complex, latitude, longitude, and hour
grouped = df.groupby(['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour'])

# Calculate the average ridership amount
average_ridership = grouped['ridership'].mean().reset_index()
average_ridership.columns = ['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour', 'average_ridership']

# Generate unique filename if needed
file_name = "average_ridership.csv"
while os.path.exists(file_name):
    file_name = f"average_ridership_{random.randint(1, 1000)}.csv"

# Save to CSV
average_ridership.to_csv(file_name, index=False)

print(f"Results saved to {file_name}")
