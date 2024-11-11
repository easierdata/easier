#!/bin/bash

# Function to get a new token
generate_token() {
    daac_source="${1}"
    echo "Getting new token for $daac_source"
    # Check if daac_source is ornl or lpdaac
    if [[ "$daac_source" == *"ornl"* ]]; then
        daac_url="https://data.ornldaac.earthdata.nasa.gov/s3credentials"
    else #[[ "$daac_source" == *"lpdaac"* ]]; then
        daac_url="https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials"
    fi

    # Create unique cookie file name based on timestamp variable and save it to the .cookies directory
    timestamp=$(date +"%Y%m%d%H%M%S")
    cookie_file="cookie_$timestamp"
    # make sure the `~/.cookies` directory exists
    mkdir -p ~/.cookies


    # # # Check if ~/.urs_cookies file exists and delete if it does
    # # if [ -f ~/.urs_cookies ]; then
    # #     rm ~/.urs_cookies
    # # fi
    #Check if ~/.cookies/"$cookie_file" file exists and delete if it does
    if [ -f "$cookie_file_path" ]; then
        rm "$cookie_file_path"
    fi
    cookie_file_path=~/.cookies/"$cookie_file"

    # Run the curl command to get the AWS credentials that are saved to .env file in the users home directory.
    response=$(curl -b "$cookie_file_path" -c "$cookie_file_path" -L -n "$daac_url" | jq -r '.')

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
