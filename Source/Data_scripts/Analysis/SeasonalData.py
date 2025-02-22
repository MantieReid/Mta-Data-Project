import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import io

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

def get_top_stations_data(seasonal_ridership, top_n=5):
    """Convert seasonal ridership dictionary to DataFrame and get top N stations."""
    df = pd.DataFrame.from_dict(seasonal_ridership, orient='index')
    total_ridership = df.sum(axis=1)
    top_stations = total_ridership.nlargest(top_n).index
    return df.loc[top_stations]

def create_seasonal_comparison_chart(results_2023, results_2024):
    """Creates a vertical bar chart comparing seasonal ridership between 2023 and 2024"""
    # Convert the dictionaries to DataFrames and get the total ridership for each season
    df_2023 = pd.DataFrame.from_dict(results_2023, orient='index').sum()
    df_2024 = pd.DataFrame.from_dict(results_2024, orient='index').sum()
    
    # Set up the data for plotting
    seasons = ['Winter', 'Spring', 'Summer', 'Fall']
    width = 0.35  # width of the bars
    
    # Create positions for the bars
    x = np.arange(len(seasons))
    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create the bars
    rects1 = ax.bar(x - width/2, df_2023, width, label='2023', color='#8884d8')
    rects2 = ax.bar(x + width/2, df_2024, width, label='2024', color='#82ca9d')
    
    # Customize the plot
    ax.set_title('Seasonal Ridership Comparison (2023 vs 2024)', pad=20)
    ax.set_xlabel('Season')
    ax.set_ylabel('Total Ridership')
    ax.set_xticks(x)
    ax.set_xticklabels(seasons)
    ax.legend()
    
    # Add gridlines
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on top of each bar
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:,.0f}',
                       xy=(rect.get_x() + rect.get_width() / 2, height),
                       xytext=(0, 3),  # 3 points vertical offset
                       textcoords="offset points",
                       ha='center', va='bottom', rotation=0)
    
    autolabel(rects1)
    autolabel(rects2)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig

def create_top_stations_comparison_chart(data_2023, data_2024):
    """Create horizontal bar chart comparing seasonal ridership for top stations."""
    # Set up the plot with increased height for even more spacing
    fig, ax = plt.subplots(figsize=(15, 20))  
    
    # Define colors for each year and season
    colors_2023 = ['#94a3b8', '#86efac', '#fde047', '#fb923c']  # lighter colors for 2023
    colors_2024 = ['#475569', '#16a34a', '#ca8a04', '#ea580c']  # darker colors for 2024
    
    # Set up positions for the bars with much more spacing
    stations = data_2023.index
    seasons = ['Winter', 'Spring', 'Summer', 'Fall']
    y_pos = np.arange(len(stations)) * 8  # Keep station group spacing
    bar_height = 0.2  # Bar height
    
    # Plot bars for each season with much more spacing
    for i, (season, color_2023, color_2024) in enumerate(zip(seasons, colors_2023, colors_2024)):
        # Calculate positions with much more space between season groups and year pairs
        pos_2023 = y_pos - bar_height * 6 + (i * bar_height * 5)  # Increased multiplier for seasonal spacing
        pos_2024 = y_pos - bar_height * 3 + (i * bar_height * 5)  # Matched seasonal spacing multiplier
        
        # 2023 bars
        bars_2023 = ax.barh(pos_2023, data_2023[season], height=bar_height, 
                           label=f'{season} 2023', color=color_2023)
        
        # 2024 bars
        bars_2024 = ax.barh(pos_2024, data_2024[season], height=bar_height,
                           label=f'{season} 2024', color=color_2024)
        
        # Add value labels only at the end of bars
        for j, (value_2023, value_2024) in enumerate(zip(data_2023[season], data_2024[season])):
            # Calculate offset based on maximum value
            offset = max(data_2023.max().max(), data_2024.max().max()) * 0.01
            
            # Only add labels at the end of bars
            ax.text(value_2023 + offset, pos_2023[j], f'{value_2023:,.0f}',
                   va='center', ha='left', fontsize=10)
            ax.text(value_2024 + offset, pos_2024[j], f'{value_2024:,.0f}',
                   va='center', ha='left', fontsize=10)

    # Customize the plot
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stations, fontsize=11)
    ax.invert_yaxis()
    
    # Add title and labels
    plt.title('Top 5 Stations Seasonal Ridership Comparison (2023-2024)', pad=20, fontsize=14)
    plt.xlabel('Ridership', fontsize=12)
    
    # Add gridlines
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Adjust legend position and size
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
    
    # Adjust layout to prevent cutoff
    plt.tight_layout()
    
    return fig

def save_results_to_excel(results_2023, results_2024, output_path):
    """Saves the seasonal ridership results and charts to an Excel file."""
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # Save 2023 data
        df_results_2023 = pd.DataFrame.from_dict(results_2023, orient='index').reset_index()
        df_results_2023.columns = ['Station', 'Winter', 'Spring', 'Summer', 'Fall']
        df_results_2023.to_excel(writer, sheet_name='Ridership_2023', index=False)
        
        # Save 2024 data
        df_results_2024 = pd.DataFrame.from_dict(results_2024, orient='index').reset_index()
        df_results_2024.columns = ['Station', 'Winter', 'Spring', 'Summer', 'Fall']
        df_results_2024.to_excel(writer, sheet_name='Ridership_2024', index=False)
        
        # Save comparison data
        df_comparison = pd.DataFrame({
            '2023': df_results_2023.sum(numeric_only=True),
            '2024': df_results_2024.sum(numeric_only=True)
        })
        df_comparison.to_excel(writer, sheet_name='Comparison', index=True)
        
        # Get top 5 stations data
        top_stations_2023 = get_top_stations_data(results_2023)
        top_stations_2024 = get_top_stations_data(results_2024)
        
        # Create and save the overall comparison chart
        workbook = writer.book
        worksheet = workbook.add_worksheet('Overall_Chart')
        
        fig_overall = create_seasonal_comparison_chart(results_2023, results_2024)
        imgdata_overall = io.BytesIO()
        fig_overall.savefig(imgdata_overall, format='png', dpi=300, bbox_inches='tight')
        plt.close(fig_overall)
        
        worksheet.insert_image('B2', '', {'image_data': imgdata_overall})
        
        # Create and save the top stations chart
        worksheet_top = workbook.add_worksheet('Top_Stations_Chart')
        
        fig_top = create_top_stations_comparison_chart(top_stations_2023, top_stations_2024)
        imgdata_top = io.BytesIO()
        fig_top.savefig(imgdata_top, format='png', dpi=300, bbox_inches='tight')
        plt.close(fig_top)
        
        worksheet_top.insert_image('B2', '', {'image_data': imgdata_top})
        
        # Adjust column widths for better visibility
        for worksheet in [worksheet, worksheet_top]:
            worksheet.set_column('A:A', 2)
            worksheet.set_column('B:B', 120)
            worksheet.set_row(0, 20)

def main():
    """Main function to execute seasonal ridership calculations and create visualizations."""
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Data", "Raw")
    file_path = os.path.join(input_dir, "MTA_Subway_Hourly_Ridership__2020-2024.csv")  # Ensure correct file name
    output_path = os.path.join(input_dir, "Seasonal_Ridership_by_Station.xlsx")
    
    results_2023 = calculate_seasonal_ridership_by_station(file_path, 2023)
    results_2024 = calculate_seasonal_ridership_by_station(file_path, 2024)
    
    save_results_to_excel(results_2023, results_2024, output_path)
    
    print("Results and charts saved to:", output_path)

if __name__ == "__main__":
    main()