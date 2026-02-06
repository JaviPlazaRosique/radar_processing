from google.cloud import firestore
from google.cloud import pubsub_v1
from datetime import datetime, timedelta
import argparse
import logging
import random
import json
import time

parser = argparse.ArgumentParser(description=('Traffic Data Generator'))

parser.add_argument('--project_id',
                    required = True,
                    help = 'GCP cloud project id.')

parser.add_argument('--firestore_collection',
                    required = True, 
                    help = 'Firestore collection name.')

parser.add_argument('--traffic_topic',
                    required = True,
                    help = 'GCP PubSub topic for traffic data')

args, opts = parser.parse_known_args()

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(args.project_id, args.traffic_topic)

def extract_drivers_plate(db, firestore_collection):
    driver_ref = db.collection(firestore_collection).stream()

    license_plate_list = []

    for driver in driver_ref:
        data = driver.to_dict()

        if "license_plate" in data:
            license_plate_list.append(data["license_plate"])

    return license_plate_list

def publish_event(license_plate, sensor_id, timestamp):
    payload = {
        "license_plate": license_plate,
        "sensor_id": sensor_id,
        "timestamp": timestamp
    }

    payload_bytes = json.dumps(payload).encode("utf-8")

    try:
        future = publisher.publish(topic_path, data=payload_bytes)

        message_id = future.result()

        logging.info(f"Event published: {message_id}")

    except Exception as e:
        logging.error(f"Error publishing event: {e}")

def main(license_plate_list):
    plate = random.choice(license_plate_list)

    speed = round(random.gauss(110, 20), 2)

    distance_km = 5

    time_in_hours = distance_km / speed
    time_in_second = int(time_in_hours  * 3600)

    entry_time = datetime.now() 
    exit_time = entry_time + timedelta(seconds = time_in_second)

    event_start = {
        "license_plate": plate,
        "timestamp": entry_time.isoformat(),
        "sensor_id": "RADAR_ENTRY",
    }

    publish_event(**event_start)

    time.sleep(random.randint(1, 10))

    event_end = {
        "license_plate": plate,
        "timestamp": exit_time.isoformat(),
        "sensor_id": "RADAR_EXIT"
    }

    publish_event(**event_end)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    logging.info('Initializing the data generator.')

    client = firestore.Client(project = args.project_id)

    license_plate_list = extract_drivers_plate(client, args.firestore_collection)

    while True:
        main(license_plate_list)
        time.sleep(random.randint(1, 5))

