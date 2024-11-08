#!/bin/bash

# Function to get a new token
generate_token() {
    # Check if ~/.urs_cookies file exists and delete if it does
    if [ -f ~/.urs_cookies ]; then
        rm ~/.urs_cookies
    fi
    # Call the Earthdata login endpoint to get a new token
    response=$(curl -b ~/.urs_cookies -c ~/.urs_cookies -L -n https://data.ornldaac.earthdata.nasa.gov/s3credentials | jq -r '.')
    # response=$(curl -b ~/.urs_cookies -c ~/.urs_cookies -L -n https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials | jq -r '.')
    # Replace the space in the expiration date with a 'T' to make it ISO 8601 compliant
    expiration=$(echo "$response" | jq -r '.expiration' | sed 's/ /T/')
    envString="ACCESS_KEY_ID=$(echo "$response" | jq -r '.accessKeyId')\nSECRET_ACCESS_KEY=$(echo "$response" | jq -r '.secretAccessKey')\nSESSION_TOKEN=$(echo "$response" | jq -r '.sessionToken')\nEXPIRATION=$expiration"
    echo -e "$envString" > ~/.env
}

# Update the rclone config file for a specific profile with the updated access key id, secret access key, and session token
# The latest token details can be found in the .env file in the user's home directory
update_rclone_config() {
    profile=$1
    envFile=~/.env
    accessKeyId=$(grep -oP "(?<=ACCESS_KEY_ID=).*" "$envFile")
    secretAccessKey=$(grep -oP "(?<=SECRET_ACCESS_KEY=).*" "$envFile")
    sessionToken=$(grep -oP "(?<=SESSION_TOKEN=).*" "$envFile")
    rcloneConfigFile=~/.config/rclone/rclone.conf
    startLine=$(grep -n "\[$profile\]" "$rcloneConfigFile" | cut -d: -f1)
    endLine=$(awk "/\[/{n++} n==$startLine" "$rcloneConfigFile")
    endLine=$((endLine-1))

    # Now you can use $startLine and $endLine to get the lines for the profile
    profileLines=$(sed -n "$startLine,${endLine}p" "$rcloneConfigFile" | while IFS= read -r line; do
        # Check if the current line contains the access key id, secret access key, or session token and update it
        if echo "$line" | grep -q "access_key_id"; then
            echo "access_key_id = $accessKeyId"
        elif echo "$line" | grep -q "secret_access_key"; then
            echo "secret_access_key = $secretAccessKey"
        elif echo "$line" | grep -q "session_token"; then
            echo "session_token = $sessionToken"
        else
            echo "$line"
        fi
    done)

    # prepend the profile name to the beginning of $profileLines
    # profileLines=$(echo "$profileLines" | sed "1s/^/[$profile]\n/")

    # Get the lines before and after the profile but also account for when the profile is at the beginning
    if [ "$startLine" -eq 1 ]; then
        linesBeforeProfile=""
    else
        linesBeforeProfile=$(sed -n "1,$((startLine-1))p" "$rcloneConfigFile")
    fi
    linesAfterProfile=$(sed -n "$((endLine+2)),$ p" "$rcloneConfigFile")

    echo "$profileLines"
    echo "$startLine"
    echo "$endLine"
    # Combine the lines before the profile, the updated profile lines, and the lines after the profile
    profileLines=$(echo -e "$linesBeforeProfile\n$profileLines\n$linesAfterProfile")

    # Save the updated rclone config file
    echo "$profileLines" > "$rcloneConfigFile"
    echo "Updated rclone config file for profile: $profile"
}

# Example usage
generate_token
# update_rclone_config "earthdata-lp-s3"
update_rclone_config "earthdata-ornl-s3"
