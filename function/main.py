from google.cloud import firestore
import json
import base64

firestore_client = firestore.Client()

def driver_notification(event, context):
    try: 
        if 'data' in event:
            msg = base64.b64decode(event['data']).decode('utf-8')
            data = json.loads(msg)
        else:
            print("No data found in event")
            return
    except Exception as e: 
        print(f"Error parsing message: {e}")
        return
    
    license_plate = data.get("license_plate")
    speed = data.get("speed")
    fine_amount = data.get("fine_amount")
    points_lost = data.get("points_lost")

    drivers_ref = firestore_client.collection("drivers")
    query = drivers_ref.where("license_plate", "==", license_plate).limit(1)
    query_results = list(query.stream())

    if not query_results:
        print(f"Driver for vehicle {license_plate} not found in Firestore")
        return
    
    driver_document = query_results[0]
    driver_data = driver_document.to_dict()
    driver_nif = driver_data.id

    current_points = driver_data.get("license_points")

    actually_points = max(0, current_points - points_lost)

    if points_lost > 0:
        driver_document.reference.update({"license_points": actually_points})
        print(f"Points updated for {driver_nif}. Old: {current_points}, New: {actually_points}")
    else:
        print("No points to deduct. Skipping DB update.")

    if actually_points == 0:
        email = """
        Subject: Traffic Violation and Loss of License Notice - {{license_plate}}

        Dear {{driver_name}},

        This is a formal notification regarding a traffic violation recorded against your vehicle. Due to the severity of this infraction and your current point balance, your driving license is now revoked.

        1. Violation Details and Financial Penalty

        - Speed Detected: {{speed}} km/h
        - Fine Amount: {{fine_amount}} €
        - Points Deducted: {{points_lost}}

        Reduced Payment Information:
        You are required to pay the fine. If paid within 21 calendar days of this notice, you are eligible for a 50% reduction.

        - Discounted amount payable: {{fine_amount_desc}} €

        To proceed with the payment, please visit the Electronic Office.

        2. Loss of Validity of Driving License

        As a result of the points deducted from this infraction, your point balance has been exhausted.

        - Current Point Balance: {{actually_points}}
        - Status: INVALID / REVOKED

        Consequences and Obligations:
        In accordance with current traffic regulations:

        1. You are strictly prohibited from driving effective immediately.
        2. You must surrender your physical driving license at the nearest Traffic Headquarters immediately.

        Sincerely,

        Traffic Administration
        """
    else:
        email = """
        Subject: Traffic Violation Notice - {{license_plate}}

        Dear {{driver_name}},

        This is a formal notification regarding a traffic violation recorded against your vehicle for speeding.

        Violation Details:
        - Speed Detected: {{speed}} km/h
        - Fine Amount: {{fine_amount}} €
        - Points Deducted: {{points_lost}}

        License Status:
        - Remaining Points Balance: {{actually_points}}

        Reduced Payment Information: Please be advised that if the fine is paid within 21 calendar days of this notice, you are eligible for a 50% reduction on the total fine amount.

        Discounted amount payable: {{fine_amount_desc}} €

        To proceed with the payment, please visit the Electronic Office.

        Sincerely,

        Traffic Administration
        """

    driver_name = f"{driver_data.get('first_name')} {driver_data.get('last_name')}"
    driver_email = driver_data.get("email")
    fine_amount_desc = float(fine_amount) * 0.5

    final_email = (
        email
        .replace("{{license_plate}}", license_plate)
        .replace("{{driver_name}}", driver_name)
        .replace("{{fine_amount}}", fine_amount)
        .replace("{{points_lost}}", points_lost)
        .replace("{{fine_amount_desc}}", fine_amount_desc)
        .replace("{{actually_points}}", actually_points)
        .replace("{{speed}}", speed)
    )

    print(f"--- SENDING EMAIL TO: {driver_email} ---")
    print(final_email)
    print("------------------------------------------")