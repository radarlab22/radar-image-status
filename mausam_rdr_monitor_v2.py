from PIL import Image
from datetime import datetime
import requests
from io import BytesIO
import json

stations = [
    "agt","aya","bnh","bhj","bhp","cpj","cni","dli","dlh","goa","gop","hyd",
    "jot","jmu","jpr","kuf","kkl","kol","koc","leh","ldn","lkn","mks","mur",
    "mbr","mpt","mum","ngp","pdp","plk","ptn","ptl","rpr","shr","sur","slp",
    "srn","tvm","vrv","vsk"
]

def get_caz_timestamp(stations):
    results = []
    with requests.Session() as session:
        for s in stations:
            caz_url = f"https://mausam.imd.gov.in/Radar/caz_{s}.gif"
            try:
                response = session.get(caz_url, timeout=5)
                response.raise_for_status()

                with Image.open(BytesIO(response.content)) as im:
                    ts = im.info.get('comment')
                    if ts:
                        timestamp = ts.decode()
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            date_str = dt.strftime("%Y-%m-%d")
                            time_str = dt.strftime("%H:%M:%S")
                            status = "ok"
                        except ValueError:
                            date_str, time_str = "Invalid", "Invalid"
                            status = "invalid"
                    else:
                        date_str, time_str = "NA", "NA"
                        status = "missing"

                results.append({
                    "station": s,
                    "date": date_str,
                    "time": time_str,
                    "status": status,
                    "product_type": "caz"
                })

            except Exception as e:
                results.append({
                    "station": s,
                    "date": "NA",
                    "time": "NA",
                    "status": "error",
                    "product_type": "caz",
                    "error_message": str(e)
                })

    return results

# Example usage: print JSON string
data = get_caz_timestamp(stations)
print(json.dumps(data, indent=2))
