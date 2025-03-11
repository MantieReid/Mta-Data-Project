import requests
import pandas as pd
import concurrent.futures
import time
from datetime import datetime


import configparser
import os

config = configparser.ConfigParser()
config.read("config.ini")

API_KEY = os.getenv("API_KEY")  # Load from environment variables
print(API_KEY)


# Base URL
BASE_URL = "https://data.ny.gov/resource/wujg-7c2s.json"

# Parameters for fetching data
LIMIT = 500000  # Reduce limit to prevent memory overload
MAX_RECORDS = 10000000  # Stop after 10 million records
offset = 0  # Start offset

# Generate filename with timestamp
timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
#filename = f"MTA_Ridership_Data_{timestamp}.csv"
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path_output = os.path.join(base_dir, "Data", "reports")

# Ensure the directory exists
os.makedirs(file_path_output, exist_ok=True)

# Generate filename with timestamp
timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
filename = os.path.join(file_path_output, f"MTA_Ridership_Data_{timestamp}.csv")
# Function to fetch data
def fetch_data(offset):
    params = {
        "$$app_token": API_KEY,
        "$limit": LIMIT,
        "$offset": offset,
        "$where": "transit_timestamp >= '2024-12-01T00:00:00' AND transit_timestamp <= '2024-12-31T23:59:59'",
        "$order": "transit_timestamp ASC"  # Sort results to ensure full range is included
    }
    
    response = requests.get(BASE_URL, params=params)
    time.sleep(0.5)  # Prevent API overload
    
    if response.status_code != 200:
        print(f"Error {response.status_code} for offset {offset}")
        return []
    
    data = response.json()
    
    if not data:
        print(f"No more data found at offset {offset}, stopping.")
        return []

    print(f"Fetched {len(data)} records at offset {offset}")

    return data

# Use multi-threading to fetch data faster without overloading memory
data_list = []
first_write = True  # Ensure header is only written once

with open(filename, 'w', newline='', encoding='utf-8') as file:
    while True:
        data = fetch_data(offset)

        if not data:
            break  # Stop when no more data is returned

        df = pd.DataFrame(data)

        # Save to CSV incrementally
        df.to_csv(file, index=False, header=first_write, mode='a')
        first_write = False  # Ensure headers are written only once

        offset += LIMIT  # Increment offset for next page

print(f"Data saved to {filename}")
