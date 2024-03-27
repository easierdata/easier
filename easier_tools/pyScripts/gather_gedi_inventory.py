# -*- coding: utf-8 -*-
import argparse
import asyncio
import csv
import re
import textwrap
import time
from pathlib import Path

import aiohttp
import requests
import tqdm
from bs4 import BeautifulSoup

# global variables
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "gedi" / "metadata"

# The user credentials that will be used to authenticate access to the data
AUTH_SELECTION = "bearer"  # input("Enter the authentication type (netrc or bearer): ")

# Represents the DAAC data source that will be referenced to parse GEDI data details.
# It can be either `ornl` or `lp` based
DAAC_SOURCE = ""

# dictionary to store the mission name and the corresponding DAAC URLs
GEDI_SOURCES = {
    "ornl": {"url": "https://daac.ornl.gov/daacdata", "mission": "gedi"},
    "lp": {"url": "https://e4ftl01.cr.usgs.gov", "mission": "GEDI"},
}

# Ensure that OUTPUT_PATH exists
Path.mkdir(OUTPUT_PATH, parents=True, exist_ok=True)

# Specify the maximum number of concurrent tasks to assign to a semaphore implementation
concurrency_limit = 15


def get_earthdata_auth(auth_type: str = ["netrc", "token"]):  # -> requests.Session:
    """
    Get the Earthdata authentication token.

    Args:
        type (str): The type of authentication to
            use. Options are 'netrc' or 'Bearer'.

    Returns:
    """
    # Set default values for different auth types
    netrc_cred = None
    headers = None

    if auth_type == "netrc":
        from netrc import netrc

        urs = "urs.earthdata.nasa.gov"
        netrcDir = Path.home() / ".netrc"
        username = netrc(netrcDir).authenticators(urs)[0]
        password = netrc(netrcDir).authenticators(urs)[2]
        netrc_cred = aiohttp.BasicAuth(username, password)
    elif auth_type == "token":
        from os import getenv

        import dotenv

        # Load the .env fileet the value of "BEARER_TOKEN" from the .env file
        dotenv.load_dotenv()
        token = getenv("BEARER_TOKEN")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        raise ValueError("Invalid authentication type. Use 'netrc' or Bearer Token")

    return netrc_cred, headers


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
    # Check if variable is not a string and convert to float
    # Default unit is "M"
    if isinstance(file_size_str, str) and file_size_str[-1].isdigit():
        number = float(file_size_str)
        unit = "M"  # Default unit
    elif isinstance(file_size_str, str):
        number = float(file_size_str[:-1])
        unit = file_size_str[-1]
    else:
        number = float(file_size_str)
        unit = "M"  # Default unit

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
            "last_modified_date",
            "direct_url",
            "directory",
        ]
        writer.writerow(headers)

        # Iterate over the items in the dictionary
        for product_title, product_info in collection_dict.items():
            total_size = product_info["total_size"]
            for file_type, file_info in product_info.items():
                if isinstance(file_info, dict):
                    # Write a row to the CSV file
                    file_size = file_info["file_size"]
                    last_modified_date = file_info["last_modified_date"]
                    direct_url = file_info["direct_url"]
                    directory = file_info["directory"]
                    writer.writerow(
                        [
                            product_title,
                            total_size,
                            file_type,
                            file_size,
                            last_modified_date,
                            direct_url,
                            directory,
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
    output_file_path = OUTPUT_PATH / "gedi-parsing-details.txt"
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

    directories = set()
    for product_info in product_dict.values():
        for file_info in product_info.values():
            if isinstance(file_info, dict):
                directories.add(file_info["directory"])
    total_days = len(directories)
    # Grab the earliest and latest collection dates
    earliest_date = min(directories)
    latest_date = max(directories)

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


def get_product_links(url: str) -> list[str] | None:
    """
    Retrieves a list of product links from the specified URL.

    Args:
        url (str): The URL to scrape for product links.

    Returns:
        list[str]: A list of product links found on the webpage.
    """
    product_links = []
    response = requests.get(url)
    if response.status_code == 200:
        valid_hrefs = remove_invalid_hrefs(response.text)
        product_links = [url + href for href in valid_hrefs]
        return product_links
    else:
        print("Failed to retrieve directory listing")
        return None


def extract_file_details(soup_obj) -> tuple:
    """
    Extracts the file details from a BeautifulSoup object.

    Args:
        soup_obj (BeautifulSoup): The BeautifulSoup object representing the HTML page.

    Returns:
        tuple: A tuple containing the product title and file type extracted from the file name.
    """
    file_name_from_line = soup_obj.find("a", href=True).get("href")
    product_title, file_type = file_name_from_line.rsplit(".", 1)
    # Ensure that the product title does not contain a period
    if "." in product_title:
        product_title = product_title.rsplit(".", 1)[0]
    return product_title, file_type


def filter_lines_from_response(response_to_filter):
    """
    Filters lines from the given response based on valid hrefs.

    Args:
        response_to_filter (str): The response to filter.

    Returns:
        list: A list of lines from the response that match the valid hrefs pattern.
    """
    valid_hrefs = remove_invalid_hrefs(response_to_filter)
    valid_hrefs_pattern = "|".join(re.escape(href) for href in valid_hrefs)
    pattern = re.compile(f'<a href="({valid_hrefs_pattern})">')
    return [line for line in response_to_filter.splitlines() if pattern.search(line)]


def get_directory_from_url(url: str) -> str:
    """
    Extracts the directory name from a given URL.

    Args:
        url (str): The URL from which to extract the directory name.

    Returns:
        str: The directory name extracted from the URL.
    """
    return url.rsplit("/")[-2]


def parse_lpdaac_line(response_text, base_url) -> dict:
    """
    Parses the response text and extracts metadata information for each product title.

    Args:
        response_text (str): The response text containing the metadata information.
        base_url (str): The base URL for constructing the direct URL of each product.

    Returns:
        dict: A dictionary containing the parsed metadata information for each product file.
            The dictionary has the following structure:
              {
                  product_title: {
                      file_type: {
                          "last_modified_date": str,
                          "file_size": float,
                          "directory": str,
                          "direct_url": str
                      },
                      "total_size": float
                  },
                  ...
    """
    parsed_lines_dict = {}
    lines = filter_lines_from_response(response_text)
    for line in lines:
        soup_to_parse = BeautifulSoup(line, features="html.parser")
        # Extract other details from soup object and instantiate the product_dict with the product details.
        product_title, file_type = extract_file_details(soup_to_parse)
        if product_title not in parsed_lines_dict:
            parsed_lines_dict[product_title] = {}
        # Extract file size and modified data from the line
        file_size = line.split()[-1]
        last_modified_date = line.split()[-3]

        # Assign the product details to the product_dict
        parsed_lines_dict[product_title][file_type] = {
            "file_size": convert_to_gb(file_size),
            "last_modified_date": last_modified_date,
            "directory": get_directory_from_url(base_url),
            "direct_url": f"{base_url}/{product_title}.{file_type}",
        }

        # Calculate the total size of all files for each given product title.
        total_size = sum(
            file_info["file_size"]
            for file_info in parsed_lines_dict[product_title].values()
            if isinstance(file_info, dict)
        )
        parsed_lines_dict[product_title]["total_size"] = round(total_size, 3)

    return parsed_lines_dict


def parse_ornl_line(response_text, base_url) -> dict:
    """
    Parses the response text and extracts metadata information for each product file found on ORNL DAAC.

    Args:
        response_text (str): The response text containing the HTML content.
        base_url (str): The base URL of the product files.

    Returns:
        dict: A dictionary containing the parsed metadata information for each product file.
              The dictionary has the following structure:
              {
                  product_title: {
                      file_type: {
                          "last_modified_date": str,
                          "file_size": float,
                          "directory": str,
                          "direct_url": str
                      },
                      "total_size": float
                  },
                  ...
              }
    """
    parsed_lines_dict = {}
    lines = list(filter_lines_from_response(response_text))
    for line in lines:
        soup_to_parse = BeautifulSoup(line, features="html.parser")
        # Find all 'tr' tags in the line which contain the file name, size, and date modified
        tr_tags = soup_to_parse.find_all("tr")
        # Extract the values and remove non-breaking space
        # Remove empty strings and strip the values of leading/trailing whitespaces
        file_details = [
            td.text.replace("\xa0", "") for tr in tr_tags for td in tr.find_all("td")
        ]
        file_details = [value.strip() for value in file_details if value]
        # Unpack and assign each item to a separate variable
        _, modified_date, file_size = file_details
        # Extract other details from soup object and instantiate the product_dict with the product details.
        product_title, file_type = extract_file_details(soup_to_parse)
        if product_title not in parsed_lines_dict:
            parsed_lines_dict[product_title] = {}

        parsed_lines_dict[product_title][file_type] = {
            "last_modified_date": modified_date,
            "file_size": convert_to_gb(file_size),
            "directory": get_directory_from_url(base_url),
            "direct_url": f"{base_url}/{product_title}.{file_type}",
        }

        total_size = sum(
            file_info["file_size"]
            for file_info in parsed_lines_dict[product_title].values()
            if isinstance(file_info, dict)
        )
        parsed_lines_dict[product_title]["total_size"] = round(total_size, 3)
    return parsed_lines_dict


def remove_invalid_hrefs(response_text: str) -> list:
    """
    Removes invalid hrefs from the response HTML.

    Args:
        response (Response): The response object containing the HTML.

    Returns:
        list: A list of valid hrefs.
    """
    valid_hrefs = []
    soup = BeautifulSoup(response_text, "html.parser")
    for a_tag in soup.find_all("a", href=True):
        if not any(s in a_tag.get("href") for s in ["?", "http"]):
            if "Parent Directory" not in a_tag.contents:
                href = a_tag.get("href")
                valid_hrefs.append(href)
    return valid_hrefs


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
            # check if response.real_url is valid if the response was was not 200
            print(
                f"Failed to retrieve content from page: {url}. Status code: {response.status}"
            )
            # Retry session with the real_url value
            return None
        else:
            return await response.text()


async def process_page(
    sem: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    page_url: str,
) -> dict | None:
    """
    Process a page by retrieving its content, parsing the relevant information, and storing it in a dictionary.

    NOTE: Currently this method is designed to work with the GEDI mission products that are
    on the ORNL LP DAACs.

    Args:
        sem (Semaphore): A semaphore object used for concurrency control.
        session (aiohttp.ClientSession): An aiohttp ClientSession object for making HTTP requests.
        page_url (str): The base URL of the page containing html that will be scraped.

    Returns:
        dict: A dictionary containing the parsed information from the page.

    """
    async with sem:  # acquire semaphore
        product_dict = {}
        page_response_text = await fetch_page(session, page_url)

        # If the page response is not false or None, parse the content
        if page_response_text:
            if DAAC_SOURCE == "ornl":
                product_dict = parse_ornl_line(page_response_text, page_url)
            elif DAAC_SOURCE == "daac":
                product_dict = parse_lpdaac_line(page_response_text, page_url)
    return product_dict


async def crawl_pages(
    collection_url: str, hrefs: list[str], collection_name: str
) -> None:
    """
    Crawls through multiple pages and processes the data.

    Args:
        collection_url (str): The collection URL containing one or more directories representing pages to be parsed.
        hrefs (list): A list of <a> tags containing the URLs of the pages to crawl.
        collection_name (str): The name of the collection that will be parsed.

    Returns:
        None

    """
    collection_start_time = time.time()
    all_results = []

    # Set the token for the Authorization header
    netrc_auth, headers_auth = get_earthdata_auth(auth_type=AUTH_SELECTION)

    async with aiohttp.ClientSession(auth=netrc_auth, headers=headers_auth) as session:
        # Create a semaphore with X as the maximum number of concurrent tasks
        sem = asyncio.Semaphore(concurrency_limit)
        tasks = []
        for href in hrefs:
            product_page_url = collection_url + href
            # Pass the semaphore to process_page in batches per the concurrency limit
            tasks.append(process_page(sem, session, product_page_url))

        # Process tasks in chunks based on the concurrency limit set for the semaphore.
        print(
            f"Hold tight! Parsing content from {len(tasks)} pages for the collection {collection_name}."
        )
        for i in tqdm.tqdm(range(0, len(tasks), sem._value)):
            chunk = tasks[i : i + sem._value]
            chunk_results = await asyncio.gather(*chunk)
            all_results.extend(chunk_results)

    # Merge all results into a single dictionary
    product_dict = {}
    for result in all_results:
        product_dict.update(result)
    # After all pages have been crawled and processed, export the data to a CSV file
    print(f"Exporting results for {collection_name} in the directory {OUTPUT_PATH}.")
    save_stats_to_file(product_dict, collection_name, collection_start_time)
    export_to_csv(product_dict, collection_name)


def extract_gedi_details() -> None:

    parser = argparse.ArgumentParser(
        prog="crawl_pages",
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            f"""\
        Description:

        A crawler that scans through the LP.DAAC or ORNL.DAAC http endpoint, to extract relevant information on the GEDI mission data products.

        Basic details such as the file name, type, size and url endpoint to download are captured and saved down to {OUTPUT_PATH}. Details on each collection are saved as separate files, prefixed with the collection name, and a summary file containing additional details about each collection.

        Credentials are REQUIRED to access http endpoints. Additional details below regarding authentication types.

        NOTE: The script uses asyncio to handle multiple requests concurrently, and the number of concurrent tasks is limited to 15.

        Additional information:

        - The script will prompt you to enter the authentication type and DAAC source to scrape the GEDI product details. The authentication type can be either `netrc` or `token`.

        - Generate a netrc file with the Easiertools poetry script tool by running the following command `poetry run update_netrc_file`

        - You can find more information on generating a token from the Earthdata Login at the following link: https://urs.earthdata.nasa.gov/documentation/for_users/user_token

        """
        ),
    )

    parser.add_argument(
        "--auth-type",
        type=str,
        default="netrc",
        required=False,
        help=r"[netrc | token]     Specify the authentication type to access Earthdata http endpoints.",
    )

    parser.add_argument(
        "--daac",
        type=str,
        default="lp",
        required=False,
        help=r"[ornl | lp]     Specify the DAAC source to scrape the GEDI prodcut details.",
    )

    args = parser.parse_args()

    # Set the global variables based on the user input
    global DAAC_SOURCE, AUTH_SELECTION

    DAAC_SOURCE = args.daac
    AUTH_SELECTION = args.auth_type

    DAAC_URL = GEDI_SOURCES[DAAC_SOURCE]["url"]
    MISSION_NAME = GEDI_SOURCES[DAAC_SOURCE]["mission"]

    collection_links = get_product_links(f"{DAAC_URL}/{MISSION_NAME}/")

    start_time = time.time()
    # Loop through each collection for the selected mission and prepare to extract the product links
    for collection in collection_links:
        base_url = collection
        collection_name = collection.split("/")[-2]

        # grab all the collection product links
        try:
            response = requests.get(base_url)
            if response.status_code != 200:
                print(f"Invalid URL from: {base_url}")
                continue
            valid_hrefs = remove_invalid_hrefs(response.text)
            asyncio.run(crawl_pages(base_url, valid_hrefs, collection_name))
        except Exception as e:
            print(f"Failed to process collection: {collection_name}. Reason: {e}")
            import traceback

            traceback.print_exc()
            continue
    # Capture the end time of the script and calculate the total run time
    end_time = time.time()
    run_time: float = end_time - start_time
    print(f"Total run time: {run_time:.2f} seconds")


if __name__ == "__main__":
    extract_gedi_details()
