import pandas as pd
import os
import gc
from datetime import datetime


def process_data_in_chunks(file_path, years_to_analyze, chunk_size=100000):
    """
    Process the MTA ridership data in chunks to reduce memory usage
    
    Args:
        file_path (str): Path to the CSV file
        years_to_analyze (list): List of years to extract
        chunk_size (int): Number of rows to process at once
        
    Returns:
        dict: Dictionary with years as keys and processed dataframes as values
    """
    # Initialize dictionaries to store results
    year_sums = {year: {} for year in years_to_analyze}
    year_counts = {year: {} for year in years_to_analyze}
    
    # Define the columns we need - this reduces memory by loading only necessary columns
    usecols = ['transit_timestamp', 'station_complex_id', 'station_complex', 
               'ridership']
    
    print(f"Loading and processing data from {file_path} in chunks...")
    
    # Read a sample to inspect the data
    sample = pd.read_csv(file_path, nrows=5)
    print("Sample data:")
    print(sample[usecols].head() if all(col in sample.columns for col in usecols) else "Missing required columns")
    
    # Check if required columns exist
    missing_cols = [col for col in usecols if col not in sample.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        print(f"Available columns: {sample.columns.tolist()}")
        return {}
    
    # Check timestamp format from sample
    if 'transit_timestamp' in sample.columns and len(sample) > 0:
        sample_timestamp = sample['transit_timestamp'].iloc[0]
        print(f"Sample timestamp: {sample_timestamp}")
        
        # Try to determine timestamp format
        formats_to_try = ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S']
        for fmt in formats_to_try:
            try:
                datetime.strptime(sample_timestamp, fmt)
                print(f"Detected timestamp format: {fmt}")
                detected_format = fmt
                break
            except ValueError:
                continue
        else:
            print("Warning: Could not determine timestamp format")
            detected_format = None
    
    # Process the file in chunks
    rows_processed = 0
    rows_matching_years = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, usecols=usecols)):
        if chunk_num % 10 == 0:
            print(f"Processing chunk {chunk_num}...")
        
        if chunk_num == 0:
            # Print sample of first chunk for debugging
            print("\nFirst 5 rows of first chunk:")
            print(chunk.head())
            print(f"\nData types: {chunk.dtypes}")
        
        # Clean data
        # Ensure ridership is numeric
        chunk['ridership'] = pd.to_numeric(chunk['ridership'], errors='coerce')
        
        # Convert timestamp to datetime 
        if detected_format:
            # Try with detected format first
            try:
                chunk['transit_timestamp'] = pd.to_datetime(chunk['transit_timestamp'], 
                                                          format=detected_format, 
                                                          errors='coerce')
            except Exception as e:
                print(f"Warning: Error parsing timestamps with detected format: {e}")
                # Fall back to automatic detection
                chunk['transit_timestamp'] = pd.to_datetime(chunk['transit_timestamp'], errors='coerce')
        else:
            # No format detected, use automatic detection
            chunk['transit_timestamp'] = pd.to_datetime(chunk['transit_timestamp'], errors='coerce')
        
        # Drop rows with invalid timestamps
        valid_timestamps = chunk['transit_timestamp'].notna().sum()
        if chunk_num == 0:
            print(f"Valid timestamps in first chunk: {valid_timestamps} of {len(chunk)}")
        
        chunk = chunk.dropna(subset=['transit_timestamp'])
        
        # Extract year and hour from timestamp
        chunk['year'] = chunk['transit_timestamp'].dt.year
        chunk['hour'] = chunk['transit_timestamp'].dt.hour
        
        if chunk_num == 0:
            # Check if there's data for our target years
            years_present = chunk['year'].unique()
            print(f"Years present in first chunk: {years_present}")
            # Check if any of our target years are present
            target_years_present = [y for y in years_to_analyze if y in years_present]
            print(f"Target years present: {target_years_present}")
            
            if not target_years_present:
                print("Warning: None of the target years are present in the first chunk!")
                print("Consider changing years_to_analyze to match the data")
        
        rows_processed += len(chunk)
        
        # Filter for relevant years
        for year in years_to_analyze:
            year_chunk = chunk[chunk['year'] == year]
            
            if chunk_num % 10 == 0:
                print(f"Chunk {chunk_num}: Found {len(year_chunk)} rows for year {year}")
            
            rows_matching_years += len(year_chunk)
            
            if not year_chunk.empty:
                # Group by required columns and calculate sum and count
                grouped = year_chunk.groupby([
                    'station_complex_id', 
                    'station_complex', 
                    'hour'
                ])['ridership'].agg(['sum', 'count']).reset_index()
                
                # Process each group
                for _, row in grouped.iterrows():
                    key = (row['station_complex_id'], row['station_complex'], row['hour'])
                    
                    if key in year_sums[year]:
                        year_sums[year][key] += row['sum']
                        year_counts[year][key] += row['count']
                    else:
                        year_sums[year][key] = row['sum']
                        year_counts[year][key] = row['count']
        
        # Explicitly delete chunk to free memory
        del chunk
        gc.collect()
    
    print(f"\nProcessed {rows_processed} total rows")
    print(f"Found {rows_matching_years} rows matching target years {years_to_analyze}")
    
    # Calculate averages and create final dataframes
    result = {}
    for year in years_to_analyze:
        rows = []
        key_count = len(year_sums[year])
        print(f"Creating dataframe for year {year} with {key_count} station/hour combinations")
        
        for key, total in year_sums[year].items():
            count = year_counts[year][key]
            avg = total / count if count > 0 else 0
            station_id, station_name, hour = key
            rows.append({
                'station_complex_id': station_id,
                'station_complex': station_name,
                'hour': hour,
                'ridership': avg
            })
        
        if rows:
            result[year] = pd.DataFrame(rows)
            print(f"Created dataframe for year {year} with {len(rows)} rows")
        else:
            print(f"Warning: No data found for year {year}")
            result[year] = pd.DataFrame(columns=['station_complex_id', 'station_complex', 'hour', 'ridership'])
        
        # Clear dictionaries to free memory
        year_sums[year].clear()
        year_counts[year].clear()
    
    return result


