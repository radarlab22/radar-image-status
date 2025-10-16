from PIL import Image
from datetime import datetime, timedelta, timezone
import requests
from io import BytesIO
import json
import os

STATION_INFO = {
    "agt": {"name": "Agartala", "state": "Tripura"},
    "aya": {"name": "Delhi Ayanagar", "state": "Delhi"},
    "bnh": {"name": "Banihal", "state": "Jammu & Kashmir"},
    "bhj": {"name": "Bhuj", "state": "Gujrat"},
    "bhp": {"name": "Bhopal", "state": "Madhya Pradesh"},
    "cpj": {"name": "Cherapunji", "state": "Meghalaya"},
    "cni": {"name": "Chennai", "state": "Tamilnadu"},
    "dli": {"name": "Delhi Hq", "state": "Delhi"},
    "dlh": {"name": "Delhi Palam", "state": "Delhi"},
    "goa": {"name": "Goa", "state": "Goa"},
    "gop": {"name": "Gopalpur", "state": "Odhisa"},
    "hyd": {"name": "Hyderabad", "state": "Telangana"},
    "jot": {"name": "Jot", "state": "Himachal Pradesh"},
    "jmu": {"name": "Jammu", "state": "Jammu & Kashmir"},
    "jpr": {"name": "Jaipur", "state": "Rajasthan"},
    "kuf": {"name": "Kufri", "state": "Himachal Pradesh"},
    "kkl": {"name": "Karaikal", "state": "Puducherry"},
    "kol": {"name": "Kolkata", "state": "West Bengal"},
    "koc": {"name": "Kochi", "state": "Kerala"},
    "leh": {"name": "Leh", "state": "Ladakh"},
    "ldn": {"name": "Lansdowne", "state": "Uttrakhand"},
    "lkn": {"name": "Lucknow", "state": "Uttar Pradesh"},
    "mks": {"name": "Mukteshwar", "state": "Uttrakhand"},
    "mur": {"name": "Murari Devi", "state": "Himachal Pradesh"},
    "mbr": {"name": "Mohanbari", "state": "Assam"},
    "mpt": {"name": "Machilipatnam", "state": "Andhra Pradesh"},
    "mum": {"name": "Mumbai", "state": "Maharashtra"},
    "ngp": {"name": "Nagpur", "state": "Maharashtra"},
    "pdp": {"name": "Paradip", "state": "Odhisa"},
    "plk": {"name": "Pallikarni", "state": "Tamilnadu"},
    "ptn": {"name": "Patna", "state": "Bihar"},
    "ptl": {"name": "Patiala", "state": "Punjab"},
    "rpr": {"name": "Raipur", "state": "Chattisgarh"},
    "shr": {"name": "Sriharikota", "state": "Andhra Pradesh"},
    "sur": {"name": "Surkanda Devi", "state": "Uttrakhand"},
    "slp": {"name": "Solapur", "state": "Maharashtra"},
    "srn": {"name": "Srinagar", "state": "Jammu & Kashmir"},
    "tvm": {"name": "Trivandrum", "state": "Kerala"},
    "vrv": {"name": "Veravai", "state": "Maharashtra"},
    "vsk": {"name": "Visakhapatnam", "state": "Andhra Pradesh"}
}


stations = [
    "agt","aya","bnh","bhj","bhp","cpj","cni","dli","dlh","goa","gop","hyd",
    "jot","jmu","jpr","kuf","kkl","kol","koc","leh","ldn","lkn","mks","mur",
    "mbr","mpt","mum","ngp","pdp","plk","ptn","ptl","rpr","shr","sur","slp",
    "srn","tvm","vrv","vsk"
]

PRODUCTS = ["caz", "ppi", "sri", "ppz", "ppv", "vp2", "pac"]

PRODUCT_THRESHOLDS = {
    "caz": 90,
    "ppi": 90,
    "sri": 90,
    "ppz": 90,
    "ppv": 90,
    "vp2": 90,
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
                #timestamp = ts.decode()
                try:
                    dt_naive = datetime.fromisoformat(ts.decode())
                    dt = dt_naive.replace(tzinfo=IST)
                except ValueError:
                    return "Invalid", False
            else:
                last_modified = response.headers.get("Last-Modified")
                if last_modified:
                    try:
                        dt = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z").astimezone(IST)
                    except ValueError:
                        return "Invalid", False
                else:
                    return "Missing", False

            if station == "koc":
                try:
                    y, m, d = dt.year, dt.month, dt.day
                    if m <= 12 and d <= 12 and d != m:
                        fixed_dt = datetime(y, d, m, dt.hour, dt.minute, dt.second, tzinfo=IST)
                        if abs((now - fixed_dt)) < abs((now - dt)):
                            dt = fixed_dt
                except Exception:
                    pass
                    
            if now - dt > timedelta(minutes=threshold_mins):
                return dt.strftime("%Y-%m-%d %H:%M:%S"), False
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S"), True
            
    except Exception:
        return "Missing", False

def get_all_product_status(stations, products, thresholds, overrides):
    now = datetime.now(IST)
    final_data = []
    with requests.Session() as session:
        for s in stations:
            # Add name and state
            row = {
                "station": s,
                "name": STATION_INFO.get(s, {}).get("name", s.upper()),
                "state": STATION_INFO.get(s, {}).get("state", "Unknown"),
            }

            # Check for manual override
            if s in overrides:
                override = overrides[s]
                # build manual_status string
                status_str = override.get("status", "Unknown")
                date_str = override.get("date", "")
                time_str = override.get("time", "")
                row["manual_status"] = f"{status_str} Since {date_str} {time_str}".strip()
                row["overall"] = "❌"
                final_data.append(row)
                continue  # Skip fetching products

            all_ok = True
            for product in products:
                threshold = thresholds.get(product, 30)
                ts, ok = fetch_product_time(s, product, threshold, session)
                row[product] = ts
                if product != "pac" and not ok:
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
