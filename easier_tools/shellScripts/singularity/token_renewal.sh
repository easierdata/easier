#!/bin/bash

# Function to get a new token
generate_token() {
    # Check if ~/.urs_cookies file exists and delete if it does
    if [ -f ~/.urs_cookies ]; then
        rm ~/.urs_cookies
    fi

    # Run the curl command to get the AWS credentials that are saved to .env file in the users home directory.
    curl -b ~/.urs_cookies -c ~/.urs_cookies -L -n https://data.ornldaac.earthdata.nasa.gov/s3credentials | jq -r '"ACCESS_KEY_ID=" + .accessKeyId + "\nSECRET_ACCESS_KEY=" + .secretAccessKey + "\nSESSION_TOKEN=" + .sessionToken' > ~/.env
    # curl -b ~/.urs_cookies -c ~/.urs_cookies -L -n https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials | jq -r '"ACCESS_KEY_ID=" + .accessKeyId + "\nSECRET_ACCESS_KEY=" + .secretAccessKey + "\nSESSION_TOKEN=" + .sessionToken' > ~/.env
    # Source the .env file
    source ~/.env
}
