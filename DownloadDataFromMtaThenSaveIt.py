import requests
import pandas as pd
import concurrent.futures
import time
from datetime import datetime

# API Key Variable
API_KEY = "nssa5ESo6MsvtBcF7aIU6ZuJm"

# Base URL
BASE_URL = "https://data.ny.gov/resource/wujg-7c2s.json"

# Parameters for fetching data
LIMIT = 500000  # Reduce limit to prevent memory overload
offsets = range(0, 10000000, LIMIT)  # Creating offsets in steps of LIMIT

# Generate filename with timestamp
timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
filename = f"MTA_Ridership_Data_{timestamp}.csv"

# Function to fetch data
def fetch_data(offset):
    params = {
        "$$app_token": API_KEY,
        "$limit": LIMIT,
        "$offset": offset,
        "$where": "transit_timestamp >= '2023-01-01T00:00:00' AND transit_timestamp <= '2024-12-31T23:59:59'"
    }
    
    response = requests.get(BASE_URL, params=params)
    time.sleep(0.5)  # Prevent API overload
    
    if response.status_code != 200:
        print(f"Error {response.status_code} for offset {offset}")
        return []
    
    data = response.json()
    print(f"Fetched {len(data)} records at offset {offset}")
    return data

# Use multi-threading to fetch data faster without overloading memory
data_list = []
with open(filename, 'w', newline='', encoding='utf-8') as file:
    first_write = True  # Ensure header is only written once
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = executor.map(fetch_data, offsets)
        
        for result in results:
            if result:
                df = pd.DataFrame(result)
                df.to_csv(file, index=False, header=first_write, mode='a')
                first_write = False  # Disable headers after first write

print(f"Data saved to {filename}")
