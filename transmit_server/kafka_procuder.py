import time
import random
import os
import json
import numpy as np
import pandas as pd
from kafka import KafkaProducer

# Load the data from the Excel file
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the Excel file
file_path = os.path.join(script_dir, 'data_sample.xlsx')
data = pd.read_excel(file_path)

# Initialize the Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def send_data():
    direction = 1  # 1 for forward, -1 for backward
    index = 0

    while True:
        # Send data in the current direction
        row = data.iloc[index]
        row = row.replace({np.nan: None})
        row_dict = row.to_dict()
        row_json = {key: value for key, value in row_dict.items() if key != 'eventdt'}
        
        # Send the data to the Kafka topic
        producer.send('data_topic', row_json)
        print(f"Sent: {row_json}")

        # Wait for a random period between 0.5 and 1.5 seconds
        time.sleep(random.uniform(1.0, 2))

        # Update the index and change direction if at the ends
        if direction == 1 and index == len(data) - 1:
            direction = -1  # Reverse direction to go backward
        elif direction == -1 and index == 0:
            direction = 1  # Reverse direction to go forward

        # Move the index in the current direction
        index += direction

if __name__ == '__main__':
    send_data()
