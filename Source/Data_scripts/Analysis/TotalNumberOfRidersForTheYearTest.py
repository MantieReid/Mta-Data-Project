import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as ticker

def define_paths():
    base_dir = Path(__file__).resolve().parents[3]
    input_dir = base_dir / "Source" / "Data" / "Raw"
    file_path = input_dir / "MTA_Subway_Hourly_Ridership__2020-2024.csv"
    output_dir = base_dir / "Source" / "Data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "MTA_Station_Ridership_Analysis.xlsx"

    if not file_path.exists():
        raise FileNotFoundError(f"🚨 File not found: {file_path}")

    return file_path, output_file, output_dir

def load_data(file_path, chunksize=100000):
    date_column = "transit_timestamp"
    ridership_column = "ridership"
    station_column = "station_complex"
    date_format = '%m/%d/%Y %I:%M:%S %p'

    total_ridership_per_year = {}
    stations_2023 = {}
    stations_2024 = {}

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

        stations_2023_chunk = chunk[chunk["year"] == 2023].groupby(station_column)[ridership_column].sum()
        for station, ridership in stations_2023_chunk.items():
            stations_2023[station] = stations_2023.get(station, 0) + ridership

        stations_2024_chunk = chunk[chunk["year"] == 2024].groupby(station_column)[ridership_column].sum()
        for station, ridership in stations_2024_chunk.items():
            stations_2024[station] = stations_2024.get(station, 0) + ridership

    return total_ridership_per_year, stations_2023, stations_2024

def process_data(total_ridership_per_year, stations_2023, stations_2024):
    official_ridership_2023 = total_ridership_per_year.get(2023, 0)
    official_ridership_2024 = total_ridership_per_year.get(2024, 0)

    print(f"✅ Total Subway Ridership in 2023: {official_ridership_2023:,}")
    print(f"✅ Total Subway Ridership in 2024: {official_ridership_2024:,}")

    stations_2023 = pd.DataFrame(list(stations_2023.items()), columns=["station_complex", "ridership"])
    stations_2024 = pd.DataFrame(list(stations_2024.items()), columns=["station_complex", "ridership"])

    stations_2023["percentage"] = (stations_2023["ridership"] / official_ridership_2023) * 100 if official_ridership_2023 > 0 else 0
    stations_2024["percentage"] = (stations_2024["ridership"] / official_ridership_2024) * 100 if official_ridership_2024 > 0 else 0

    stations_2023["ridership"] = stations_2023["ridership"].apply(lambda x: '{:,.0f}'.format(x))
    stations_2024["ridership"] = stations_2024["ridership"].apply(lambda x: '{:,.0f}'.format(x))

    stations_2023_numeric = stations_2023.copy()
    stations_2024_numeric = stations_2024.copy()
    stations_2023_numeric["ridership"] = pd.to_numeric(stations_2023_numeric["ridership"].str.replace(',', ''))
    stations_2024_numeric["ridership"] = pd.to_numeric(stations_2024_numeric["ridership"].str.replace(',', ''))

    top5_2023 = stations_2023.loc[stations_2023_numeric.sort_values(by="ridership", ascending=False).index].head(15)
    top5_2024 = stations_2024.loc[stations_2024_numeric.sort_values(by="ridership", ascending=False).index].head(15)
    top10_2023 = stations_2023.loc[stations_2023_numeric.sort_values(by="ridership", ascending=False).index].head(10)
    top10_2024 = stations_2024.loc[stations_2024_numeric.sort_values(by="ridership", ascending=False).index].head(10)

    return stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024

