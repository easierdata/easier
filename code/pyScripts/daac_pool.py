# -*- coding: utf-8 -*-
import argparse
import datetime
import warnings
from multiprocessing.pool import ThreadPool
from netrc import netrc
from pathlib import Path

import pandas as pd
import requests

warnings.filterwarnings("ignore")

profiles = {
    "1B": ["GEDI01_B.002", "../../data/gedi/inventory_GEDI01_B.002_latest.csv", 220000],
    "2A": ["GEDI02_A.002", "../../data/gedi/inventory_GEDI02_A.002_latest.csv", 220000],
    "2B": ["GEDI02_B.002", "../../data/gedi/inventory_GEDI02_B.002_latest.csv", 220000],
}

# Set up command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--profile", required=True, help="Specify level to download")
args = parser.parse_args()

p = args.profile
local_cache_root = "../../../daac_data_download_python/data/"
product = profiles[p][0]  # ["GEDI01_B.002","GEDI02_A.002","GEDI02_B.002"]
urs = "urs.earthdata.nasa.gov"  # Address to call for authentication
netrcDir = Path.expanduser("~/.netrc")
print(product)


def check_path(url):
    saveName = local_cache_root + product + url.split(product)[1]
    if not Path(saveName).parent.exists():
        Path(saveName).parent.mkdir(parents=True)
    return


# Define the function to download a single file
def download_file(url):
    saveName = local_cache_root + product + url.split(product)[1]
    try:
        # Create and submit request and download file
        with requests.get(
            url.strip(),
            verify=False,
            stream=True,
            timeout=10,
            auth=(
                netrc(netrcDir).authenticators(urs)[0],
                netrc(netrcDir).authenticators(urs)[2],
            ),
        ) as response:
            if response.status_code != 200:
                print(
                    "{} not downloaded. Verify that your username and password are correct in {}".format(
                        url.split("/")[-1].strip(), netrcDir
                    )
                )
            else:
                response.raw.decode_content = True
                content = response.raw
                with Path.open(saveName, "wb", encoding="utf-8") as d:
                    while True:
                        chunk = content.read(16 * 1024)
                        if not chunk:
                            break
                        d.write(chunk)
                print("saved", saveName)
    except ConnectionResetError as m:
        print(f"\r--> {datetime.datetime.now()} Failed to download {url}. Reason: {m}")


if __name__ == "__main__":
    from time import time

    ts = time()
    inventory = pd.read_csv(profiles[p][1])
    # inventory = pd.read_csv(f'../../data/gedi/inventory_GEDI02_A.002_04-25-2023.csv')

    # List of URLs to download
    tasks = inventory.query('cache=="no"')

    # total scenes to download
    total_scenes = profiles[p][2]

    # Number of threads to use
    num_threads = 16
    file_list = tasks.file_location[0:total_scenes].tolist()
    print("using", num_threads, "to download", len(file_list), "files")

    for url in file_list:
        check_path(url)
    print("paths checked")
    # Create a thread pool and map the download function to the list of URLs
    with ThreadPool(num_threads) as pool:
        pool.map(download_file, file_list)
    te = time()
    print("finished ", total_scenes, " scenes in secs: ", te - ts)
