# -*- coding: utf-8 -*-
import asyncio
import csv
import time
from pathlib import Path

import aiohttp
import requests
from bs4 import BeautifulSoup

# global variables
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "gedi" / "lpdaac-metadata"
# Ensure that OUTPUT_PATH exists
Path.mkdir(OUTPUT_PATH, parents=True, exist_ok=True)

# Specify the maximum number of concurrent tasks to assign to a semaphore implementation
concurrency_limit = 15


# Convert the file size to gigabytes
def convert_to_gb(file_size_str: str) -> float:
    """
    Converts a file size string to gigabytes (GB).

    Args:
        file_size_str (str): The file size string to be converted.

    Returns:
        float: The file size in gigabytes (GB).

    Raises:
        None

    Examples:
        >>> convert_to_gb("100M")
        0.095367
        >>> convert_to_gb("512K")
        0.000488
        >>> convert_to_gb("2G")
        2.0
    """
    # Get the number and unit from the file size string
    number = float(file_size_str[:-1])
    unit = file_size_str[-1]

    if unit == "M":
        return round((number / 1024), 6)
    elif unit == "K":
        return round(number / (1024**2), 6)
    elif unit == "G":
        return number
    else:
        return round(0, 6)


def export_to_csv(collection_dict: dict, collection_name: str) -> None:
    """
    Export the product information from a dictionary to a CSV file.

    Args:
        product_dict (dict): A dictionary containing the product information.
        collection_name (str): The name of the GEDI collection.

    Returns:
        None
    """
    # prepare file name and path
    output_file_path = OUTPUT_PATH / f"{collection_name}-details.csv"

    # Delete .csv file if it already exists and generate a new blank csv file
    if Path.exists(output_file_path):
        Path.unlink(output_file_path)
    else:
        pass

    # Open the CSV file in write mode
    with Path.open(output_file_path, "w", newline="") as csvfile:
        # Create a CSV writer
        writer = csv.writer(csvfile)

        # Write the headers to the CSV file
        headers = [
            "product_title",
            "total_size",
            "file_type",
            "file_size",
            "direct_url",
            "collection_date",
        ]
        writer.writerow(headers)

        # Iterate over the items in the dictionary
        for product_title, product_info in collection_dict.items():
            total_size = product_info["total_size"]
            for file_type, file_info in product_info.items():
                if isinstance(file_info, dict):
                    # Write a row to the CSV file
                    file_size = file_info["file_size"]
                    direct_url = file_info["direct_url"]
                    collection_date = file_info["collection_date"]
                    writer.writerow(
                        [
                            product_title,
                            total_size,
                            file_type,
                            file_size,
                            direct_url,
                            collection_date,
                        ]
                    )


