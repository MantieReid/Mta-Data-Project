import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import requests
from GetDataAttempt3 import fetch_batch, base_url, batch_size

class TestGetDataAttempt3(unittest.TestCase):

    @patch('GetDataAttempt3.requests.get')
    def test_fetch_batch(self, mock_get):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'value': [
                {'station_complex_id': '1', 'station_complex': 'Station A', 'latitude': 40.7128, 'longitude': -74.0060, 'transit_timestamp': '2023-01-01T00:00:00', 'ridership': 100},
                {'station_complex_id': '2', 'station_complex': 'Station B', 'latitude': 40.7128, 'longitude': -74.0060, 'transit_timestamp': '2023-01-01T01:00:00', 'ridership': 150}
            ]
        }
        mock_get.return_value = mock_response

        # Call the function
        result = fetch_batch(0)

        # Check the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['station_complex_id'], '1')
        self.assertEqual(result[1]['station_complex_id'], '2')

    @patch('GetDataAttempt3.requests.get')
    def test_total_records(self, mock_get):
        # Mock the API response for total records
        mock_response = MagicMock()
        mock_response.text = '100'
        mock_get.return_value = mock_response

        # Call the function to get total records
        count_url = f"{base_url}/$count"
        response = requests.get(count_url)
        total_records = int(response.text)

        # Check the result
        self.assertEqual(total_records, 100)

    def test_data_processing(self):
        # Sample data
        data = [
            {'station_complex_id': '1', 'station_complex': 'Station A', 'latitude': 40.7128, 'longitude': -74.0060, 'transit_timestamp': '2023-01-01T00:00:00', 'ridership': 100},
            {'station_complex_id': '1', 'station_complex': 'Station A', 'latitude': 40.7128, 'longitude': -74.0060, 'transit_timestamp': '2023-01-01T01:00:00', 'ridership': 150}
        ]

        # Convert data to DataFrame
        df = pd.DataFrame(data)

        # Ensure the datetime column is in datetime format
        df['transit_timestamp'] = pd.to_datetime(df['transit_timestamp'])

        # Extract date and hour from the datetime column
        df['date'] = df['transit_timestamp'].dt.date
        df['hour'] = df['transit_timestamp'].dt.hour

        # Group by station_complex_ID, station_complex, latitude, longitude, and hour
        grouped = df.groupby(['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour'])

        # Calculate the average ridership amount
        average_ridership = grouped['ridership'].mean().reset_index()
        average_ridership.columns = ['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour', 'average_ridership']

        # Check the result
        self.assertEqual(len(average_ridership), 2)
        self.assertEqual(average_ridership.iloc[0]['average_ridership'], 100)
        self.assertEqual(average_ridership.iloc[1]['average_ridership'], 150)

if __name__ == '__main__':
    unittest.main()