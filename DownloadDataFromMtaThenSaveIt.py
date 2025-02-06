import requests
import pandas as pd
from datetime import datetime
import pytz

def get_all_records(url, batch_size=1000):
    records = []
    offset = 0
    while True:
        paged_url = f"{url}?$top={batch_size}&$skip={offset}"
        response = _original_get(paged_url)
        data = response.json().get('value', [])
        if not data:
            break
        records.extend(data)
        offset += batch_size
    # To mimic a response object with a json() method:
    class AllResponse:
        def json(self):
            return {"value": records}
    return AllResponse()

def organize_data(data):
    df = pd.DataFrame(data)
    desired_columns = ['transit_timestamp', 'station_complex_id', 'station_complex', 'latitude', 'longitude', 'ridership']
    # Keep only the columns present in the data, in the desired order
    existing = [col for col in desired_columns if col in df.columns]
    df = df[existing]
    # Sort the DataFrame by transit_timestamp if available
    if 'transit_timestamp' in df.columns:
        df.sort_values(by='transit_timestamp', inplace=True)
    # Export the organized DataFrame to CSV
    def save_organized(filename):
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    return save_organized
import json

url = "https://data.ny.gov/api/odata/v4/wujg-7c2s" 

_original_get = requests.get
def new_get(url, *args, **kwargs):
    resp = _original_get(url, *args, **kwargs)
    if '$top' in url:
        try:
            data = resp.json().get('value', [])
            # Only include records with transit_timestamp after December 31, 2022
            filtered_data = [
                record for record in data
                if pd.to_datetime(record['transit_timestamp']) > pd.Timestamp('2022-12-31')
            ]
            resp._content = json.dumps({'value': filtered_data}).encode('utf-8')
        except Exception:
            pass
    return resp
requests.get = new_get



def generate_filename():
    eastern = pytz.timezone('US/Eastern')
    now_est = datetime.now(eastern)
    timestamp = now_est.strftime('%m-%d-%Y_%H-%M-%S')
    return f"MTA_Data_Analysis{timestamp}.csv"

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
if __name__ == "__main__":
    response = get_all_records(url)
    data = response.json().get("value", [])
    filename = generate_filename()
    save_organized = organize_data(data)
    save_organized(filename)
