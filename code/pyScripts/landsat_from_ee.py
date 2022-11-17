"""
Cache Landsat scenes from USGS Earth Explorer.

Migrated from Pynotebooks/Inventory_check_Landsat.ipynb
"""

from pathlib import Path
import browser_cookie3
import requests
import shutil
import os
import json
from urllib.request import urlopen
from pystac.item import Item
import pandas as pd
import datetime
import glob

# background step: login in USGS EROS so the brower cookie can skip the redirect of USGS when request

cj = browser_cookie3.firefox(domain_name="usgs.gov")


def cache_asset(url, path):
    """
    cache single file with href from USGS
    """
    r = requests.get(url, stream=True, cookies=cj)
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True

        # Open a local file with wb ( write binary ) permission.
        with open(path, "wb") as f:
            shutil.copyfileobj(r.raw, f)


def hand_pull_product(
    product_id, collection="landsat-c2l1", tarfile=True, verbose=False
):
    """
    Retrieve all files for a c2l1 product and pack into a .tar file
    product_id: e.g."LC09_L1TP_086075_20220509_20220510_02_T1"
    """
    directory = f"../../data/landsat/hand_pull/{product_id}"
    if os.path.exists(directory + ".tar"):
        # print('skip',product_id)
        return
    usgs_item_url = f"https://landsatlook.usgs.gov/stac-server/collections/{collection}/items/{product_id}"
    # read stac
    r = urlopen(usgs_item_url).read()
    stac_json = json.loads(r)
    scene = Item.from_dict(stac_json)
    assets_urls = [
        [k, scene.assets[k].href] for k in scene.get_assets().keys() if k != "index"
    ]
    directory = (
        f"../../data/landsat/hand_pull/{scene.id}"  # in case there is a miss match
    )
    if not os.path.exists(directory):
        os.makedirs(directory)
    # loop run the assets
    for k, url in assets_urls:
        path = f"{directory}/{Path(url).name}"
        # print(k,path)
        if verbose:
            print(url)
        cache_asset(url, path)
    # save stac information
    with open(f"{directory}/{scene.id}_stac.json", "w") as w:
        json.dump(stac_json, w)
    if tarfile:
        output = shutil.make_archive(
            directory, "tar", Path(directory).parent, Path(directory).name
        )
        print(output)
        shutil.rmtree(directory)
    else:
        print(directory)


def load_todo_list():
    """
    return a list of product id to download
    """
    missing_products_l1 = pd.read_csv(
        "../../../data/Landsat/missing_id.csv"
    ).id.tolist()
    finished = [
        fp.split("/")[-1][:-4]
        for fp in glob.glob("../../data/landsat/**/*.tar", recursive=True)
    ]
    chronological_list = sorted(
        list(set(missing_products_l1) - set(finished)), key=lambda x: x.split("_")[3]
    )
    print(chronological_list[20000])
    return chronological_list[:20000]


def task_run(product_list):
    """
    download product in parallel mode
    """

    from multiprocessing import Pool
    from itertools import repeat

    print(datetime.datetime.now())
    a_args = product_list
    second_arg = "landsat-c2l1"
    with Pool(10) as p:
        p.starmap(hand_pull_product, zip(a_args, repeat(second_arg)))
    print(datetime.datetime.now())


if __name__ == "__main__":
    product_list = load_todo_list()
    task_run(product_list)
