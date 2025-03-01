import os
import time
import json
import requests
import csv
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# ✅ Load Google Drive credentials from Railway environment variable
creds_json = os.getenv("GDRIVE_CREDENTIALS")
drive = None

if creds_json:
    try:
        creds_dict = json.loads(creds_json)  # ✅ Load credentials directly from env variable
        scope = ["https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gauth = GoogleAuth()
        gauth.credentials = creds
        drive = GoogleDrive(gauth)
        print("✅ Google Drive authentication successful!")
    except json.JSONDecodeError:
        print("❌ Error: Google Drive credentials are not in valid JSON format.")
    except Exception as e:
        print(f"❌ Error loading Google Drive credentials: {e}")
else:
    print("❌ Google Drive credentials not found!")

# ✅ API details
URL = "https://imgametransit.com/api/webapi/GetNoaverageEmerdList"
HEADERS = {"Content-Type": "application/json"}
CSV_FILE = "data.csv"
CSV_HEADERS = ["Period", "Number", "Premium"]

# ✅ Fetch data
def fetch_data():
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 1,
        "language": 0,
        "random": "4f7eb2c47c0641c2be6b62053f2f3f53",
        "signature": "E3D7840D7D96C459DD2074174CD5A9A5",
        "timestamp": int(datetime.now().timestamp())
    }
    try:
        response = requests.post(URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # ✅ Raises an error for HTTP errors
        data = response.json()
        return data.get("data", {}).get("list", None)
    except requests.RequestException as e:
        print(f"❌ Error fetching data from API: {e}")
    except json.JSONDecodeError:
        print("❌ Error: Received invalid JSON response from API.")
    return None

# ✅ Read existing periods (prevent duplicates)
def get_existing_periods():
    if not os.path.exists(CSV_FILE):
        return set()
    try:
        with open(CSV_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip headers
            return {row[0] for row in reader if row}
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return set()

# ✅ Prepend new data to CSV
def write_to_csv(items):
    existing_periods = get_existing_periods()
    new_data = []

    for item in items:
        period = str(item.get("issueNumber", ""))
        number = str(item.get("number", ""))
        premium = str(item.get("premium", ""))
        if period and period not in existing_periods:
            new_data.append([period, number, premium])
            print(f"✅ New period added: {period}")

    if new_data:
        try:
            # ✅ Read existing CSV data safely
            existing_data = []
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "r", newline="") as file:
                    reader = csv.reader(file)
                    existing_data = list(reader)

            # ✅ Write new data at the top while keeping structure intact
            with open(CSV_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(CSV_HEADERS)  # Always keep header
                writer.writerows(new_data)  # Write new data first
                writer.writerows(existing_data[1:])  # Append old data (skip duplicate header)

            # ✅ Upload to Google Drive if new data is added
            upload_to_drive()
        except Exception as e:
            print(f"❌ Error writing to CSV file: {e}")

# ✅ Upload CSV to Google Drive
def upload_to_drive():
    if drive is None:
        print("❌ Google Drive not authenticated. Skipping upload.")
        return

    try:
        file_list = drive.ListFile({'q': f"title='{CSV_FILE}' and trashed=false"}).GetList()
        if file_list:
            file_id = file_list[0]['id']
            file = drive.CreateFile({'id': file_id})
        else:
            file = drive.CreateFile({'title': CSV_FILE})

        file.SetContentFile(CSV_FILE)
        file.Upload()
        print(f"📤 Uploaded {CSV_FILE} to Google Drive! ✅")
    except Exception as e:
        print(f"❌ Error uploading to Google Drive: {e}")

# ✅ Main function
def main():
    print("🔄 Fetching data...")
    data = fetch_data()
    if data:
        write_to_csv(data)
    else:
        print("⚠️ No new data found.")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(600)  # Fetch data every 10 minutes
