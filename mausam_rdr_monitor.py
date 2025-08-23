from PIL import Image
from datetime import datetime
import requests
from io import BytesIO

#gif_path = r'd:\Office\Works\2025-26\Radar\Datacenter\RadarStatus\caz_dlh.gif'

statn = ["agt", "aya", "bnh", "bhj","bhp","cpj","cni","dli","dlh","goa","gop","hyd","jot","jmu","jpr","kuf","kkl","kol",
         "koc","leh","ldn","lkn","mks","mur","mbr","mpt","mum","ngp","pdp","plk","ptn","ptl","rpr","shr","sur","slp","srn","tvm","vrv","vsk"]

def get_caz_timestamp(stations):
    results = []
    with requests.Session() as session:
        for s in stations:
            caz_url = f"https://mausam.imd.gov.in/Radar/caz_{s}.gif"
            response = requests.get(caz_url)
            response.raise_for_status()

            try:
                with Image.open(BytesIO(response.content)) as im:
                    ts = im.info.get('comment')
                    if ts:
                        timestamp = ts.decode()
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            date_str = dt.strftime("%Y-%m-%d")
                            time_str = dt.strftime("%H:%M:%S")
                        except ValueError:
                            date_str, time_str = "Invalid Timestamp", "Invalid Timestamp"
                    else:
                        date_str, time_str = "NA", "NA"
                results.append((s,date_str,time_str))
            
            except Exception as e:
                results.append((s, "Error",str(e)))
    return results

for station, date, time in get_caz_timestamp(statn):
    print(f"{station:<6} {date:<12} {time}")