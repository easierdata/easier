import requests
import pandas as pd
import time
import subprocess
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()
TOKEN = os.getenv('TOKEN')
TMPDIR = os.getenv('TMPDIR')
DATAROOT = os.getenv('DATAROOT')
ENDPOINT = os.getenv('ENDPOINT')
#PATH_TO_SCRIPT = ""

#PATH_TO_CSV = ""
#NEW_CSV = ""
dataset=""
year= "2013"
NEW_CSV = f"{DATAROOT}/{dataset}-CAR_{year}_car_master.csv"

df = pd.read_csv(NEW_CSV,index_col=0)
if 'textile_id' not in df.columns:
    df['textile_id'] = ''


new_df = df.copy()
for idx, row in df.iterrows():
  print("Index ", idx)
  print(row["name"])

  if len(str(row["textile_id"])) > 3:
    print("Exists, Skipping")
  else:
    file_name = row["file"]
    api_key = TOKEN
    #url = f"" 
    url = f"{ENDPOINT}/{dataset}-CAR/{year}/{file_name}" # GEOG Cluster
    payload_cid = str(row["payload_cid"])
    piece_cid = str(row["piece_cid"])
    piece_size = str(row["piece_size"])
    next = datetime.now() + timedelta(days=10)
    date = str(next.isoformat(timespec="seconds")) + "-04:00"
    body = {"payloadCid":payload_cid,"pieceCid":piece_cid,"pieceSize":int(round(float(piece_size))), "repFactor":5, "deadline":date, "carURL":{"url":url} }
    headers={'Authorization': f'Bearer {api_key}'}
    print(body)
    response = requests.post("https://broker.staging.textile.dev/auction-data",headers=headers, data=json.dumps(body))
    print(response)
    try:
      result = response.json()
      id = result.get("id", "Failure")
    except Exception as e:
      print(e)
      id = 9999
    print("Received ID", id )
    print("Saving ID")

    new_df.at[idx,'textile_id'] = id
    new_df.to_csv(NEW_CSV)
    print("Sleeping...")
    time.sleep(30 * 60)
