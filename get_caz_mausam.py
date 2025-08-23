from PIL import Image
from datetime import datetime, timedelta, timezone
import requests
from io import BytesIO
import json
import os

stations = [
    "agt","aya","bnh","bhj","bhp","cpj","cni","dli","dlh","goa","gop","hyd",
    "jot","jmu","jpr","kuf","kkl","kol","koc","leh","ldn","lkn","mks","mur",
    "mbr","mpt","mum","ngp","pdp","plk","ptn","ptl","rpr","shr","sur","slp",
    "srn","tvm","vrv","vsk"
]

# Below mentioned time is in minutes, like 30 is 30 minutes, for two hour it needs to be 120 minutes
PRODUCT_THRESHOLDS = {
    "caz": 30,      # 30 minutes
    "xyz": 60,      # 1 hour
    "abc": 1440     # 24 hours
}

IST = timezone(timedelta(hours=5, minutes=30))

def load_station_overrides(file_path="station_overrides.json"):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                overrides = json.load(f)
                return {item["stn"]: item for item in overrides}
            except json.JSONDecodeError:
                print("Warning: Invalid JSON Format")
    return {}

def get_product_timestamp(stations, product_type, thresholds, overrides):
    results = []
    threshold_mins = thresholds.get(product_type, 30)
    now = datetime.now(IST)

    with requests.Session() as session:
        for s in stations:

            if s in overrides:
                override = overrides[s]
                results.append({
                    "station": s,
                    "date": override.get("date", "NA"),
                    "time": override.get("time", "NA"),
                    "status": override.get("status", "Unknown"),
                    "product_type": product_type
                })
                continue

            url = f"https://mausam.imd.gov.in/Radar/{product_type}_{s}.gif"
            try:
                response = session.get(url, timeout=5)
                response.raise_for_status()

                with Image.open(BytesIO(response.content)) as im:
                    ts = im.info.get('comment')
                    if ts:
                        timestamp = ts.decode()
                        try:
                            dt_naive = datetime.fromisoformat(timestamp)
                            dt = dt_naive.replace(tzinfo=IST)
                            date_str = dt.strftime("%Y-%m-%d")
                            time_str = dt.strftime("%H:%M:%S")
                            
                            if now - dt > timedelta(minutes=threshold_mins):
                                status = "Not Ok"
                            else:
                                status = "Ok"
                        except ValueError:
                            date_str, time_str = "Invalid", "Invalid"
                            status = "problem"
                    else:
                        date_str, time_str = "NA", "NA"
                        status = "Timestamp Missing"
                results.append({
                    "station": s,
                    "date": date_str,
                    "time": time_str,
                    "status": status,
                    "product_type": product_type
                })
            except Exception as e:
                results.append({
                    "station": s,
                    "date": "NA",
                    "time": "NA",
                    "status": "problem",
                    "product_type": product_type,
                    "error_message": str(e)
                })
    return results

if __name__ == "__main__":
    product = "caz"
    overrides = load_station_overrides()
    data = get_product_timestamp(stations, product, PRODUCT_THRESHOLDS, overrides)

    now_str = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    filename = f"status_{product}_{now_str}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Station Status Updated: {filename}")