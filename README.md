# MTA Data Project
![til](https://github.com/MantieReid/Mta-Data-Project/blob/main/Pictures/ExamplePictures/MonthlyPowerPointAvgRiders/ExampleOfPowerPointMonthly.gif)

## Overview

This project aims to analyze data from the MTA and visualize it into charts, tables, and more. The goal is to allow others to dive deep and find interesting trends about the MTA data. In the future, this data will also be displayed on a dedicated website to enhance accessibility and allow users to interact with the visualized trends etc. 

## Examples 

- Example Files of the charts and tables can be found in `Source/Data/reports/Example`. 
- Link to the example folder -> [Example Folder](https://github.com/MantieReid/Mta-Data-Project/tree/main/Source/Data/reports/Example)
  
## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/MantieReid/Mta-Data-Project.git
   ```
2. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```
   
## Usage

1. **Download the dataset**:
   - The scripts extract data from the CSV, specifically from the dataset "MTA Subway Hourly Ridership: 2020-2024".
   - Download the dataset as a CSV from [here](https://dev.socrata.com/foundry/data.ny.gov/wujg-7c2s) by clicking on "Export dataset as CSV".
   - ![alt text](https://github.com/MantieReid/Mta-Data-Project/blob/main/Pictures/InstructionsPictures/ExportThatDataset.png)
   - It will take a while to download the entire dataset. Go watch a movie while you wait.
2. **Move the downloaded file**:
   - Move the downloaded file to `Source/Data/Raw`.
3. **Run the scripts**:
   - Run the script and it will create the reports in `Source/Data/Reports`. 

## Script Descriptions

- **SeasonalData.py** (Located in `Source/Data_scripts/Analysis/`):

 
  - Creates seasonal ridership comparison charts.
  - Generates the table `Ridership_2023` and `Ridership_2024`, listing total ridership for each station for each season.
  - `Top_Stations_chart` shows the top five stations for each season.
  - `Overall_chart` shows the number of riders for each season compared with the two years 2023 and 2024. 
  - Exports results to: `Seasonal_Ridership_Data_by_Station_<date>.xlsx` in `Source/Data/reports/`.

- **TotalNumberOfRidersForTheYear.py** (Located in `Source/Data_scripts/Analysis/`):

  - Calculates the total subway ridership for each year and shows the busiest stations.
  - Creates top station ridership charts.
  - Generates tables:
    - `2023 Ridership` and `2024 Ridership`: Contains total ridership for each station.
    - `Top 5 Stations 2023` and `Top 5 Stations 2024`: Lists the busiest stations by ridership.
  - Charts are located in the `Top 10 Chart` tab of the exported file.
  - Exports results to: `MTA_Station_Ridership_Yearly_Analysis_For_2023_and_2024_<date>.xlsx` in `Source/Data/reports/`.

- **AverageNumberOfRiders2023and2024Sep.py** (Located in `Source/Data_scripts/Analysis/`):

  - Shows the average number of riders per hour for each station in 2023 and 2024.

  - Creates tables that shows the Average number of riders for each hour for each year. 

  - `Ridership_<year>`: Lists average hourly ridership per station for the year.

  - Exports results to: `avg_ridership_<year>Made_On_<date>.xlsx` in `Source/Data/reports/`. It will be in Two Separate excel files. One for 2023 and 2024.  

- **AverageNumberOfRidersForEachDayOfTheWeek.py** (Located in `Source/Data_scripts/Analysis/`):

  - Creates tables and charts that shows the average number of riders for each day of the week. 
  - `2023 Average Ridership` and `2024 Average Ridership`: Lists average ridership for each day of the week.
  - Tables are exported in Excel format. Charts are exported in the powerpoint format. 
  - Exports results to: `MTA_Subway_Ridership_Weekday_Stats_average_<date>.xlsx` and `Average Daily Subway Ridership by Day of Week_For_2023_and_2024_<date>.pptx` in `Source/Data/reports/`.

- **CreateChartsForEachMonthINPowerPoint.py** (Located in `Source/Data_scripts/Charts/In_PowerPoint_Format/`):

  - Creates a line chart that shows the average number of riders for each station for each hour. Shows peak hours and off peak hours.
  - Each month is put in a different powerpoint file.
  - Over 400 slides for each powerpoint file.  
  - Exports results to: `MTA_Ridership_<month>_<year>.pptx` in `Source/Data/reports/`.

## Future Plans

- **Website Integration:** The project aims to host a dedicated website that will dynamically display the analyzed MTA data, making it more accessible to the public.

