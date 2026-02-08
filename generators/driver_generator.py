from google.cloud import firestore 
from faker import Faker 
import random 
import datetime
import argparse
import logging

fake = Faker("es_ES")

parser = argparse.ArgumentParser(description=('Radar Processing Data Generator.'))

parser.add_argument('--project_id',
                    required = True,
                    help = 'GCP cloud project name.')

parser.add_argument('--firestore_collection',
                    default = 'drivers',
                    required = False, 
                    help = 'Firestore collection name.')

args, opts = parser.parse_known_args()

def license_points(element):
    today = datetime.date.today()

    age = today.year - element.year - ((today.month, today.day) < (element.month, element.day))

    if 18 <= age < 20:
        return 8
    elif 20 <= age < 22:
        return 12
    elif age == 22:
        return 14
    else:
        return 15

def license_plate():
    letters = "BCDFGHJKLMNPRSTVWXYZ"

    return f"{random.randint(0, 9999):04d}{"".join(random.choices(letters, k=3))}"

def driver_profile():
    date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=100)

    points = license_points(date_of_birth)

    profile = {
        "first_name": fake.first_name(),
        "last_name": f"{fake.last_name()} {fake.last_name()}",
        "date_of_birth": date_of_birth.strftime('%d/%m/%Y'),
        "address": f"{fake.street_address()}, {fake.city()}",
        "postal_code": fake.postcode(),
        "email": fake.email(),
        "phone_number": fake.phone_number(),
        "license_points": points,
        "license_plate": license_plate()
    }

    return profile

def main(db, firestore_collection):
    driver_ref = db.collection(firestore_collection)

    for i in range(50):
        payload = driver_profile()
        
        nif = fake.nif()
        
        payload["nif"] = nif
        
        try: 
            driver_ref.add(payload, document_id=nif)
            logging.info(f"Created driver document: {nif}")
        except Exception as e: 
            logging.error(f"Error creating driver document {nif}: {e}")

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    logging.info('Initializing the data generator.')

    client = firestore.Client(project=args.project_id)
    main(db=client, firestore_collection=args.firestore_collection)