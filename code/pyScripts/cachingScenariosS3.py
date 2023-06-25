import random
import requests
import tkinter as tk
import subprocess
import boto3

IN_GUI_MODE = False  # Override in __main__

MY_S3_AUTH = {
    "aws_access_key_id": "MY_AWS_ACCESS_KEY_ID",
    "aws_secret_access_key": "MY_AWS_SECRET_ACCESS_KEY",
    "endpoint_url": "http://localhost:9000",
    "bucket_name": "my-bucket",
}


# Request data from storage provider web server
def request_data_from_resource(
    auth_dict: str, piece_cid: str, content_cid: str
) -> bytes:
    if auth_dict["s3"]:
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=auth_dict["s3"]["aws_access_key_id"],
            aws_secret_access_key=auth_dict["s3"]["aws_secret_access_key"],
            endpoint_url=auth_dict["s3"]["endpoint_url"],
            bucket_name=auth_dict["s3"]["bucket_name"],
        )

        try:
            obj = s3.Object(piece_cid)
            data = obj.get()["Body"].read()
            return data
        except Exception as e:
            log_message(f"Error: Unable to get data from S3: {e}")
            return None


def get_data_from_filecoin(
    content_cid: str, piece_cid: str, storage_providers: set
) -> bytes:
    # Create a storage provider dictionary where the primary key is the storage provider ID and the value is the HTTP web server endpoint
    storage_providers_ids_set = {
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKZ",
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKF8",
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKG",
    }

    auth_dict = {
        "12D3KooWQY8k3XoH76BPPPXsrP5BWzTHpfC78u9aHS5FdTx2EXKF8": {
            "http_web_server": {
                "endpoint": "http://localhost:5000",
            }
        }
    }

    # Find storage providers that are not in the storage_providers_ids_set
    unknown_providers = storage_providers - storage_providers_ids_set
    if unknown_providers:
        log_message(f"Unknown storage providers: {unknown_providers}")

    # Perform a set intersection to only include storage providers that are in the storage_providers__ids_set
    storage_providers = storage_providers & storage_providers_ids_set

    if len(storage_providers) == 0:
        log_message("Error: No storage providers found")
        return None

    # Convert the set back to a list and randomly shuffle the storage providers that have the data
    storage_providers = list(storage_providers)
    random.shuffle(storage_providers)

    # Iterate over the shuffled list of storage providers
    for storage_provider_id in storage_providers:
        log_message(
            f"Trying Storage Provider ID: {storage_provider_id} found via cid.contact API"
        )
        provider_data = request_data_from_resource(auth_dict, piece_cid, content_cid)

        if provider_data:
            return provider_data
        else:
            log_message(
                f"Unable to get data from Storage Provider ID: {storage_provider_id}"
            )

    # If we've gone through all storage providers and haven't found the data, return None
    log_message("Unable to find data with any storage provider")
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
    #     log_message(f"Error: Unable to get data from S3: {e}")
    #     return None


def check_ipfs_for_data(cid: str) -> bytes:  # Warm layer
    # Try to get the data
    try:
        data = subprocess.check_output(["ipfs", "cat", cid], timeout=1)
        return data
    except subprocess.CalledProcessError as e:
        log_message(f"Error: Unable to get data from IPFS: {e}")
        return None
    except subprocess.TimeoutExpired:
        log_message("Error: IPFS request timed out")
        return None


def find_storage_providers_for_cid(cid: str) -> set:
    network_indexer_endpoint = f"https://cid.contact/cid/{cid}"
    response = requests.get(network_indexer_endpoint)

    if response.status_code == 200:
        data = response.json()
        storage_providers_response = data["MultihashResults"][0]["ProviderResults"]
        storage_providers_ids_set = {
            result["Provider"]["ID"] for result in storage_providers_response
        }
        return storage_providers_ids_set
    else:
        log_message("Error: Unable to get data from cid.contact API")
        return set()


def check_filecoin_for_data(
    cid: str,
    piece_cid,
) -> bytes:
    storage_providers_ids = find_storage_providers_for_cid(cid)

    if len(storage_providers_ids) > 0:
        return get_data_from_filecoin(cid, piece_cid, storage_providers_ids)
    else:
        log_message("No storage providers found for CID")
        return None


