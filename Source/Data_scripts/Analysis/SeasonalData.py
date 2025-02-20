import pandas as pd
import os

def get_season(month):
    """Returns the season based on the month number."""
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    elif month in [9, 10, 11]:
        return 'Fall'

def calculate_seasonal_ridership_by_station(file_path, year, chunk_size=500000):
    """Processes the CSV file in chunks and calculates total ridership per season for each station in a given year."""
    seasonal_ridership = {}
    
    # Read CSV in chunks to optimize performance
    for chunk in pd.read_csv(file_path, usecols=['transit_timestamp', 'ridership', 'station_complex'], parse_dates=['transit_timestamp'], chunksize=chunk_size):
        # Extract year and month
        chunk['year'] = chunk['transit_timestamp'].dt.year
        chunk['month'] = chunk['transit_timestamp'].dt.month
        
        # Filter only for the specified year
        chunk = chunk[chunk['year'] == year]
        
        # Map each month to a season
        chunk['season'] = chunk['month'].apply(get_season)
        
        # Aggregate ridership per season per station
        season_totals = chunk.groupby(['station_complex', 'season'])['ridership'].sum().reset_index()
        
        # Update main dictionary
        for _, row in season_totals.iterrows():
            station = row['station_complex']
            season = row['season']
            ridership = row['ridership']
            
            if station not in seasonal_ridership:
                seasonal_ridership[station] = {'Winter': 0, 'Spring': 0, 'Summer': 0, 'Fall': 0}
            
            seasonal_ridership[station][season] += ridership
    
    return seasonal_ridership

def save_results_to_excel(results_2023, results_2024, output_path):
    """Saves the seasonal ridership results for each station for 2023 and 2024 to an Excel file in separate sheets."""
    with pd.ExcelWriter(output_path) as writer:
        df_results_2023 = pd.DataFrame.from_dict(results_2023, orient='index').reset_index()
        df_results_2023.columns = ['Station', 'Winter', 'Spring', 'Summer', 'Fall']
        df_results_2023.to_excel(writer, sheet_name='Ridership_2023', index=False)
        
        df_results_2024 = pd.DataFrame.from_dict(results_2024, orient='index').reset_index()
        df_results_2024.columns = ['Station', 'Winter', 'Spring', 'Summer', 'Fall']
        df_results_2024.to_excel(writer, sheet_name='Ridership_2024', index=False)

def main():
    """Main function to execute seasonal ridership calculations."""
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Data", "Raw")
    file_path = os.path.join(input_dir, "MTA_Subway_Hourly_Ridership__2020-2024.csv")  # Ensure correct file name
    output_path = os.path.join(input_dir, "Seasonal_Ridership_by_Station.xlsx")
    
    results_2023 = calculate_seasonal_ridership_by_station(file_path, 2023)
    results_2024 = calculate_seasonal_ridership_by_station(file_path, 2024)
    save_results_to_excel(results_2023, results_2024, output_path)
    
    print("Total Ridership by Station and Season saved to:", output_path)
    print("2023 Ridership Summary:")
    print(pd.DataFrame.from_dict(results_2023, orient='index').head())
    
    print("\n2024 Ridership Summary:")
    print(pd.DataFrame.from_dict(results_2024, orient='index').head())

if __name__ == "__main__":
    main()