def save_stats_to_file(
    product_dict: dict, collection_name: str, start_time: float
) -> None:
    """
    Save statistics about the GEDI collection to a file.

    Args:
        product_dict (dict): A dictionary containing information about the products.
        collection_name (str): The name of the GEDI collection.
        start_time (float): The start time of processing the collection.

    Returns:
        None
    """
    # Grab the end time of processing the collection
    end_time = time.time()
    run_time = end_time - start_time

    # Check if the file exists and create it if it doesn't
    output_file_path = OUTPUT_PATH / "lpdaac-stats.txt"
    output_file_path.touch(exist_ok=True)

    # Get the total size of all the products
    total_products = len(product_dict)
    total_size = sum(
        file_info["file_size"]
        for product_info in product_dict.values()
        for file_info in product_info.values()
        if isinstance(file_info, dict)
    )
    avg_file_size = round((total_size / total_products), 1)

    # Dictionary to store the details of each file type
    file_type_details = {}

    file_types = set()
    # Get the total number of unique file types
    for file_details in product_dict.values():
        if isinstance(file_details, dict):
            for key in file_details:
                if isinstance(file_details[key], dict):
                    file_types.add(key)

    for inner_dict in product_dict.values():
        for file_type, file_info in inner_dict.items():
            if isinstance(file_info, dict) and "file_size" in file_info:
                if file_type not in file_type_details:
                    file_type_details[file_type] = {
                        "file-count": 0,
                        "total-size": 0,
                        "avg-size": 0,
                    }
                file_type_details[file_type]["file-count"] += 1
                file_type_details[file_type]["total-size"] += file_info["file_size"]

    # Calculate the average size for each file type and round the total size
    for details in file_type_details.values():
        details["avg-size"] = (
            round((details["total-size"] / details["file-count"]), 5)
            if details["file-count"] > 0
            else 0
        )
        details["total-size"] = round(details["total-size"], 3)

    collection_dates = set()
    for product_info in product_dict.values():
        for file_info in product_info.values():
            if isinstance(file_info, dict):
                collection_dates.add(file_info["collection_date"])
    total_days = len(collection_dates)
    # Grab the earliest and latest collection dates
    earliest_date = min(collection_dates)
    latest_date = max(collection_dates)

    # Calculate the maximum lengths to make output text look nice
    max_file_type_len = max(len(file_type) for file_type in file_type_details.keys())
    max_file_count_len = (
        max(len(str(details["file-count"])) for details in file_type_details.values())
        + 2
    )
    max_total_size_len = (
        max(len(str(details["total-size"])) for details in file_type_details.values())
        + 2
    )
    max_avg_size_len = (
        max(len(str(details["avg-size"])) for details in file_type_details.values()) + 2
    )
    # Save the stats to the file
    with output_file_path.open("a") as f:
        f.write(f"GEDI Collection: {collection_name}\n\n")
        f.write(f"Total run time: {run_time:.2f} seconds\n")
        f.write(f"Total size of all products: {round(total_size, 1):,} GB\n")
        f.write(f"Average file size of all products: {avg_file_size:,} GB\n")
        f.write(f"Total number of unique product titles: {total_products:,}\n")
        f.write(f"Total number of unique file types: {len(file_type_details.keys())}\n")
        f.write(f"File types: {', '.join(file_type_details.keys())}\n")
        f.write("Count & Average file size by file type:\n")
        for file_type, details in file_type_details.items():
            f.write(
                f'\t{file_type:<{max_file_type_len}} - Number of files: {details["file-count"]:<{max_file_count_len},} | Cumulative file size: {details["total-size"]:<{max_total_size_len},} GB | Avg file size: {details["avg-size"]:<{max_avg_size_len},} GB\n'
            )
        f.write(f"Total number of days in collection: {total_days:,}\n")
        f.write(f"Earliest collection date: {earliest_date}\n")
        f.write(f"Latest collection date: {latest_date}\n")
        f.write(f"{'-'*100}\n\n")


async def fetch_page(session: aiohttp.ClientSession, url: str) -> None | str:
    """
    Fetches the content of a web page using an async HTTP GET request.

    Args:
        session (aiohttp.ClientSession): The aiohttp client session to use for the request.
        url (str): The URL of the web page to fetch.

    Returns:
        str: The content of the web page as a string, or None if the request was unsuccessful.
    """
    async with session.get(url) as response:
        if response.status != 200:
            return None
        else:
            return await response.text()


