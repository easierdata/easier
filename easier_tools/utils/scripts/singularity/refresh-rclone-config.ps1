<#
    .SYNOPSIS
    Refreshes the rclone config file with a new token for a specific profile containing "s3" in the profile name.

    .DESCRIPTION
    This script is used to refresh the rclone config file with a new token for a specific profile containing "s3" in the profile name. It retrieves a new token from the Earthdata login endpoint and updates the rclone config file with the new access key id, secret access key, and session token.

    .PARAMETER profile_name
    The name of the profile in the rclone config file to refresh.

    .NOTES
    Version:        1.0

    .EXAMPLE
    PS> refresh-rclone-config.ps1 -profile_name "lp-s3"

    This command will refresh the rclone config file for the "lp-s3" profile with a new token, but only if the profile exists in the rclone config file and the string 's3'.

    .LINK
    Earthdata Login: https://urs.earthdata.nasa.gov/
    Rclone: https://rclone.org/
    Easier Tools: https://github.com/easier/easier


#>

param (
    [string]$profile_name
)
# Check if profile_name is provided
if (-not $profile_name) {
    Write-Host "Error: You must provide a value for the profile_name parameter."
    exit 1
}
# Function to check if the profile exists in the rclone config file
function Check_ProfileExists {
    param (
        [string]$profile_name
    )
    $rcloneConfigFile = Join-Path $env:appdata "/rclone/rclone.conf"
    if (-not (Test-Path $rcloneConfigFile)) {
        Write-Host "Error: rclone config file not found."
        exit 1
    }
    $rcloneConfig = Get-Content $rcloneConfigFile
    $profileExists = $rcloneConfig -match "\[$profile_name\]"

    if (-not $profileExists) {
        Write-Host "Error: Profile '$profile_name' does not exist in the rclone config file."
        Write-Host "Valid profiles are:"
        $rcloneConfig | ForEach-Object {
            if ($_ -match '^\[(.+?)\]') {
                Write-Host $matches[1]
            }
        }
        exit 1
    }
    return $profileExists
}
# Function to get a new token
function generate_token {
    param (
        [string]$profile_name
    )
    # Determine the DAAC name based on the profile
    if ($profile_name -match "lp") {
        $daac_endpoint = "data.lpdaac.earthdatacloud.nasa.gov"
    } elseif ($profile_name -match "ornl") {
        $daac_endpoint = "data.ornldaac.earthdata.nasa.gov"
    } else {
        Write-Host "Profile does not specify which DAAC to generate tokens. Check to see if the profile contains 'lp' or 'ornl'."
        exit 1
    }
    # Check if ~.urs_cookies file exists and delete if it does
    if (Test-Path $env:userprofile/.urs_cookies) {
        Remove-Item $env:userprofile/.urs_cookies
    }
    # Call the Earthdata login endpoint to get a new token
    $url = "https://$daac_endpoint./s3credentials"
    $response = curl -b $env:userprofile/.urs_cookies -c $env:userprofile/.urs_cookies -L -n $url | ConvertFrom-Json
    if ($null -eq $response) {
        Write-Host "Failed to get a response from the server."
        return
    }
    if ($null -eq $response.expiration) {
        Write-Host "The response does not contain an expiration field."
        return
    }
    # Replace the space in the expiration date with a 'T' to make it ISO 8601 compliant
    $expiration = $response.expiration.Replace(" ", "T")
    $envString = "ACCESS_KEY_ID=" + $response.accessKeyId + "`nSECRET_ACCESS_KEY=" + $response.secretAccessKey + "`nSESSION_TOKEN=" + $response.sessionToken + "`nEXPIRATION=" + $expiration
    $envString | Out-File (Join-Path $env:userprofile ".env")
}
# Update the rclone config file for a specific profile with the updated access key id, secret access key, and session token
# The latest token details can be found in the .env file in the user's home directory
function update_rclone_config {
    param (
        [string]$profile_name
    )
    if ($profile_name -match "s3") {
        generate_token -profile_name $profile_name
    } else {
        Write-Warning "Profile does not specify S3 storage. Tokens will not be generated."
        return
    }
    $envFile = Join-Path $env:userprofile ".env"
    $env = Get-Content $envFile | ConvertFrom-StringData
    $accessKeyId = $env.ACCESS_KEY_ID
    $secretAccessKey = $env.SECRET_ACCESS_KEY
    $sessionToken = $env.SESSION_TOKEN
    $rcloneConfigFile = Join-Path $env:appdata "/rclone/rclone.conf"
    $rcloneConfig = Get-Content $rcloneConfigFile
    $startLine = $rcloneConfig | Select-String -Pattern "\[$profile_name\]" -Context 0, 1
    $startLineNumber = [int]$startLine.LineNumber
    $endLineNumber = $startLineNumber
    while ($endLineNumber -lt $rcloneConfig.Length -and ($rcloneConfig[$endLineNumber] -notmatch '^\s*\[' -or $rcloneConfig[$endLineNumber] -eq '')) {
        $endLineNumber++
    }
    $endLineNumber--
    $profileLines = $rcloneConfig[($startLineNumber-1)..$endLineNumber] | ForEach-Object {
        if ($_ -match "access_key_id") {
            "access_key_id = $accessKeyId"
        } elseif ($_ -match "secret_access_key") {
            "secret_access_key = $secretAccessKey"
        } elseif ($_ -match "session_token") {
            "session_token = $sessionToken"
        } else {
            $_
        }
    }
    if ($startLineNumber -eq 1) {
        $linesBeforeProfile = @()
    } else {
        $linesBeforeProfile = $rcloneConfig[0..($startLineNumber-2)]
    }
    $linesAfterProfile = $rcloneConfig[($endLineNumber+1)..$rcloneConfig.Length]
    $profileLines = $linesBeforeProfile + $profileLines + $linesAfterProfile
    $profileLines | Set-Content $rcloneConfigFile
    Write-Host "Updated rclone config file for profile: $profile_name"
}
# Check if the profile exists in the rclone config file
if (-not (Check_ProfileExists -profile_name $profile_name)) {
    Write-Host "Error: Profile '$profile_name' does not exist in the rclone config file."
    exit 1
}
# Example usage
update_rclone_config -profile_name $profile_name
