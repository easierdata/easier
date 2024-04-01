# -*- coding: utf-8 -*-
# =============================================================================
#  USGS/EROS Inventory Service Example
#  Description: Download Landsat Collection 2 files
#  Modified From: https://m2m.cr.usgs.gov/api/docs/example/download_landsat_c2-py
#  Usage: python landsat_from_m2m.py -f filetype -s scenes
#         optional argument f refers to filetype including 'bundle' or 'band'
#         required argument s refers to the txt file for scenes id
# =============================================================================

import argparse
import datetime
import json
import os
import re
import sys
import tarfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()


path = "../../data/landsat/m2m_download"  # Fill a valid download path
maxthreads = 16  # Threads count for downloads
sema = threading.Semaphore(value=maxthreads)
label = datetime.datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)  # Customized label using date time
threads = []
# The entityIds/displayIds need to save to a text file such as scenes.txt.
# The header of text file should follow the format: datasetName|displayId or datasetName|entityId.
# sample file - scenes.txt
# landsat_ot_c2_l2|displayId
# LC08_L2SP_012025_20201231_20210308_02_T1
# LC08_L2SP_012027_20201215_20210314_02_T1


# Send http request
def send_request(url, data, api_key=None, exit_if_no_response=True):
    json_data = json.dumps(data)

    if api_key is None:
        response = requests.post(url, json_data, timeout=5)
    else:
        headers = {"X-Auth-Token": api_key}
        response = requests.post(url, json_data, headers=headers, timeout=30)

    output = handle_response(response, exit_if_no_response)
    response.close()

    return output["data"]


def handle_response(response, exit_if_no_response):
    """
    Handle the response from the service.

    Args:
        response: The HTTP response object.
        exit_if_no_response: A boolean indicating whether to exit if there is no response.

    Returns:
        The response data if successful, False otherwise.
    """
    http_status_code = response.status_code

    if response is None:
        print("No output from service")
        if exit_if_no_response:
            sys.exit()
        else:
            return False

    output = json.loads(response.text)

    if output["errorCode"] is not None:
        print(output["errorCode"], "- ", output["errorMessage"])
        if exit_if_no_response:
            sys.exit()
        else:
            return False

    if http_status_code == 404:
        print("404 Not Found")
        if exit_if_no_response:
            sys.exit()
        else:
            return False

    if http_status_code == 401:
        print("401 Unauthorized")
        if exit_if_no_response:
            sys.exit()
        else:
            return False

    if http_status_code == 400:
        handle_400_error(http_status_code, exit_if_no_response)
        return False

    return output


def handle_400_error(http_status_code, exit_if_no_response):
    """
    Handle the 400 error code.

    Args:
        http_status_code: The HTTP status code.
        exit_if_no_response: A boolean indicating whether to exit if there is no response.
    """
    print("Error Code", http_status_code)
    if exit_if_no_response:
        sys.exit()


def downloadFile(url):
    sema.acquire()
    try:
        response = requests.get(url, stream=True, timeout=5)
        disposition = response.headers["content-disposition"]
        filename = re.findall("filename=(.+)", disposition)[0].strip('"')
        print(f"Downloading {filename} ...\n")
        product_id = filename[:-4]
        ac_date = filename.split("_")[3]
        if path != "" and path[-1] != "/":
            filename = "/" + filename
        Path.open(path + filename, "wb", encoding="utf-8").write(response.content)

        tar = tarfile.open(path + filename)
        tar.extractall(path + "/" + ac_date + "/" + product_id)
        tar.close()
        Path.unlink(path + filename)
        print(f"Downloaded and extracted {filename}\n")
        sema.release()
    except Exception:
        print(f"Failed to download from {url}. Will skip.")
        sema.release()
        # runDownload(threads, url)


def runDownload(threads_list, url):
    download_thread = threading.Thread(target=downloadFile, args=(url,))
    threads_list.append(download_thread)
    download_thread.start()


