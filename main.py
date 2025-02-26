import requests
import csv
import os
import time
from datetime import datetime

# API details
URL = "https://imgametransit.com/api/webapi/GetNoaverageEmerdList"
HEADERS = {"Content-Type": "application/json"}

# CSV file path (Railway uses `/app` as the working directory)
CSV_FILE = os.path.join(os.getcwd(), "data.csv")
CSV_HEADERS = ["Period", "Number", "Premium"]

# Function to fetch data
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
        if "data" in data and "list" in data["data"]:
            return data["data"]["list"]
    
    return None

# Function to check if period already exists in CSV
def get_existing_periods():
    if not os.path.exists(CSV_FILE):
        return set()

    with open(CSV_FILE, "r") as file:
        return {line.split(",")[0] for line in file.readlines()[1:]}

# Function to write data to CSV
def write_to_csv(items):
    existing_periods = get_existing_periods()
    new_data = []

    for item in items:
        period = item["issueNumber"]
        number = item["number"]
        premium = item["premium"]
        
        if period not in existing_periods:
            new_data.append([period, number, premium])
            print(f"✅ New period added: {period}")
        else:
            print(f"⚠️ Duplicate period skipped: {period}")

    if new_data:
        existing_data = []
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "r") as file:
                existing_data = file.readlines()
        
        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS)
            writer.writerows(new_data)
            if existing_data:
                file.writelines(existing_data[1:])

# Continuous loop for fetching data
def main():
    while True:
        print(f"⏳ Fetching data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        data = fetch_data()
        if data:
            write_to_csv(data)
        else:
            print("No new data found.")
        
        time.sleep(600)  # Fetch data every 10 min

if __name__ == "__main__":
    main()
