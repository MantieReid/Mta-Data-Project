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
    
    # Convert years to strings for filtering
    year_strings = [str(year) for year in years_to_analyze]
    
    # Define the columns we need - this reduces memory by loading only necessary columns
    usecols = ['transit_timestamp', 'station_complex_id', 'station_complex', 
               'ridership']
    
    # Create a parser function to efficiently extract year without loading entire timestamp
    def parse_timestamp(x):
        try:
            dt = datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
            return dt
        except (ValueError, TypeError):
            return pd.NaT
    
    print(f"Loading and processing data from {file_path} in chunks...")
    
    # Process the file in chunks
    for chunk_num, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, usecols=usecols)):
        if chunk_num % 10 == 0:
            print(f"Processing chunk {chunk_num}...")
        
        # Filter rows by year before processing to reduce memory usage
        # This pre-filtering can drastically reduce the amount of data we need to process
        chunk['transit_timestamp'] = pd.to_datetime(chunk['transit_timestamp'], errors='coerce')
        chunk.dropna(subset=['transit_timestamp'], inplace=True)
        
        # Extract year and hour
        chunk['year'] = chunk['transit_timestamp'].dt.year
        chunk['hour'] = chunk['transit_timestamp'].dt.hour
        
        # Filter for relevant years
        for year in years_to_analyze:
            year_chunk = chunk[chunk['year'] == year]
            
            if not year_chunk.empty:
                # Group by required columns and calculate sum and count
                grouped = year_chunk.groupby([
                    'station_complex_id', 
                    'station_complex', 
                    'hour', 
                ])['ridership'].agg(['sum', 'count']).reset_index()
                
                # Process each group
                for _, row in grouped.iterrows():
                    key = (row['station_complex_id'], row['station_complex'], 
                           row['hour'])
                    
                    if key in year_sums[year]:
                        year_sums[year][key] += row['sum']
                        year_counts[year][key] += row['count']
                    else:
                        year_sums[year][key] = row['sum']
                        year_counts[year][key] = row['count']
        
        # Explicitly delete chunk to free memory
        del chunk
        gc.collect()
    
    # Calculate averages and create final dataframes
    result = {}
    for year in years_to_analyze:
        rows = []
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
        
        result[year] = pd.DataFrame(rows)
        
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
    
    # Years to analyze
    years_to_analyze = [2023, 2024]
    
    # Process data in chunks and calculate average ridership
    avg_ridership = process_data_in_chunks(file_path, years_to_analyze)
    
    # Save results
    print("Saving results...")
    saved_files = save_results(avg_ridership)
    
    # Display the results
    for filename in saved_files:
        print(f"Average ridership saved to {filename}")


if __name__ == "__main__":
    main()