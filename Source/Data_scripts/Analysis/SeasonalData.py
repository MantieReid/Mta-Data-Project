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

def calculate_seasonal_ridership(file_path, chunk_size=500000):
    """Processes the CSV file in chunks and calculates total ridership per season for 2023."""
    seasonal_ridership = {'Winter': 0, 'Spring': 0, 'Summer': 0, 'Fall': 0}
    
    # Read CSV in chunks to optimize performance
    for chunk in pd.read_csv(file_path, usecols=['transit_timestamp', 'ridership'], parse_dates=['transit_timestamp'], chunksize=chunk_size):
        # Extract year and month
        chunk['year'] = chunk['transit_timestamp'].dt.year
        chunk['month'] = chunk['transit_timestamp'].dt.month
        
        # Filter only for the year 2023
        chunk = chunk[chunk['year'] == 2023]
        
        # Map each month to a season
        chunk['season'] = chunk['month'].apply(get_season)
        
        # Aggregate ridership per season
        season_totals = chunk.groupby('season')['ridership'].sum()
        
        # Update main dictionary
        for season, total in season_totals.items():
            seasonal_ridership[season] += total
    
    return seasonal_ridership

def save_results_to_excel(results, output_path):
    """Saves the seasonal ridership results to an Excel file."""
    df_results = pd.DataFrame(list(results.items()), columns=['Season', 'Total Ridership'])
    df_results.to_excel(output_path, index=False)

def main():
    """Main function to execute seasonal ridership calculations."""
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Data", "Raw")
    file_path = os.path.join(input_dir, "MTA_Subway_Hourly_Ridership__2020-2024.csv")  # Ensure correct file name
    output_path = os.path.join(input_dir, "Seasonal_Ridership_2023.xlsx")
    
    results = calculate_seasonal_ridership(file_path)
    save_results_to_excel(results, output_path)
    
    print("Total Ridership by Season in 2023 saved to:", output_path)
    for season, total in results.items():
        print(f"{season}: {total:,}")

if __name__ == "__main__":
    main()
