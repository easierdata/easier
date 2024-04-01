#!/bin/bash
module load rclone
# Folder where you want to save the downloaded files
destination_folder="../../data/landsat/piknik"

# Create the folder if it doesn't exist
mkdir -p "$destination_folder"

# Loop through each line in file_list.txt
while read -r line; do
    # Use rclone to download the file
    rclone copy --ignore-existing --transfers 16 "${line}" "${destination_folder}"
done < $1
