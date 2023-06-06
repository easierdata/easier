import random
import requests
import boto3
import subprocess

# TODO: Add type hints. Then try the workflow


# Request data from storage provider web server
def request_data_from_storage_provider(
    http_request_endpoint: str, piece_cid: str, content_cid: str
) -> bytes:
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
        "f01234": "http://www.storageprovider1.com",
        "f05678": "http://www.storageprovider2.com",
        "f09abc": "http://www.storageprovider3.com",
    }
    storage_providers_ids_set = {"f01234", "f05678", "f09abc"}

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
        if storage_provider_id in storage_providers_dict:
            # Try to get the data from the storage provider
            provider_data = request_data_from_storage_provider(
                storage_providers_dict[storage_provider_id], piece_cid, cid
            )

            # If we successfully got data, return it
            if provider_data:
                return provider_data
            else:
                print(
                    f"Unable to get data from Storage Provider ID: {storage_provider_id}"
                )

        else:
            print(
                f"Error: Storage Provider ID: {storage_provider_id} not found in storage_providers dictionary"
            )
            continue

    # If we've gone through all storage providers and haven't found the data, return None
    print("Unable to find data with any storage provider")
    return None


def check_s3_for_data(cid: str) -> bytes:  # Hot layer
    hit = random.randint(0, 1)
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
        data = subprocess.check_output(["ipfs", "cat", cid])
        return data
    except subprocess.CalledProcessError as e:
        print(f"Error: Unable to get data from IPFS: {e}")
        return None


def check_filecoin_for_data(
    cid: str, network_indexer_url="https://cid.contact"
) -> bytes:  # Cold layer
    # We use a network indexer (cid.contact) to find the storage providers that have the CID we are looking for in a storage deal
    api_endpoint = f"{network_indexer_url}/cid/{cid}"
    response = requests.get(api_endpoint)

    if response.status_code == 200:
        data = response.json()
        storage_providers = data["MultihashResults"][0]["ProviderResults"]
        if len(storage_providers) > 0:
            return get_data_from_filecoin(cid, storage_providers)
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
    data = check_filecoin_for_data(cid, piece_cid)
    if data:
        print("Got data from Filecoin")
        return data

    return None


if __name__ == "__main__":
    cid = "QmT6gKjQ7h8C1Vx2JqGQ5JzXV5q7ZyJr7Zu2XVQ5Yk2LQ1"
    piece_cid = "baga6ea4seaq"

    data = get_data(cid, piece_cid)
    if data:
        print(f"Got data: {data}")
    else:
        print("Unable to get data")
