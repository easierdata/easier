#!/bin/bash

# Function to upload a file to S3 with a key based on its IPFS CID
upload_file() {
    local filename=$1
    local bucket=$2

    # Add the file to IPFS and get the CID
    local cid=$(ipfs add -nq "$filename")

    # Upload the file to S3 with the CID as the key
    aws s3 cp "$filename" "s3://$bucket/$cid"
}

# Usage: sh ./upload_to_s3_with_CID_key <filename> <bucket>
# Example: sh ./upload_to_s3_with_CID_key.sh ../../data/landsat/ls9/LC09_L1TP_004069_20220628_20220629_02_T1/LC09_L1TP_004069_20220628_20220629_02_T1_B1.TIF landsat-warm-layer
upload_file $1 $2
