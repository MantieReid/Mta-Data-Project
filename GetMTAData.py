import requests
import csv

# API URL
url = "https://data.ny.gov/resource/wujg-7c2s.csv?$limit=50000"

# Fetch data from the API
response = requests.get(url)
response.raise_for_status()  # Check if the request was successful

# Save the data to a CSV file
with open('data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    offset = 0
    limit = 50000
    while True:
        paginated_url = f"{url}&$offset={offset}"
        print(f"Fetching data from: {paginated_url}")
        response = requests.get(paginated_url)
        response.raise_for_status()
        lines = response.iter_lines(decode_unicode=True)
        if offset == 0:
            writer.writerow(next(lines).split(','))  # Write header only once
        row_count = 0
        for line in lines:
            writer.writerow(line.split(','))
            row_count += 1
        print(f"Fetched {row_count} rows")
        if row_count < limit:
            break
        offset += limit
        print(f"Offset updated to: {offset}")

print("Data has been successfully saved to data.csv")