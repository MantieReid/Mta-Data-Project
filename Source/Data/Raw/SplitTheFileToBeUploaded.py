import pandas as pd
import os

# Define file paths
script_dir = os.path.dirname(os.path.realpath(__file__))
input_file = os.path.join(script_dir, "MTASubwayHourlyRidership20202024.csv")  # Replace with your large CSV file
output_prefix = "split_mta_data_"   # Prefix for the split files
chunk_size = 500000  # Number of rows per split file (adjust as needed)

# Read and split the large CSV file
for i, chunk in enumerate(pd.read_csv(input_file, chunksize=chunk_size)):
    output_file = f"{output_prefix}{i+1}.csv"
    chunk.to_csv(output_file, index=False)
    print(f"Saved {output_file} with {len(chunk)} rows.")

print("Splitting complete!")