async def process_page(
    sem: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    base_url: str,
    href: str,
    product_prefix: str,
) -> dict | None:
    """
    Process a page by retrieving its content, parsing the relevant information, and storing it in a dictionary.

    Args:
        sem (Semaphore): A semaphore object used for concurrency control.
        session (aiohttp.ClientSession): An aiohttp ClientSession object for making HTTP requests.
        base_url (str): The base URL of the page.
        href (str): The href value of the page.
        product_prefix (str): The prefix used to identify relevant lines in the page content.

    Returns:
        dict: A dictionary containing the parsed information from the page.

    """
    async with sem:  # acquire semaphore
        product_dict = {}
        page_url = base_url + href
        print(f"Reviewing content on page: {page_url}")
        page_response = await fetch_page(session, page_url)
        if page_response is None:
            print(f"Failed to retrieve content from page: {page_url}")
            return product_dict
        for line in page_response.splitlines():
            if product_prefix in line:
                decoded_line = line
                soup = BeautifulSoup(decoded_line, "html.parser")
                a_tag = soup.find("a")
                if a_tag:
                    href_value = a_tag.get("href")
                    product_title, file_type = href_value.rsplit(".", 1)
                    if "." in product_title:
                        product_title = product_title.rsplit(".", 1)[0]
                    file_size_str = decoded_line.split()[-1]

                    # Grab the collection date from the href_value
                    collection_date = href.split("/")[0]
                    if product_title not in product_dict:
                        product_dict[product_title] = {}
                    product_dict[product_title][file_type] = {
                        "file_size": convert_to_gb(file_size_str),
                        "direct_url": page_url + href_value,
                        "collection_date": collection_date,
                    }
                    total_size = sum(
                        file_info["file_size"]
                        for file_info in product_dict[product_title].values()
                        if isinstance(file_info, dict)
                    )
                    product_dict[product_title]["total_size"] = round(total_size, 3)
    return product_dict


async def crawl_pages(
    base_url: str, a_tags: str, product_prefix: str, collection_name: str
) -> None:
    """
    Crawls through multiple pages and processes the data.

    Args:
        base_url (str): The base URL of the website to crawl.
        a_tags (list): A list of <a> tags containing the URLs of the pages to crawl.
        product_prefix (str): The prefix to be added to the product titles.
        collection_name (str): The name of the GEDI collection.

    Returns:
        None

    """
    collection_start_time = time.time()

    all_results = []
    async with aiohttp.ClientSession() as session:
        # Create a semaphore with X as the maximum number of concurrent tasks
        sem = asyncio.Semaphore(concurrency_limit)
        tasks = []
        for a_tag in a_tags:
            href = a_tag["href"]
            # Pass the semaphore to process_page
            tasks.append(process_page(sem, session, base_url, href, product_prefix))

        # Process tasks in chunks of X
        for i in range(0, len(tasks), sem._value):
            chunk = tasks[i : i + sem._value]
            chunk_results = await asyncio.gather(*chunk)
            all_results.extend(chunk_results)
            # await asyncio.sleep(0.11)  # add delay

    # Merge all results into a single dictionary
    product_dict = {}
    for result in all_results:
        product_dict.update(result)
    # After all pages have been crawled and processed, export the data to a CSV file
    save_stats_to_file(product_dict, collection_name, collection_start_time)
    export_to_csv(product_dict, collection_name)


def get_product_links(url: str = "https://e4ftl01.cr.usgs.gov/") -> list[str]:
    """
    Retrieves a list of product links from the specified URL.

    Args:
        url (str): The URL to scrape for product links. Defaults to "https://e4ftl01.cr.usgs.gov/".

    Returns:
        list[str]: A list of product links found on the webpage.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    product_links = []
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        if href and not href.startswith("?"):  # Exclude links that start with '?'
            product_links.append(url + href)
    return product_links


def main() -> None:
    GEDI_collection = r"https://e4ftl01.cr.usgs.gov/GEDI/"
    collection_links = get_product_links(GEDI_collection)

    start_time = time.time()
    # Loop through each collection links and prepare to extract the product links
    for collection in collection_links:
        base_url = collection
        collection_name = collection.split("/")[-2]
        collection_prefix = collection_name.split(".")[0]

        # grab all the collection product links
        if collection_prefix:
            response = requests.get(base_url)
            if response.status_code != 200:
                print(f"Invalid URL from: {base_url}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            a_tags = soup.find_all("a", href=True)
            asyncio.run(
                crawl_pages(base_url, a_tags, f"{collection_prefix}_", collection_name)
            )
    # Capture the end time of the script and calculate the total run time
    end_time = time.time()
    run_time: float = end_time - start_time
    print(f"Total run time: {run_time:.2f} seconds")


if __name__ == "__main__":
    main()
