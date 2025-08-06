import time
import os
import json
import pandas as pd
from kafka import KafkaProducer

# Load the data from the Excel file
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'data_sample_v3.xlsx')
data = pd.read_excel(file_path)

# Initialize the Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def send_data():
    for _, row in data.iterrows():
        # Convert the row to a dictionary
        row = row.replace({pd.NA: None})
        row_dict = row.to_dict()

        # Convert Timestamp objects to string, excluding event_date and gps_dt
        for key, value in row_dict.items():
            if isinstance(value, pd.Timestamp):
                row_dict[key] = value.isoformat()

        # Prepare the JSON object, excluding 'event_date' and 'gps_dt'
        row_json = {key: value for key, value in row_dict.items() if key not in ['event_date', 'gps_dt']}
        
        # Send the data to the Kafka topic
        producer.send('data_topic', row_json)
        print(f"Sent: {row_json}")
        
        # Sleep for the duration specified in the time_diff_seconds column
        sleep_time = row_dict.get('time_diff_seconds', 1)  # Default to 1 second if no value
        time.sleep(sleep_time)

if __name__ == '__main__':
    send_data()
