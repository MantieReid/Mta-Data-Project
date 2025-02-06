import requests
import pandas as pd
import concurrent.futures

# Define the base API endpoint and parameters
base_url = "https://data.ny.gov/resource/wujg-7c2s.json"
where_clause = "transit_timestamp > '2024-01-01T00:00:00.000'::floating_timestamp"
limit = 1000  # Number of records to fetch per request

# Initialize an empty list to store the data
all_data = []
total_records = 0

def fetch_data(offset):
    query = f"{base_url}?$where={where_clause}&$limit={limit}&$offset={offset}"
    response = requests.get(query)
    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except ValueError:
            print("Error decoding JSON response; skipping batch.")
    else:
        print(f"Failed to fetch data at offset {offset}. Status code: {response.status_code}")
    return []

# Using multithreading to fetch data faster
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    offset = 0
    futures = []
    results = []  # Initialize results list to avoid NameError
    while True:
        futures.append(executor.submit(fetch_data, offset))
        offset += limit
        if len(futures) >= 10:  # Process 10 batches at a time
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            for result in results:
                if result:
                    all_data.extend(result)
                    total_records += len(result)
                    print(f"Retrieved {total_records} records so far...")
            futures.clear()
        if not results or any(len(result) < limit for result in results):
            break

# Convert the accumulated data to a DataFrame
df = pd.DataFrame(all_data)

# Save to CSV file
csv_filename = "MTA_Ridership_Data_After_2024.csv"
df.to_csv(csv_filename, index=False)
print(f"Data successfully saved to {csv_filename}")
