from google.cloud import firestore
import argparse
import logging

parser = argparse.ArgumentParser(description=('Traffic Data Generator'))

parser.add_argument('--project_id',
                    required = True,
                    help = 'GCP cloud project id.')

parser.add_argument('--firestore_collection',
                    required = True, 
                    help = 'Firestore collection name.')

args, opts = parser.parse_known_args()

def extract_drivers_plate(db, firestore_collection):
    driver_ref = db.collection(firestore_collection).stream()

    license_plate_list = []

    for driver in driver_ref:
        data = driver.to_dict()

        if "license_plate" in data:
            license_plate_list.append(data["license_plate"])

    return license_plate_list

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    logging.info('Initializing the data generator.')

    client = firestore.Client(project = args.project_id)
    print(extract_drivers_plate(db=client, firestore_collection = args.firestore_collection))