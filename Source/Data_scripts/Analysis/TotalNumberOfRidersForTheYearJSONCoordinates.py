import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as ticker
from datetime import datetime
import json
import numpy as np

# Add watermark text constant
WATERMARK_TEXT = "Mantie Reid II"

def get_unique_filename(base_path):
    print("Checking if file exists...")
    """Generate a unique filename by adding a number if the file exists."""
    directory = base_path.parent
    stem = base_path.stem
    suffix = base_path.suffix
    
    counter = 1
    new_path = base_path
    while new_path.exists():
        new_path = directory / f"{stem}_{counter}{suffix}"
        counter += 1
    print(f"Unique filename generated: {new_path}")
    return new_path

def define_paths():
    print("🚀 Starting the process...")
    # Get current date and time
    current_time = datetime.now()
    date_time_str = current_time.strftime("%B %d, %Y %I-%M %p")
    
    base_dir = Path(__file__).resolve().parents[3]
    input_dir = base_dir / "Source" / "Data" / "Raw"
    file_path = input_dir / "MTA_Subway_Hourly_Ridership__2020-2024.csv"
    output_dir = base_dir / "Source" / "Data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename with date and time
    base_filename = f"MTA_Station_Ridership_Yearly_Analysis_For_2023_and_2024{date_time_str}.xlsx"
    output_file = output_dir / base_filename
    
    # Get unique filename if file already exists
    output_file = get_unique_filename(output_file)

    if not file_path.exists():
        raise FileNotFoundError(f"🚨 File not found: {file_path}")

    return file_path, output_file, output_dir, current_time

def load_data(file_path, chunksize=100000):
    print(f"📊 Loading data from: {file_path}")
    date_column = "transit_timestamp"
    ridership_column = "ridership"
    station_column = "station_complex"
    
    # Geographic columns
    lat_column = "latitude"
    lon_column = "longitude"
    georef_column = "georeference"
    borough_column = "borough"
    
    date_format = '%m/%d/%Y %I:%M:%S %p'

    total_ridership_per_year = {}
    stations_2023 = {}
    stations_2024 = {}
    
    # Store geo data for each station
    station_geo_data = {}
    
    # First read a small chunk to check available columns
    first_chunk = pd.read_csv(file_path, nrows=5)
    available_columns = first_chunk.columns.tolist()
    
    # Check which geo columns are available
    geo_columns = [station_column]
    if lat_column in available_columns:
        geo_columns.append(lat_column)
    if lon_column in available_columns:
        geo_columns.append(lon_column)
    if georef_column in available_columns:
        geo_columns.append(georef_column)
    if borough_column in available_columns:
        geo_columns.append(borough_column)
    
    print(f"Available geo columns: {geo_columns}")

    for chunk in pd.read_csv(
        file_path, 
        chunksize=chunksize, 
        parse_dates=[date_column],
        date_format=date_format,
        low_memory=False
    ):
        chunk["year"] = chunk[date_column].dt.year
        yearly_ridership = chunk.groupby("year")[ridership_column].sum()
        for year, ridership in yearly_ridership.items():
            total_ridership_per_year[year] = total_ridership_per_year.get(year, 0) + ridership

        # Process 2023 data
        stations_2023_chunk = chunk[chunk["year"] == 2023].groupby(station_column)[ridership_column].sum()
        for station, ridership in stations_2023_chunk.items():
            stations_2023[station] = stations_2023.get(station, 0) + ridership

        # Process 2024 data
        stations_2024_chunk = chunk[chunk["year"] == 2024].groupby(station_column)[ridership_column].sum()
        for station, ridership in stations_2024_chunk.items():
            stations_2024[station] = stations_2024.get(station, 0) + ridership

        # Collect geo data for each station - only use available columns
        station_geo_chunk = chunk[geo_columns].drop_duplicates(subset=[station_column])
        for _, row in station_geo_chunk.iterrows():
            station = row[station_column]
            if station not in station_geo_data:
                station_data = {"station_complex": station}
                
                # Add available geo data
                if lat_column in geo_columns:
                    station_data["latitude"] = row[lat_column]
                if lon_column in geo_columns:
                    station_data["longitude"] = row[lon_column]
                if georef_column in geo_columns:
                    station_data["georeference"] = row[georef_column]
                if borough_column in geo_columns:
                    station_data["borough"] = row[borough_column]
                
                station_geo_data[station] = station_data

    return total_ridership_per_year, stations_2023, stations_2024, station_geo_data

