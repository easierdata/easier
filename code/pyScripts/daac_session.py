import os
from multiprocessing.pool import ThreadPool
from pathlib import Path
from netrc import netrc
import pandas as pd
import argparse
import warnings

warnings.filterwarnings("ignore")
from http.cookiejar import CookieJar
import datetime
import urllib.request as urllib

profiles = {
    "3": [
        "GEDI_L3_LandSurface_Metrics_V2",
        "../../data/gedi/inventory_GEDI_L3_LandSurface_Metrics_V2_latest.csv",
        50,
    ],
    "4A": [
        "GEDI_L4A_AGB_Density_V2_1",
        "../../data/gedi/inventory_GEDI_L4A_AGB_Density_V2_1_latest.csv",
        220000,
    ],
    "4B": [
        "GEDI_L4B_Gridded_Biomass",
        "../../data/gedi/inventory_GEDI_L4B_Gridded_Biomass_latest.csv",
        20,
    ],
}

# Set up command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--profile", required=True, help="Specify level to download")
args = parser.parse_args()

p = args.profile
local_cache_root = "../../../daac_data_download_python/data/"
product = profiles[p][0]  # ["GEDI01_B.002","GEDI02_A.002","GEDI02_B.002"]
urs = "urs.earthdata.nasa.gov"  # Address to call for authentication
netrcDir = os.path.expanduser("~/.netrc")
print(product)
# The user credentials that will be used to authenticate access to the data

username = netrc(netrcDir).authenticators(urs)[0]
password = netrc(netrcDir).authenticators(urs)[2]

password_manager = urllib.HTTPPasswordMgrWithDefaultRealm()
password_manager.add_password(
    None, "https://urs.earthdata.nasa.gov", username, password
)

# Create a cookie jar for storing cookies. This is used to store and return
# the session cookie given to use by the data server (otherwise it will just
# keep sending us back to Earthdata Login to authenticate).  Ideally, we
# should use a file based cookie jar to preserve cookies between runs. This
# will make it much more efficient.

cookie_jar = CookieJar()


# Install all the handlers.

opener = urllib.build_opener(
    urllib.HTTPBasicAuthHandler(password_manager),
    # urllib2.HTTPHandler(debuglevel=1),    # Uncomment these two lines to see
    # urllib2.HTTPSHandler(debuglevel=1),   # details of the requests/responses
    urllib.HTTPCookieProcessor(cookie_jar),
)
urllib.install_opener(opener)


def check_path(url):
    saveName = local_cache_root + product + url.split("gedi/" + product)[1]
    if not Path(saveName).parent.exists():
        Path(saveName).parent.mkdir(parents=True)
    return


# Define the function to download a single file
def download_file(url):
    saveName = local_cache_root + product + url.split("gedi/" + product)[1]
    try:
        request = urllib.Request(url.strip())
        response = urllib.urlopen(request)

        if response.getcode() != 200:
            print(
                "{} not downloaded. Verify that your username and password are correct in {}".format(
                    url.split("/")[-1].strip(), netrcDir
                )
            )
        else:
            content = response.read()
            with open(saveName, "wb") as d:
                d.write(content)
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
    print("finished ", len(file_list), " files in secs: ", te - ts)
