from pathlib import Path
import os
import subprocess
import pandas as pd
import json
import datetime
from dotenv import load_dotenv
import os
load_dotenv()
token = os.getenv('TOKEN')
TMPDIR = os.getenv('TMPDIR')
DATAROOT = os.getenv('DATAROOT')
pow_path = os.getenv('POW')
year="2011"
dataset = "MOD09Q1G_NDVI"
target_dir = Path(f"{DATAROOT}/{dataset}/{year}") # path to input fils
car_dir = Path(f"{DATAROOT}/{dataset}-CAR/{year}") # path to output CARs

car_dir.mkdir(parents=True, exist_ok=True) # create car dir automatically
targets = [x for x in target_dir.glob("*") if x.is_dir()]


print(datetime.datetime.now())

df = pd.DataFrame(columns = ['name', 'payload_cid', 'piece_size', 'piece_cid', "file"])
for target in targets:

    print(target)

    car_target = car_dir / Path(str(target.stem) + ".car")

    if car_target.exists():
        print(f"Skipping {car_target.name}")
        continue

    # Don't aggregate 
    # result = subprocess.run([str(pow_path), "offline", "prepare", "--json", str(target), str(car_target)], shell=True, capture_output=True)
    
    # Aggregate
    result = subprocess.run(f"{str(pow_path)} offline prepare --json --aggregate {str(target)} {str(car_target)} --tmpdir {TMPDIR}", shell=True, capture_output=True)
    #limited tmp folder on GEOG cluster; add tmpdir to redirect tmp files
    
    try:
        result=json.loads(result.stderr.decode('utf-8'))
        temp_df = {"name": str(car_target.stem), "payload_cid": result["payload_cid"], "piece_size": result["piece_size"], "piece_cid": result["piece_cid"], "file": str(car_target.name)}
        df = df.append(temp_df, ignore_index=True)
        df.to_csv(f"{str(car_dir.parent)}/{str(car_dir.stem)}_car_master.csv") # CHANGE AS REQUIRED
        with open(f"{str(car_dir.parent)}/{str(car_dir.stem)}_{str(target.stem)}_car_reference.json",'w',encoding='utf-8') as fw:
            json.dump(result,fw,ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"error - {target}  - {e}")
    
    print(result)


print(datetime.datetime.now())