def get_data(content_cid: str, piece_cid: str) -> bytes:
    # Check the hot layer for the data
    log_message("Checking hot layer (S3) for data")

    data = check_s3_for_data(auth_dict=MY_S3_AUTH, content_cid=content_cid)
    if data:
        log_message("Got data from S3")
        return data
    log_message("Unable to get data from S3")

    # Check IPFS for the data
    log_message("Checking warm layer (IPFS) for data")
    data = check_ipfs_for_data(content_cid)
    if data:
        log_message("Got data from IPFS")
        return data
    log_message("Unable to get data from IPFS")

    # Check Filecoin for the data
    log_message("Checking cold layer (Filecoin) for data")
    data = check_filecoin_for_data(content_cid=content_cid, piece_cid=piece_cid)
    if data:
        log_message("Got data from Filecoin")
        return data
    log_message("Unable to get data from Filecoin")

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
    global root, cid_entry, piece_cid_entry, result_label, log_text
    root = tk.Tk()
    root.geometry("600x300")  # Define window size
    root.resizable(True, True)
    root.title("Data Fetcher")  # Add a title to the window

    style = tk.ttk.Style()
    style.configure("TLabel", font=("Arial", 12))  # Increase font size for labels
    style.configure("TButton", font=("Arial", 12))  # Increase font size for buttons

    frame = tk.ttk.Frame(root, padding="10 10 10 10")  # Add padding to the frame
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    frame.columnconfigure(1, weight=1)

    cid_label = tk.ttk.Label(frame, text="CID:")
    cid_label.grid(row=0, column=0, padx=(100, 0), sticky="w")
    cid_entry = tk.ttk.Entry(frame, width=30)  # Set the width of the entry field
    cid_entry.grid(row=0, column=1, padx=(0, 100), sticky="e")
    cid_entry.insert(0, "bafybeigoe4ss23hrahns7sbqus6tas4ovvnhupmrnrym5zluu2ssg5yj5u")

    piece_cid_label = tk.ttk.Label(frame, text="Piece CID:")
    piece_cid_label.grid(row=1, column=0, padx=(100, 0), sticky="w")
    piece_cid_entry = tk.ttk.Entry(frame, width=30)  # Set the width of the entry field
    piece_cid_entry.grid(row=1, column=1, padx=(0, 100), sticky="e")
    piece_cid_entry.insert(
        0, "baga6ea4seaqfnimohx7eefyfgc3m5hvhy4hmdukyvlhw4vwacwbdlvpfvod4wky"
    )

    get_data_button = tk.ttk.Button(frame, text="Get Data", command=get_data_gui)
    get_data_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    result_label = tk.ttk.Label(frame, text="")
    result_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))

    log_text = tk.scrolledtext.ScrolledText(frame, width=100, height=10)
    log_text.grid(row=4, column=0, columnspan=2, pady=(10, 0))

    root.columnconfigure(0, weight=1)  # Makes the column expandable
    root.rowconfigure(0, weight=1)  # Makes the row expandable

    root.mainloop()


def log_message(message: str):
    """Log a message. If in GUI mode, update the GUI; otherwise, print to the console."""
    if IN_GUI_MODE:
        log_text.insert(tk.END, message + "\n")
        log_text.see(tk.END)  # Auto-scroll to the end
    else:
        print(message)


if __name__ == "__main__":
    # To run as standalone script, uncomment the following two lines:
    # cid = "bafybeigoe4ss23hrahns7sbqus6tas4ovvnhupmrnrym5zluu2ssg5yj5u"
    # piece_cid = "baga6ea4seaqfnimohx7eefyfgc3m5hvhy4hmdukyvlhw4vwacwbdlvpfvod4wky"
    # data = get_data(cid, piece_cid)
    # if data:
    #     print(f"Got data: {data}")
    # else:
    #     print("Unable to get data")

    # To run in GUI mode, uncomment the following lines:
    IN_GUI_MODE = True
    run_gui()
