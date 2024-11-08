# Function to get a new token
function generate_token {
    # Check if ~.urs_cookies file exists and delete if it does
    if (Test-Path $env:userprofile/.urs_cookies) {
        Remove-Item $env:userprofile/.urs_cookies
    }
    # Call the Earthdata login endpoint to get a new token
    $response = curl -b $env:userprofile/.urs_cookies -c $env:userprofile/.urs_cookies -L -n https://data.ornldaac.earthdata.nasa.gov/s3credentials | ConvertFrom-Json
    # $response = curl -b $env:userprofile/.urs_cookies -c $env:userprofile/.urs_cookies -L -n https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials | ConvertFrom-Json
    # Replace the space in the expiration date with a 'T' to make it ISO 8601 compliant
    $expiration = $response.expiration.Replace(" ", "T")
    $envString = "ACCESS_KEY_ID=" + $response.accessKeyId + "`nSECRET_ACCESS_KEY=" + $response.secretAccessKey + "`nSESSION_TOKEN=" + $response.sessionToken + "`nEXPIRATION=" + $expiration
    $envString | Out-File (Join-Path $env:userprofile ".env")
}

# Update the rclone config file for a specific profile with the updated access key id, secret access key, and session token
# The latest token details can be found in the .env file in the user's home directory
function update_rclone_config {
    $profile = $args[0]
    $envFile = Join-Path $env:userprofile ".env"
    $env = Get-Content $envFile | ConvertFrom-StringData
    $accessKeyId = $env.ACCESS_KEY_ID
    $secretAccessKey = $env.SECRET_ACCESS_KEY
    $sessionToken = $env.SESSION_TOKEN
    $rcloneConfigFile = Join-Path $env:appdata "/rclone/rclone.conf"
    $rcloneConfig = Get-Content $rcloneConfigFile
    $startLine = $rcloneConfig | Select-String -Pattern "\[$profile\]" -Context 0, 1
    $startLineNumber = [int]$startLine.LineNumber
    # $endLine = $rcloneConfig | Select-String -Pattern "\[" -Context $startLineNumber, 1
    # $endLineNumber =$startLineNumber + 9

    $endLineNumber = $startLineNumber
    while ($endLineNumber -lt $rcloneConfig.Length -and ($rcloneConfig[$endLineNumber] -notmatch '^\s*\[' -or $rcloneConfig[$endLineNumber] -eq '')) {
        $endLineNumber++
    }

    $endLineNumber--

    # Now you can use $startLineNumber and $endLineNumber to get the lines for the profile
    $profileLines = $rcloneConfig[($startLineNumber-1)..$endLineNumber] | ForEach-Object {

        # Check if the current line contains the access key id, secret access key, or session token and update it
        if ($_ -match "access_key_id") {
            $access_key_id_line  = "access_key_id = $accessKeyId"
            $access_key_id_line
        } elseif ($_ -match "secret_access_key") {
            $secret_access_key_line = "secret_access_key = $secretAccessKey"
            $secret_access_key_line
        } elseif ($_ -match "session_token") {
            $session_token_line= "session_token = $sessionToken"
            $session_token_line
            # Save the file with the updated session token
        } else {
            $_
        }
    }

    # prepend the profile name to the beginning of $profileLines
    # $profileLines[0] = "[$profile]"

    # Get the lines before and after the profile but also account for when the profile is at the beginning
    if ($startLineNumber -eq 1) {
        $linesBeforeProfile = @()
    } else {
        $linesBeforeProfile = $rcloneConfig[0..($startLineNumber-2)]
    }
    $linesAfterProfile = $rcloneConfig[($endLineNumber+1)..$rcloneConfig.Length]

    echo $profileLines
    echo $startLineNumber
    echo $endLineNumber
    # Combine the lines before the profile, the updated profile lines, and the lines after the profile
    $profileLines = $linesBeforeProfile + $profileLines + $linesAfterProfile

    # Save the updated rclone config file
    $profileLines | Set-Content $rcloneConfigFile
    Write-Host "Updated rclone config file for profile: $profile"
}

# Example usage
generate_token
# update_rclone_config "earthdata-lp-s3"
update_rclone_config "earthdata-ornl-s3"
