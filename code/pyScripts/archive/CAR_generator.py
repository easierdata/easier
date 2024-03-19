# -*- coding: utf-8 -*-
import datetime
import json
import os
import subprocess
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TOKEN")
TMPDIR = os.getenv("TMPDIR")
DATAROOT = os.getenv("DATAROOT")
pow_path = os.getenv("POW")
year = "2011"
dataset = "MOD09Q1G_NDVI"
target_dir = Path(f"{DATAROOT}/{dataset}/{year}")  # path to input fils
car_dir = Path(f"{DATAROOT}/{dataset}-CAR/{year}")  # path to output CARs

car_dir.mkdir(parents=True, exist_ok=True)  # create car dir automatically
targets = [x for x in target_dir.glob("*") if x.is_dir()]


print(datetime.datetime.now())

df = pd.DataFrame(columns=["name", "payload_cid", "piece_size", "piece_cid", "file"])
for target in targets:
    print(target)

    car_target = car_dir / Path(str(target.stem) + ".car")

    if car_target.exists():
        print(f"Skipping {car_target.name}")
        continue

    # Don't aggregate
    # result = subprocess.run([str(pow_path), "offline", "prepare", "--json", str(target), str(car_target)], shell=True, capture_output=True)

    # Aggregate
    result = subprocess.run(
        f"{pow_path!s} offline prepare --json --aggregate {target!s} {car_target!s} --tmpdir {TMPDIR}",
        shell=True,
        capture_output=True,
    )
    # limited tmp folder on GEOG cluster; add tmpdir to redirect tmp files

    try:
        result = json.loads(result.stderr.decode("utf-8"))
        temp_df = {
            "name": str(car_target.stem),
            "payload_cid": result["payload_cid"],
            "piece_size": result["piece_size"],
            "piece_cid": result["piece_cid"],
            "file": str(car_target.name),
        }
        df = df.append(temp_df, ignore_index=True)
        df.to_csv(
            f"{car_dir.parent!s}/{car_dir.stem!s}_car_master.csv"
        )  # CHANGE AS REQUIRED
        with Path.open(
            f"{car_dir.parent!s}/{car_dir.stem!s}_{target.stem!s}_car_reference.json",
            "w",
            encoding="utf-8",
        ) as fw:
            json.dump(result, fw, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"error - {target}  - {e}")

    print(result)


print(datetime.datetime.now())
