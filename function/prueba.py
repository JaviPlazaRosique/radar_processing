import base64
import json
from google.cloud import firestore

# Initialize Firestore client
firestore_client = firestore.Client()

def process_traffic_fine(event, context):
    """
    Cloud Function triggered by Pub/Sub
    """
    try:
        # 1. Pub/Sub delivers the message in base64
        if 'data' in event:
            pubsub_message = base64.b64decode(event['data']).decode('utf-8')
            data = json.loads(pubsub_message)
        else:
            print("No data found in event")
            return
    except Exception as e:
        print("Error parsing message:", e)
        return

    # 2. Read the Pub/Sub messages
    license_plate = data.get("license_plate")
    speed = data.get("speed")
    fine_amount = data.get("fine_amount")
    points_lost = data.get("points_lost", 0)

    # 3. Validates that the message contains the license plate
    if not license_plate:
        print("Incomplete message: missing license_plate")
        return

    print(f"Processing fine for {license_plate}: -{points_lost} points, {fine_amount} EUR")

    # 4. Queries Firestore to find the driver associated with the license plate
    # We use a query because we might not know the Document ID (NIF), only the plate
    drivers_ref = firestore_client.collection("drivers")
    query = drivers_ref.where("license_plate", "==", license_plate).limit(1)
    results = list(query.stream())

    if not results:
        print(f"Driver for vehicle {license_plate} not found in Firestore")
        return

    # Get the document snapshot
    driver_doc = results[0]
    driver_data = driver_doc.to_dict()
    driver_id = driver_doc.id

    # 5. Updates the driver's points in Firestore
    current_points = driver_data.get("license_points", 0)
    
    # Calculate new points (ensure it doesn't drop below 0)
    new_points = max(0, current_points - points_lost)

    if points_lost > 0:
        # Update the document
        driver_doc.reference.update({"license_points": new_points})
        print(f"Points updated for {driver_id}. Old: {current_points}, New: {new_points}")
    else:
        print("No points to deduct. Skipping DB update.")

    # 6. Constructs the fine notification email
    driver_name = driver_data.get("first_name", "Driver")
    driver_email = driver_data.get("email", "unknown@email.com")

    email_template = """
    Subject: Traffic Violation Notice - {{license_plate}}
    
    Dear {{name}},
    
    You have been fined for speeding.
    
    Details:
    - Speed Detected: {{speed}} km/h
    - Fine Amount: {{fine_amount}} €
    - Points Deducted: {{points_lost}}
    
    Your remaining points: {{new_points}}
    
    Please pay at the electronic office.
    """

    # 7. Replaces template placeholders with real values
    final_message = (
        email_template
        .replace("{{license_plate}}", license_plate)
        .replace("{{name}}", driver_name)
        .replace("{{speed}}", str(speed))
        .replace("{{fine_amount}}", str(fine_amount))
        .replace("{{points_lost}}", str(points_lost))
        .replace("{{new_points}}", str(new_points))
    )

    # 8. Displays the message (simulating email sending)
    print(f"--- SENDING EMAIL TO: {driver_email} ---")
    print(final_message)
    print("------------------------------------------")