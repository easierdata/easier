import random
import requests
import tkinter as tk
from tkinter import ttk

# import boto3
import subprocess


# Request data from storage provider web server
def request_data_from_storage_provider(
    http_request_endpoint: str, piece_cid: str, content_cid: str
) -> bytes:
    return b"Data from storage provider"
    request_url = (
        f"{http_request_endpoint}?piece_cid={piece_cid}&content_cid={content_cid}"
    )

    response = requests.get(request_url)

    if response.status_code == 200:
        data = response.content
        return data

    else:
        print(f"Error: Received status code {response.status_code} from web server")
        return None


def get_data_from_filecoin(cid: str, piece_cid: str, storage_providers: set) -> bytes:
    # Create a storage provider dictionary where the primary key is the storage provider ID and the value is the HTTP web server endpoint
    storage_providers_dict = {
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKZ": "localhost:8080/fetch",
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKF8": "http://www.storageprovider2.com",
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKG": "http://www.storageprovider3.com",
    }
    storage_providers_ids_set = {
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKZ",
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKF8",
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKG",
    }

    # Find storage providers that are not in the storage_providers_ids_set
    unknown_providers = storage_providers - storage_providers_ids_set
    if unknown_providers:
        print(f"Unknown storage providers: {unknown_providers}")

    # Perform a set intersection to only include storage providers that are in the storage_providers__ids_set
    storage_providers = storage_providers & storage_providers_ids_set

    if len(storage_providers) == 0:
        print("Error: No storage providers found")
        return None

    # Convert the set back to a list and randomly shuffle the storage providers that have the data
    storage_providers = list(storage_providers)
    random.shuffle(storage_providers)

    # Iterate over the shuffled list of storage providers
    for storage_provider_id in storage_providers:
        print(
            f"Trying Storage Provider ID: {storage_provider_id} found via cid.contact API"
        )
        provider_data = request_data_from_storage_provider(
            storage_providers_dict[storage_provider_id], piece_cid, cid
        )

        if provider_data:
            return provider_data
        else:
            print(f"Unable to get data from Storage Provider ID: {storage_provider_id}")

    # If we've gone through all storage providers and haven't found the data, return None
    print("Unable to find data with any storage provider")
    return None


def check_s3_for_data(cid: str) -> bytes:  # Hot layer
    # hit = random.randint(0, 1)
    hit = False
    if hit:
        return b"Data from S3"
    else:
        return None
    # # Create a session using your AWS credentials
    # s3 = boto3.resource("s3")

    # # Assume your bucket name is "my-bucket"
    # bucket = s3.Bucket("my-bucket")

    # # Try to get the object
    # try:
    #     obj = bucket.Object(cid)
    #     data = obj.get()["Body"].read()
    #     return data
    # except Exception as e:
    #     print(f"Error: Unable to get data from S3: {e}")
    #     return None


def check_ipfs_for_data(cid: str) -> bytes:  # Warm layer
    # Try to get the data
    try:
        data = subprocess.check_output(["ipfs", "cat", cid], timeout=1)
        return data
    except subprocess.CalledProcessError as e:
        print(f"Error: Unable to get data from IPFS: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("Error: IPFS request timed out")
        return None


def check_filecoin_for_data(
    cid: str, piece_cid, network_indexer_url="https://cid.contact"
) -> bytes:  # Cold layer
    # We use a network indexer (cid.contact) to find the storage providers that have the CID we are looking for in a storage deal
    def process_storage_provider_response(response: dict) -> set:
        storage_providers = set()
        for result in response:
            provider_id = result["Provider"]["ID"]
            storage_providers.add(provider_id)
        return storage_providers

    api_endpoint = f"{network_indexer_url}/cid/{cid}"
    response = requests.get(api_endpoint)

    if response.status_code == 200:
        data = response.json()
        storage_providers = data["MultihashResults"][0]["ProviderResults"]
        if len(storage_providers) > 0:
            return get_data_from_filecoin(
                cid, piece_cid, process_storage_provider_response(storage_providers)
            )
        else:
            print("No storage providers found for CID")
            return None


def get_data(cid: str, piece_cid: str) -> bytes:
    # Check the hot layer for the data
    data = check_s3_for_data(cid)
    if data:
        print("Got data from S3")
        return data

    # Check IPFS for the data
    data = check_ipfs_for_data(cid)
    if data:
        print("Got data from IPFS")
        return data

    # Check Filecoin for the data
    data = check_filecoin_for_data(cid=cid, piece_cid=piece_cid)
    if data:
        print("Got data from Filecoin")
        return data

    return None


def get_data_gui():
    cid = cid_entry.get()
    piece_cid = piece_cid_entry.get()
    data = get_data(cid, piece_cid)
    if data:
        result_label.config(text=f"Got data: {data}")
    else:
        result_label.config(text="Unable to get data")


def run_gui():
    global root, cid_entry, piece_cid_entry, result_label
    root = tk.Tk()
    root.geometry("400x300")  # Define window size
    root.title("Data Fetcher")  # Add a title to the window

    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 12))  # Increase font size for labels
    style.configure("TButton", font=("Arial", 12))  # Increase font size for buttons

    frame = ttk.Frame(root, padding="10 10 10 10")  # Add padding to the frame
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    cid_label = ttk.Label(frame, text="CID:")
    cid_label.grid(row=0, column=0, sticky="w")
    cid_entry = ttk.Entry(frame)
    cid_entry.grid(row=0, column=1, sticky="w")

    piece_cid_label = ttk.Label(frame, text="Piece CID:")
    piece_cid_label.grid(row=1, column=0, sticky="w")
    piece_cid_entry = ttk.Entry(frame)
    piece_cid_entry.grid(row=1, column=1, sticky="w")

    get_data_button = ttk.Button(frame, text="Get Data", command=get_data_gui)
    get_data_button.grid(row=2, column=0, columnspan=2)

    result_label = ttk.Label(frame, text="")
    result_label.grid(row=3, column=0, columnspan=2)

    root.columnconfigure(0, weight=1)  # Makes the column expandable
    root.rowconfigure(0, weight=1)  # Makes the row expandable

    root.mainloop()


if __name__ == "__main__":
    # To run as standalone script, uncomment the following two lines:
    # cid = "bafybeigoe4ss23hrahns7sbqus6tas4ovvnhupmrnrym5zluu2ssg5yj5u"
    # piece_cid = "baga6ea4seaqfnimohx7eefyfgc3m5hvhy4hmdukyvlhw4vwacwbdlvpfvod4wky"
    # data = get_data(cid, piece_cid)
    # if data:
    #     print(f"Got data: {data}")
    # else:
    #     print("Unable to get data")

    # To run in GUI mode, uncomment the following line:
    run_gui()
