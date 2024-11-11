#!/bin/bash

# Function to get a new token
generate_token() {
    daac_source="${1}"
    echo "Getting new token for $daac_source"
    # Check if daac_source is ornl or lpdaac
    if [[ "$daac_source" == *"ornl"* ]]; then
        daac_url="data.ornldaac.earthdata.nasa.gov"
    elif [[ "$daac_source" == *"lp"* ]]; then
        daac_url="data.lpdaac.earthdatacloud.nasa.gov"
    else:
        echo "Invalid DAAC source. Please provide a valid source."
        return 1
    fi

    # Parse the response and save the values to variables
    accessKeyId=$(echo $response | jq -r '.accessKeyId')
    secretAccessKey=$(echo $response | jq -r '.secretAccessKey')
    sessionToken=$(echo $response | jq -r '.sessionToken')
    # Note: The expiration time is missing the 'T' between the date and time.  This will need to be added to the expiration time.
    expiration=$(echo $response | jq -r '.expiration' | tr ' ' 'T')

    # echo "Access Key ID: $accessKeyId | Secret Access $secretAccessKey | Session Token: $sessionToken | Expiration: $expiration"
    # Construct the env variables and save to the .env file in the users home directory
    envString="ACCESS_KEY_ID=$accessKeyId\nSECRET_ACCESS_KEY=$secretAccessKey\nSESSION_TOKEN=$sessionToken\nEXPIRATION=$expiration"
    echo -e $envString > $HOME/.env

    # Source the .env file
    source ~/.env
}
