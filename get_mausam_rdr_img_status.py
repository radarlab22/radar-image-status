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

PRODUCTS = ["caz", "ppi", "sri", "ppz", "ppv", "vp2", "pac"]

PRODUCT_THRESHOLDS = {
    "caz": 30,
    "ppi": 30,
    "sri": 30,
    "ppz": 30,
    "ppv": 30,
    "vp2": 30,
    "pac": 1440
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

def fetch_product_time(station, product_type, threshold_mins, session):
    url = f"https://mausam.imd.gov.in/Radar/{product_type}_{station}.gif"
    now = datetime.now(IST)
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
                    if now - dt > timedelta(minutes=threshold_mins):
                        return dt.strftime("%Y-%m-%d %H:%M:%S"), False
                    else:
                        return dt.strftime("%Y-%m-%d %H:%M:%S"), True
                except ValueError:
                    return "Invalid", False
            else:
                return "Missing", False
    except Exception:
        return "Missing", False

def get_all_product_status(stations, products, thresholds, overrides):
    now = datetime.now(IST)
    final_data = []
    with requests.Session() as session:
        for s in stations:
            row = {"station": s}
            all_ok = True
            for product in products:
                threshold = thresholds.get(product, 30)
                if s in overrides and product in overrides[s]:
                    ts = overrides[s][product].get("timestamp", "NA")
                    row[product] = ts
                else:
                    ts, ok = fetch_product_time(s, product, threshold, session)
                    row[product] = ts
                    if not ok:
                        all_ok = False
            row["overall"] = "✔️" if all_ok else "❌"
            final_data.append(row)
    return final_data

if __name__ == "__main__":
    overrides = load_station_overrides()
    data = get_all_product_status(stations, PRODUCTS, PRODUCT_THRESHOLDS, overrides)

    now_str = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    filename = f"status_all_{now_str}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Station Status Updated: {filename}")
