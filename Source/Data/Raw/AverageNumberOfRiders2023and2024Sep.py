import pandas as pd
import os
import gc


def process_data_in_chunks(file_path, years_to_analyze, chunksize=100000):
    """
    Process the MTA ridership data in chunks to reduce memory usage
    
    Args:
        file_path (str): Path to the CSV file
        years_to_analyze (list): List of years to analyze
        chunksize (int): Number of rows to process at once
        
    Returns:
        dict: Dictionary with years as keys and processed dataframes as values
    """
    try:
        # Initialize results dictionary and row counters
        year_aggregates = {year: {} for year in years_to_analyze}
        row_counts = {year: 0 for year in years_to_analyze}
        
        print(f"Reading data in chunks of {chunksize} rows...")
        
        # Read and process file in chunks
        chunk_count = 0
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            chunk_count += 1
            print(f"Processing chunk {chunk_count}...")
            
            # Check required columns
            required_cols = ["transit_timestamp", "station_complex_id", "station_complex", "ridership"]
            if not all(col in chunk.columns for col in required_cols):
                missing = [col for col in required_cols if col not in chunk.columns]
                print(f"Warning: Missing required columns: {missing}. Skipping chunk.")
                continue
            
            # Extract year directly from timestamp string instead of parsing the full datetime
            # This is faster and more reliable
            try:
                # Extract year using string manipulation (faster than full datetime parsing)
                chunk["year"] = chunk["transit_timestamp"].str.extract(r'(\d{4})').astype(int)
                
                # Extract hour - first try to parse time portion, fallback to full datetime if needed
                try:
                    # Try to extract hour from HH:MM:SS format
                    time_part = chunk["transit_timestamp"].str.extract(r'\d+/\d+/\d+\s+(\d+):\d+:\d+')
                    chunk["hour"] = pd.to_numeric(time_part[0], errors='coerce')
                except:
                    # Fallback to full datetime parsing for hour
                    print("Falling back to datetime parsing for hours...")
                    chunk["transit_timestamp"] = pd.to_datetime(chunk["transit_timestamp"], errors='coerce')
                    chunk = chunk.dropna(subset=["transit_timestamp"])
                    chunk["hour"] = chunk["transit_timestamp"].dt.hour
            except Exception as e:
                print(f"Warning: Error extracting year/hour from timestamps: {str(e)}")
                print("Trying alternative parsing method...")
                try:
                    # Fallback to full datetime parsing
                    chunk["transit_timestamp"] = pd.to_datetime(chunk["transit_timestamp"], errors='coerce')
                    chunk = chunk.dropna(subset=["transit_timestamp"])
                    chunk["year"] = chunk["transit_timestamp"].dt.year
                    chunk["hour"] = chunk["transit_timestamp"].dt.hour
                except Exception as e2:
                    print(f"Error parsing dates: {str(e2)}. Skipping chunk.")
                    continue
            
            # Make sure we have valid numeric data
            try:
                chunk["ridership"] = pd.to_numeric(chunk["ridership"], errors='coerce')
                chunk = chunk.dropna(subset=["ridership", "year", "hour"])
            except Exception as e:
                print(f"Warning: Error converting ridership to numeric: {str(e)}")
                continue
                
            # Filter to relevant years and process each year
            for year in years_to_analyze:
                try:
                    year_chunk = chunk[chunk["year"] == year]
                    
                    if len(year_chunk) > 0:
                        print(f"Found {len(year_chunk)} rows for year {year} in this chunk")
                        
                        # Define required columns for grouping
                        groupby_columns = ["station_complex_id", "station_complex", "hour"]
                        
                        # Group by station and hour and sum ridership
                        grouped = year_chunk.groupby(groupby_columns)["ridership"].agg(['sum', 'count']).reset_index()
                        
                        # Update aggregate dictionary
                        for _, row in grouped.iterrows():
                            # Create a key with just the required columns
                            key = (row["station_complex_id"], row["station_complex"], row["hour"])
                            
                            if key in year_aggregates[year]:
                                year_aggregates[year][key][0] += row["sum"]  # Sum of ridership
                                year_aggregates[year][key][1] += row["count"]  # Count of records
                            else:
                                year_aggregates[year][key] = [row["sum"], row["count"]]
                        
                        # Update count of rows processed for this year
                        row_counts[year] += len(year_chunk)
                except Exception as e:
                    print(f"Error processing data for year {year} in chunk {chunk_count}: {str(e)}")
            
            # Free memory
            del chunk
            gc.collect()
        
        # Calculate averages and convert to dataframes
        result = {}
        for year in years_to_analyze:
            print(f"Processing final results for {year}...")
            print(f"Total rows processed for {year}: {row_counts[year]}")
            print(f"Number of unique station-hour combinations for {year}: {len(year_aggregates[year])}")
            
            if len(year_aggregates[year]) > 0:
                # Convert aggregates to dataframe
                rows = []
                for key, (sum_val, count) in year_aggregates[year].items():
                    avg_ridership = sum_val / count if count > 0 else 0
                    # Create a row dict with only the required columns
                    row_dict = {
                        "station_complex_id": key[0],
                        "station_complex": key[1],
                        "hour": key[2],
                        "ridership": avg_ridership
                    }
                    
                    rows.append(row_dict)
                
                if rows:
                    result[year] = pd.DataFrame(rows)
                    print(f"Created dataframe for {year} with {len(rows)} rows")
                    # Free memory
                    del year_aggregates[year]
                    gc.collect()
            else:
                print(f"No aggregated data found for {year}")
        
        if not result:
            print("No data was processed for any requested years. Check if years exist in the dataset.")
            return {}
            
        return result
    
    except Exception as e:
        print(f"Unexpected error in process_data_in_chunks: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}


def save_results(df_dict, output_dir=None, prefix="avg_ridership"):
    """
    Save dataframes to CSV files in the specified output directory
    
    Args:
        df_dict (dict): Dictionary with years as keys and dataframes as values
        output_dir (str): Directory to save output files, defaults to "Data/Processed" in project root
        prefix (str): Prefix for output filenames
        
    Returns:
        list: List of output filenames
    """
    # If output_dir is not specified, use default path relative to script location
    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels
        output_dir = os.path.join(project_root, "Data", "Processed")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    filenames = []
    for year, df in df_dict.items():
        filename = os.path.join(output_dir, f"{prefix}_{year}.csv")
        df.to_csv(filename, index=False)
        filenames.append(filename)
    return filenames


def main():
    """
    Main function to execute the memory-optimized MTA ridership analysis pipeline
    """
    # Get the absolute path to the input file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels from script location
    file_path = os.path.join(project_root, "Data", "Raw", "MTA_Subway_Hourly_Ridership__2020-2024.csv")
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: Input file not found at {file_path}")
        print("Please check the file path and try again.")
        return
    
    # Years to analyze
    years_to_analyze = [2023, 2024]
    
    # Process data in chunks
    print(f"Starting to process data from {file_path}...")
    avg_ridership = process_data_in_chunks(file_path, years_to_analyze, chunksize=50000)
    
    if not avg_ridership:
        print("No data was found for the requested years. Exiting.")
        return
    
    # Save results
    print("Saving results...")
    saved_files = save_results(avg_ridership)
    
    if saved_files:
        # Display the results
        for filename in saved_files:
            print(f"Average ridership saved to {filename}")
        
        print("Processing complete!")
    else:
        print("No output files were created. Check if the data contains the requested years.")



if __name__ == "__main__":
    main()