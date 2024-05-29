#!/bin/bash

# -----------------------------------------------------------------------------------------
# Script based on this gist: https://gist.github.com/jcace/f811078f5cc110425cb317b3b87da654
# Generate a directory of sample data at a provided output folder of the following
#    - A folder containing N number of "small" files at defined size in bytes
#    - A folder with an empty folder inside
#    - A single "large" file at a defined size in GB
# -----------------------------------------------------------------------------------------

# Modify variables below to customize file generation
small_file_count=10 # Count of files generated
small_file_size=600000000 # File size in bytes; 1,000,000 bytes = 1MB
large_file_size=5 # File size in GB

# Check if an argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_directory>"
    exit 1
fi

# Name of the base directory
BASE_DIR="$1"

# Function to create a large number of small files
create_small_files() {
    local target_dir="$1"
    local count="$2"
    local file_size="$3"

    for i in $(seq 1 $count); do
        head -c $file_size /dev/urandom > "${target_dir}/file_${i}"
    done
}

# Function to create a large file
create_large_file() {
    local target_file="$1"
    local file_size_gb="$2"

    head -c $(($file_size_gb * 1024**3)) /dev/urandom > "$target_file"
}

# Create the base directory
mkdir -p "$BASE_DIR"

# Create a large number of small files
mkdir -p "${BASE_DIR}/small_files"
create_small_files "${BASE_DIR}/small_files" $small_file_count $small_file_size

# Create nested folders
mkdir -p "${BASE_DIR}/nested/empty_folder"

# Create a large file
create_large_file "${BASE_DIR}/large_file" $large_file_size

echo "Directory structure created in ${BASE_DIR}!"
