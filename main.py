import os
import json
import requests
import csv
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from io import StringIO

# Load Google Drive credentials from Railway environment variable
creds_json = os.getenv("GDRIVE_CREDENTIALS")
if creds_json:
    creds_path = "/tmp/credentials.json"  # Temp file path
    with open(creds_path, "w") as f:
        f.write(creds_json)

    # Authenticate with Google Drive
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(creds_path)  # Correct method
    gauth.CommandLineAuth()  # Use this instead of LocalWebserverAuth()
    drive = GoogleDrive(gauth)
else:
    print("❌ Google Drive credentials not found!")
    exit()

# API details
URL = "https://imgametransit.com/api/webapi/GetNoaverageEmerdList"
HEADERS = {"Content-Type": "application/json"}
CSV_FILE = "data.csv"
CSV_HEADERS = ["Period", "Number", "Premium"]

# Fetch data
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
    response = requests.post(URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["list"] if "data" in data and "list" in data["data"] else None
    return None

# Check existing periods
def get_existing_periods():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, "r") as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header
        return {row[0] for row in reader}

# Write to CSV (append new data)
def write_to_csv(items):
    existing_periods = get_existing_periods()
    new_data = []

    for item in items:
        period = str(item["issueNumber"])  # Ensure period is a string
        number = item["number"]
        premium = item["premium"]
        if period not in existing_periods:
            new_data.append([period, number, premium])
            print(f"✅ New period added: {period}")

    if new_data:
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(CSV_HEADERS)  # Write headers if file is new
            writer.writerows(new_data)

        # Upload to Google Drive
        upload_to_drive()

# Upload function (delete old file first)
def upload_to_drive():
    # Check for existing file with same name
    file_list = drive.ListFile({'q': f"title='{CSV_FILE}'"}).GetList()
    for file in file_list:
        file.Delete()  # Delete existing file

    # Upload new file
    file = drive.CreateFile({'title': CSV_FILE})
    file.SetContentFile(CSV_FILE)
    file.Upload()
    print(f"📤 Uploaded {CSV_FILE} to Google Drive!")

# Main function
def main():
    print("Fetching data...")
    data = fetch_data()
    if data:
        write_to_csv(data)
    else:
        print("No new data found.")

if __name__ == "__main__":
    main()