def save_results(df_dict, prefix="avg_ridership"):
    """
    Save dataframes to CSV files
    
    Args:
        df_dict (dict): Dictionary with years as keys and dataframes as values
        prefix (str): Prefix for output filenames
        
    Returns:
        list: List of output filenames
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path_output = os.path.join(base_dir, "Data", "reports")
    
    if not os.path.exists(file_path_output):
        os.makedirs(file_path_output)
    filenames = []
    # Create a list of years to safely iterate over
    years = list(df_dict.keys())
    
    for year in years:
        df = df_dict[year]
        filename = os.path.join(file_path_output, f"{prefix}_{year}.csv")
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} rows to {filename}")
        filenames.append(filename)
        
        # Delete dataframe after saving to free memory
        del df_dict[year]
        gc.collect()
        
    return filenames


def main():
    """
    Main function to execute the MTA ridership analysis pipeline
    """
    # File path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path = os.path.join(base_dir, "Data", "Raw", "MTA_Subway_Hourly_Ridership__2020-2024.csv")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        # Try the first_month1c.csv file as an alternative
        alt_file_path = os.path.join(base_dir, "Data", "Raw", "first_month1c.csv")
        if os.path.exists(alt_file_path):
            print(f"Trying alternative file: {alt_file_path}")
            file_path = alt_file_path
        else:
            print("Alternative file not found either. Please check file paths.")
            return
    
    # Years to analyze
    years_to_analyze = [2023, 2024]
    
    print(f"Looking for data from years: {years_to_analyze}")
    
    # Process data in chunks and calculate average ridership
    avg_ridership = process_data_in_chunks(file_path, years_to_analyze)
    
    if not avg_ridership:
        print("Error: No data processed, check previous messages for details")
        return
    
    # Save results
    print("Saving results...")
    saved_files = save_results(avg_ridership)
    
    # Display the results
    for filename in saved_files:
        print(f"Average ridership saved to {filename}")


if __name__ == "__main__":
    main()