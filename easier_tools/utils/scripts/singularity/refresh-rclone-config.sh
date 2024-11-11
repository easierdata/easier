#!/bin/bash

# Function to check if the profile exists in the rclone config file
function check_profile_exists {
    profile_name=$1
    rcloneConfigFile="$HOME/.config/rclone/rclone.conf"
    if [ ! -f "$rcloneConfigFile" ]; then
        echo "Error: rclone config file not found."
        exit 1
    fi
    profileExists=$(grep -E "\[$profile_name\]" "$rcloneConfigFile")
    if [ -z "$profileExists" ]; then
        echo "Error: Profile '$profile_name' does not exist in the rclone config file."
        echo "Valid profiles are:"
        grep -E "^\[.*\]" "$rcloneConfigFile" | sed 's/^\[\(.*\)\]/\1/'
        exit 1
    fi
}

# Function to get a new token
function generate_token {
    profile_name=$1
    if [[ $profile_name =~ "lp" ]]; then
        daac_endpoint="data.lpdaac.earthdatacloud.nasa.gov"
    elif [[ $profile_name =~ "ornl" ]]; then
        daac_endpoint="data.ornldaac.earthdata.nasa.gov"
    else
        echo "Profile does not specify which DAAC to generate tokens. Check to see if the profile contains 'lp' or 'ornl'."
        exit 1
    fi
    if [ -f "$HOME/.urs_cookies" ]; then
        rm "$HOME/.urs_cookies"
    fi
    url="https://$daac_endpoint/s3credentials"
    response=$(curl -b "$HOME/.urs_cookies" -c "$HOME/.urs_cookies" -L -n "$url")
    if [ -z "$response" ]; then
        echo "Failed to get a response from the server."
        return
    fi
    expiration=$(echo "$response" | jq -r '.expiration')
    if [ -z "$expiration" ]; then
        echo "The response does not contain an expiration field."
        return
    fi
    expiration=$(echo "$expiration" | sed 's/ /T/')
    accessKeyId=$(echo "$response" | jq -r '.accessKeyId')
    secretAccessKey=$(echo "$response" | jq -r '.secretAccessKey')
    sessionToken=$(echo "$response" | jq -r '.sessionToken')
    envString="ACCESS_KEY_ID=$accessKeyId\nSECRET_ACCESS_KEY=$secretAccessKey\nSESSION_TOKEN=$sessionToken\nEXPIRATION=$expiration"
    echo -e "$envString" > "$HOME/.env"
}

# Update the rclone config file for a specific profile with the updated access key id, secret access key, and session token
# The latest token details can be found in the .env file in the user's home directory
function update_rclone_config {
    profile_name=$1

    # Open the rclone config file and extract the profile section that needs to be updated
    rcloneConfigFile="$HOME/.config/rclone/rclone.conf"
    startLine=$(grep -nE "^\[$profile_name\]" "$rcloneConfigFile" | cut -d: -f1)
    endLine=$(grep -nE "^\[" "$rcloneConfigFile" | grep -A1 -m1 "^$startLine" | tail -n1 | cut -d: -f1)
    endLine=$((endLine - 1)) # Adjust end line to capture up to previous section

    # Extract the profile section that needs to be updated
    profileLines=$(sed -n "$startLine,$endLine p" "$rcloneConfigFile")

        # Check if the 'type' property exists and is set to 's3'
    profileType=$(echo "$profileLines" | grep -E "^type\s*=" | cut -d'=' -f2 | xargs)

    if [[ "$profileType" == "s3" ]]; then
        generate_token "$profile_name"
    else
        echo "storage type error for $profile_name"
        echo "The property 'type' is missing or not assigned the value 's3'. Currently set to: $profileType "
        echo "Exiting..."
        return
    fi

        # Read in the token details from the .env file
    envFile="$HOME/.env"
    accessKeyId=$(grep -E "^ACCESS_KEY_ID=" "$envFile" | cut -d'=' -f2)
    secretAccessKey=$(grep -E "^SECRET_ACCESS_KEY=" "$envFile" | cut -d'=' -f2)
    sessionToken=$(grep -E "^SESSION_TOKEN=" "$envFile" | cut -d'=' -f2)

    # Update profileLines with new values or add them if missing
    # NOTE: Escape special characters in variables. Using by using the `@` as the delimiter in sed avoids conflicts
    #       with characters that may be present in the values
    if ! echo "$profileLines" | grep -q "access_key_id ="; then
        profileLines="$profileLines"$'\n'"access_key_id = $accessKeyId"
    else
        profileLines=$(echo "$profileLines" | sed -E "s@(access_key_id = ).*@\1$accessKeyId@")
    fi

    if ! echo "$profileLines" | grep -q "secret_access_key ="; then
        profileLines="$profileLines"$'\n'"secret_access_key = $secretAccessKey"
    else
        profileLines=$(echo "$profileLines" | sed -E "s@(secret_access_key = ).*@\1$secretAccessKey@")
    fi

    if ! echo "$profileLines" | grep -q "session_token ="; then
        profileLines="$profileLines"$'\n'"session_token = $sessionToken"
    else
        profileLines=$(echo "$profileLines" | sed -E "s@(session_token = ).*@\1$sessionToken@")
    fi
    # Create a temporary file for the new content
    tempFile=$(mktemp)

    # Write content before the section
    head -n $((startLine - 1)) "$rcloneConfigFile" > "$tempFile"

    # Write the updated section
    echo "$profileLines" >> "$tempFile"

    # Write content after the section
    tail -n +$((endLine)) "$rcloneConfigFile" >> "$tempFile"

    # Replace the original file with the updated content
    mv "$tempFile" "$rcloneConfigFile"

    echo "Updated configuration for profile '$profile_name'."
}

# Check if profile_name is provided
if [ -z "$1" ]; then
    echo "Error: You must provide a value for the profile_name parameter."
    exit 1
fi

# Check if the profile exists in the rclone config file
check_profile_exists "$1"

# Example usage
update_rclone_config "$1"