def process_data(total_ridership_per_year, stations_2023, stations_2024, station_geo_data):
    print("📈 Processing data...")
    official_ridership_2023 = total_ridership_per_year.get(2023, 0)
    official_ridership_2024 = total_ridership_per_year.get(2024, 0)

    print(f"✅ Total Subway Ridership in 2023: {official_ridership_2023:,}")
    print(f"✅ Total Subway Ridership in 2024: {official_ridership_2024:,}")

    # Convert to DataFrames
    stations_2023 = pd.DataFrame(list(stations_2023.items()), columns=["station_complex", "ridership"])
    stations_2024 = pd.DataFrame(list(stations_2024.items()), columns=["station_complex", "ridership"])

    # Calculate percentages
    stations_2023["percentage"] = (stations_2023["ridership"] / official_ridership_2023) if official_ridership_2023 > 0 else 0
    stations_2024["percentage"] = (stations_2024["ridership"] / official_ridership_2024) if official_ridership_2024 > 0 else 0

    # Add geo data to DataFrames
    for df in [stations_2023, stations_2024]:
        # Dynamically add available geo fields from station_geo_data
        for station_idx, row in df.iterrows():
            station = row["station_complex"]
            if station in station_geo_data:
                # Get all available fields for this station
                geo_info = station_geo_data[station]
                for field, value in geo_info.items():
                    if field != "station_complex":  # Skip the key field
                        # Add column if it doesn't exist
                        if field not in df.columns:
                            df[field] = None
                        # Set the value for this station
                        df.at[station_idx, field] = value

    # Keep ridership as numeric values
    top5_2023 = stations_2023.sort_values(by="ridership", ascending=False).head(15)
    top5_2024 = stations_2024.sort_values(by="ridership", ascending=False).head(15)
    top10_2023 = stations_2023.sort_values(by="ridership", ascending=False).head(10)
    top10_2024 = stations_2024.sort_values(by="ridership", ascending=False).head(10)

    return stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024

def write_to_excel(output_file, stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024, output_dir, file_path, ridership_column, current_time, chunksize=100000, date_column="transit_timestamp", date_format='%m/%d/%Y %I:%M:%S %p'):
    print(f"📝 Writing data to Excel file: {output_file}")
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        workbook = writer.book
        
        # Create a number format with commas
        number_format = workbook.add_format({'num_format': '#,##0'})
        percent_format = workbook.add_format({'num_format': '0.00%'})

        def write_as_table(df, sheet_name, writer, use_color=False):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            end_row = len(df)
            end_col = len(df.columns) - 1
            table_range = f'A1:{chr(65 + end_col)}{end_row + 1}'
            
            # Define column formats
            columns = []
            for col in df.columns:
                if col == "station_complex":
                    columns.append({'header': col})
                elif col == "percentage":
                    columns.append({'header': col, 'format': percent_format})
                elif col in ["ridership"]:
                    columns.append({'header': col, 'format': number_format})
                else:
                    columns.append({'header': col})

            table_style = 'Table Style Medium 2' if not use_color else 'Table Style Medium 4'
            worksheet.add_table(table_range, {
                'columns': columns,
                'style': table_style,
                'first_column': True
            })

            # Set column widths and formats
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                if col == "ridership":
                    worksheet.set_column(idx, idx, max_length + 2, number_format)
                elif col == "percentage":
                    worksheet.set_column(idx, idx, max_length + 2, percent_format)
                else:
                    worksheet.set_column(idx, idx, max_length + 2)

        write_as_table(stations_2023, "2023 Ridership", writer)
        write_as_table(stations_2024, "2024 Ridership", writer)
        write_as_table(top5_2023, "Top 5 Stations 2023", writer, use_color=True)
        write_as_table(top5_2024, "Top 5 Stations 2024", writer, use_color=True)

        fig, ax = plt.subplots(figsize=(12, 8))
        top10_2023_plot = top10_2023.copy()
        top10_2024_plot = top10_2024.copy()

        bar_height = 0.35
        y_pos = range(len(top10_2023_plot))
        ax.barh([i + bar_height for i in y_pos], 
                top10_2023_plot["ridership"], 
                height=bar_height,
                label="2023",
                color="#1f77b4",
                alpha=0.8)
        
        ax.barh([i for i in y_pos], 
                top10_2024_plot["ridership"], 
                height=bar_height,
                label="2024",
                color="#d62728",
                alpha=0.8)
        
        def format_with_commas(x, p):
            return f"{x:,.0f}"

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_with_commas))
        ax.set_xlabel("Ridership", fontsize=10, fontweight='bold')
        ax.set_ylabel("Station Complex", fontsize=10, fontweight='bold')
        ax.set_title("Top 10 Subway Stations Ridership Comparison (2023 vs 2024)", 
                    fontsize=12, 
                    fontweight='bold', 
                    pad=20)
       
        ax.set_yticks([i + bar_height/2 for i in y_pos])
        ax.set_yticklabels(top10_2023_plot["station_complex"], fontsize=9)
        ax.grid(True, axis='x', linestyle='--', alpha=0.3)

        ax.legend(bbox_to_anchor=(1.02, 1),
                 loc='upper left',
                 ncol=1,
                 fontsize=10,
                 borderaxespad=0)
                 
        # Add watermark with your name - positioned in center with very low opacity
        plt.figtext(0.5, 0.5, WATERMARK_TEXT, ha='center', va='center', 
                   color='gray', alpha=0.15, fontsize=24, 
                   rotation=30, transform=ax.transAxes)

        plt.tight_layout()
        
        chart_path = output_dir / "top_10_ridership_chart.png"
        plt.savefig(chart_path, bbox_inches="tight", dpi=300)
        plt.close(fig)

        hourly_data = pd.Series(0, index=range(24))
        hourly_counts = pd.Series(0, index=range(24))
        for chunk in pd.read_csv(file_path, chunksize=chunksize, parse_dates=[date_column], date_format=date_format, low_memory=False):
            chunk['hour'] = chunk[date_column].dt.hour
            hourly_sum = chunk.groupby('hour')[ridership_column].sum()
            hourly_count = chunk.groupby('hour').size()
            hourly_data = hourly_data.add(hourly_sum, fill_value=0)
            hourly_counts = hourly_counts.add(hourly_count, fill_value=0)

        hourly_data = hourly_data / hourly_counts
        hours = list(range(1, 24)) + [0]
        hourly_data = hourly_data.reindex(hours)

        worksheet_chart = workbook.add_worksheet("Top 10 Chart")
        worksheet_chart.insert_image("B2", str(chart_path))

    # Export data to JSON
    export_to_json(stations_2023, stations_2024, top5_2023, top5_2024, output_dir, current_time)