def write_to_excel(output_file, stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024, output_dir, file_path, ridership_column, chunksize=100000, date_column="transit_timestamp", date_format='%m/%d/%Y %I:%M:%S %p'):
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        workbook = writer.book

        def write_as_table(df, sheet_name, writer, use_color=False):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            end_row = len(df)
            end_col = len(df.columns) - 1
            table_range = f'A1:{chr(65 + end_col)}{end_row + 1}'
            table_style = 'Table Style Medium 2' if not use_color else 'Table Style Medium 4'
            worksheet.add_table(table_range, {
                'columns': [{'header': col} for col in df.columns],
                'style': table_style,
                'first_column': True
            })
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.set_column(idx, idx, max_length + 2)

        write_as_table(stations_2023, "2023 Ridership", writer)
        write_as_table(stations_2024, "2024 Ridership", writer)
        write_as_table(top5_2023, "Top 5 Stations 2023", writer, use_color=True)
        write_as_table(top5_2024, "Top 5 Stations 2024", writer, use_color=True)

        fig, ax = plt.subplots(figsize=(12, 8))
        top10_2023_plot = top10_2023.copy()
        top10_2024_plot = top10_2024.copy()
        top10_2023_plot["ridership"] = pd.to_numeric(top10_2023_plot["ridership"].str.replace(',', ''))
        top10_2024_plot["ridership"] = pd.to_numeric(top10_2024_plot["ridership"].str.replace(',', ''))


        bar_height = 0.35
        #plot 2023 data
        y_pos = range(len(top10_2023_plot))
        ax.barh([i + bar_height for i in y_pos], 
                top10_2023_plot["ridership"], 
                height=bar_height,
                label="2023",
                color="#1f77b4",  # A more visible blue
                alpha=0.8)
        
        #plot 2023 data
        ax.barh([i for i in y_pos], 
                top10_2024_plot["ridership"], 
                height=bar_height,
                label="2024",
                color="#d62728",  # A more visible red
                alpha=0.8)
        
        # Format axis and labels
        def format_with_commas(x, p):
            return f"{x:,.0f}"

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_with_commas))
        ax.set_xlabel("Ridership", fontsize=10, fontweight='bold')
        ax.set_ylabel("Station Complex", fontsize=10, fontweight='bold')
        ax.set_title("Top 10 Subway Stations Ridership Comparison (2023 vs 2024)", 
                    fontsize=12, 
                    fontweight='bold', 
                    pad=20)
       
        # Adjust y-axis labels
        ax.set_yticks([i + bar_height/2 for i in y_pos])
        ax.set_yticklabels(top10_2023_plot["station_complex"], fontsize=9)
       # Add gridlines for better readability
        ax.grid(True, axis='x', linestyle='--', alpha=0.3)

        # Customize legend
        ax.legend(bbox_to_anchor=(1.02, 1),  # Move to upper right corner
                 loc='upper left',            # Align to upper left of the bbox_to_anchor point
                 ncol=1,                      # Stack the legend items vertically
                 fontsize=10,
                 borderaxespad=0)             # Remove padding between axis and legend

        # Adjust layout to make room for legend
        plt.tight_layout()
        
        # When saving, ensure the legend is included in the output
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

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(range(24), hourly_data, marker='o')
        hour_labels = [f'{h%12 if h%12 != 0 else 12}:00 {"AM" if h < 12 else "PM"}' for h in hours]
        ax.set_xticks(range(24))
        ax.set_xticklabels(hour_labels, rotation=45)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))
        hour_labels = [f'{h}:00' for h in (hours)]
        ax.set_xticks(range(24))
        ax.set_xticklabels(hour_labels, rotation=45)
        ax.set_xlabel('Hour (EST)')
        ax.set_ylabel('Average Ridership')
        ax.set_title('Average Hourly Subway Ridership')
        ax.grid(True, linestyle='--', alpha=0.7)


        #lets not include the hourly chart for now. It has to be fixed. The Number of riders keeps coming out as zero. I will fix it later.
        #hourly_chart_path = output_dir / "hourly_ridership_chart.png"
        #plt.savefig(hourly_chart_path, bbox_inches="tight", dpi=300)
        plt.close(fig)

        #worksheet_hourly = workbook.add_worksheet("Hourly Chart")
        #worksheet_hourly.insert_image("B2", str(hourly_chart_path))
        worksheet_chart = workbook.add_worksheet("Top 10 Chart")
        worksheet_chart.insert_image("B2", str(chart_path))

    print(f"✅ Updated file with full ridership data, percentages, top stations, and charts saved to: {output_file}")

def main():
    file_path, output_file, output_dir = define_paths()
    total_ridership_per_year, stations_2023, stations_2024 = load_data(file_path)
    stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024 = process_data(total_ridership_per_year, stations_2023, stations_2024)
    write_to_excel(output_file, stations_2023, stations_2024, top5_2023, top5_2024, top10_2023, top10_2024, output_dir, file_path, "ridership")

if __name__ == "__main__":
    main()