if __name__ == "__main__":
    # User input
    parser = argparse.ArgumentParser()
    # parser.add_argument('-u', '--username', required=True, help='Username')
    # parser.add_argument('-p', '--password', required=True, help='Password')
    parser.add_argument(
        "-f",
        "--filetype",
        required=False,
        choices=["bundle", "band"],
        help='File types to download, "bundle" for bundle files and "band" for band files',
    )
    parser.add_argument(
        "-s", "--scenes", required=True, help="File contains a list of scene ids"
    )
    args = parser.parse_args()
    username = os.getenv("M2M_USER")
    password = os.getenv("M2M_PSWD")
    filetype = args.filetype
    scenesFile = args.scenes
    print("\nRunning Scripts...\n")
    startTime = time.time()

    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    # Login
    payload = {"username": username, "password": password}
    apiKey = send_request(serviceUrl + "login", payload)
    print("API Key: " + apiKey + "\n")

    # Read scenes
    f = Path.open(scenesFile, "r", encoding="utf-8")
    lines = f.readlines()
    f.close()
    header = lines[0].strip()
    spliter = header.find("|") + 1
    datasetName = header[: header.find("|")]
    idField = header[spliter:]

    print("Scenes details:")
    print(f"Dataset name: {datasetName}")
    print(f"Id field: {idField}\n")

    entityIds = []

    lines.pop(0)
    entityIds = [line.strip() for line in lines]

    # Search scenes
    # If you don't have a scenes text file that you can use scene-search to identify scenes you're interested in
    # https://m2m.cr.usgs.gov/api/docs/reference/#scene-search
    # payload = {
    #             'datasetName' : '', # dataset alias
    #             'maxResults' : 10, # max results to return
    #             'startingNumber' : 1,
    #             'sceneFilter' : {} # scene filter
    #           }

    # results = send_request(serviceUrl + "scene-search", payload, apiKey)
    # for result in results:
    #     entityIds.append(result['entityId'])

    # Add scenes to a list
    listId = f"temp_{datasetName}_list"  # customized list id
    payload = {
        "listId": listId,
        "idField": idField,
        "entityIds": entityIds,
        "datasetName": datasetName,
    }

    print("Adding scenes to list...\n")
    count = send_request(serviceUrl + "scene-list-add", payload, apiKey)
    print("Added", count, "scenes\n")

    # Get download options
    payload = {"listId": listId, "datasetName": datasetName}

    print("Getting product download options...\n")
    products = send_request(serviceUrl + "download-options", payload, apiKey)
    print("Got product download options\n")

    # Select products
    downloads = []
    if filetype == "bundle":
        # select bundle files
        downloads = [
            {"entityId": product["entityId"], "productId": product["id"]}
            for product in products
            if product["bulkAvailable"]
        ]
    elif filetype == "band":
        # select band files
        for product in products:
            if (
                product["secondaryDownloads"] is not None
                and len(product["secondaryDownloads"]) > 0
            ):
                for secondaryDownload in product["secondaryDownloads"]:
                    if secondaryDownload["bulkAvailable"]:
                        downloads.append(
                            {
                                "entityId": secondaryDownload["entityId"],
                                "productId": secondaryDownload["id"],
                            }
                        )
    else:
        # select all available files
        for product in products:
            if product["bulkAvailable"]:
                downloads.append(
                    {"entityId": product["entityId"], "productId": product["id"]}
                )
                cond = (
                    product["secondaryDownloads"] is not None
                    and len(product["secondaryDownloads"]) > 0
                )
                if cond:
                    for secondaryDownload in product["secondaryDownloads"]:
                        if secondaryDownload["bulkAvailable"]:
                            downloads.append(
                                {
                                    "entityId": secondaryDownload["entityId"],
                                    "productId": secondaryDownload["id"],
                                }
                            )

    # Remove the list
    payload = {"listId": listId}
    send_request(serviceUrl + "scene-list-remove", payload, apiKey)

    # Send download-request
    payLoad = {"downloads": downloads, "label": label, "returnAvailable": True}

    print("Sending download request ...\n")
    results = send_request(serviceUrl + "download-request", payLoad, apiKey)
    print("Done sending download request\n")

    for result in results["availableDownloads"]:
        u = urlparse(result["url"])
        if u.path.split("/")[-1] != "gen-browse":
            print(f"Get download url: {result['url']}\n")
            runDownload(threads, result["url"])

    preparingDownloadCount = len(results["preparingDownloads"])
    preparingDownloadIds = []
    if preparingDownloadCount > 0:
        preparingDownloadIds = [
            result["downloadId"] for result in results["preparingDownloads"]
        ]

        payload = {"label": label}
        # Retrieve download urls
        print("Retrieving download urls...\n")
        results = send_request(serviceUrl + "download-retrieve", payload, apiKey, False)
        if results:
            for result in results["available"]:
                if result["downloadId"] in preparingDownloadIds:
                    preparingDownloadIds.remove(result["downloadId"])
                    print(f"Get download url: {result['url']}\n")
                    runDownload(threads, result["url"])

            for result in results["requested"]:
                if result["downloadId"] in preparingDownloadIds:
                    preparingDownloadIds.remove(result["downloadId"])
                    print(f"Get download url: {result['url']}\n")
                    runDownload(threads, result["url"])

        # Don't get all download urls, retrieve again after 30 seconds
        while len(preparingDownloadIds) > 0:
            print(
                f"{len(preparingDownloadIds)} downloads are not available yet. Waiting for 30s to retrieve again\n"
            )
            time.sleep(30)
            results = send_request(
                serviceUrl + "download-retrieve", payload, apiKey, False
            )
            if results:
                for result in results["available"]:
                    if result["downloadId"] in preparingDownloadIds:
                        preparingDownloadIds.remove(result["downloadId"])
                        print(f"Get download url: {result['url']}\n")
                        runDownload(threads, result["url"])

    print("\nGot download urls for all downloads\n")
    # Logout
    endpoint = "logout"
    if send_request(serviceUrl + endpoint, None, apiKey) is None:
        print("Logged Out\n")
    else:
        print("Logout Failed\n")

    print("Downloading files... Please do not close the program\n")
    for thread in threads:
        thread.join()

    print("Complete Downloading")

    executionTime = round((time.time() - startTime), 2)
    print(f"Total time: {executionTime} seconds")