def convert_nan(obj):
    """Convert NaN values to a serializable format"""
    if isinstance(obj, dict):
        return {k: convert_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_nan(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return convert_nan(obj.tolist())
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj

def export_to_json(stations_2023, stations_2024, top5_2023, top5_2024, output_dir, current_time):
    """Export data to a JSON file with geo coordinates"""
    
    # Create the JSON structure with all required data including geo coordinates
    json_output = {
        "metadata": {
            "generated_at": current_time.isoformat(),
            "description": "MTA Subway Station Ridership Analysis with Geographic Data",
            "creator": WATERMARK_TEXT
        },
        "all_stations": {
            "2023": stations_2023.to_dict(orient='records'),
            "2024": stations_2024.to_dict(orient='records')
        },
        "top_stations": {
            "2023": top5_2023.to_dict(orient='records'),
            "2024": top5_2024.to_dict(orient='records')
        },
        # Add a dedicated geoJSON section for mapping
        "geoJSON": {
            "type": "FeatureCollection",
            "features": []
        }
    }
    
    # Add GeoJSON features for all 2023 stations (can be easily mapped)
    for _, station in stations_2023.iterrows():
        # Check if latitude and longitude columns exist and are not null
        has_coords = (
            "latitude" in station.index and 
            "longitude" in station.index and 
            not pd.isna(station["latitude"]) and 
            not pd.isna(station["longitude"])
        )
        
        if not has_coords:
            # Skip stations without coordinates, but log them
            print(f"Skipping station without coordinates: {station['station_complex']}")
            continue
            
        # Create properties dictionary with all available data
        properties = {"station_name": station["station_complex"]}
        
        # Add all station data to properties
        for col in station.index:
            if col not in ["latitude", "longitude"]:
                properties[f"{col}_2023"] = station[col]
        
        # Add 2024 data if available
        if station["station_complex"] in stations_2024["station_complex"].values:
            station_2024 = stations_2024.loc[stations_2024["station_complex"] == station["station_complex"]].iloc[0]
            for col in station_2024.index:
                if col not in ["station_complex", "latitude", "longitude"]:
                    properties[f"{col}_2024"] = station_2024[col]
        
        # Create the GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(station["longitude"]), float(station["latitude"])]
            },
            "properties": properties
        }
        json_output["geoJSON"]["features"].append(feature)

    # Convert NaN values to None for JSON serialization
    json_output = convert_nan(json_output)

    # Generate JSON file path
    json_filename = f"MTA_Station_Ridership_Analysis_{current_time.strftime('%Y_%m_%d')}.json"
    json_file_path = output_dir / json_filename

    # Save the data to a JSON file
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_output, json_file, indent=2)

    print(f"✅ Enhanced JSON output with geo coordinates saved to: {json_file_path}")

def main():
    file_path, output_file, output_dir, current_time = define_paths()
    total_ridership_per_year, stations_2023, stations_2024, station_geo_data = load_data(file_path)
    stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024 = process_data(
        total_ridership_per_year, stations_2023, stations_2024, station_geo_data
    )
    write_to_excel(output_file, stations_2023, stations_2024, top5_2023, top5_2024, 
                  top10_2023, top10_2024, output_dir, file_path, "ridership", current_time)

if __name__ == "__main__":
    main()