#!/bin/bash

# Set the GOLOG_LOG environment variable:
#   - GOLOG_LOG_LEVEL options: debug, info, warn, error, dpanic, panic, fatal
#   - GOLOG_LOG_FMT    - example values: color, nocolor, json
#   - More details can be found at https://github.com/ipfs/go-log
export GOLOG_LOG_LEVEL='info'

#---------------------------------------------------------------------------------------------------------
### Script Parameters
# --root-dir - Define the root directory where test cases will be saved.
#           DEFAULTS to current working directory if no value is passed in.
# --sample-data-path - Path to where the sample data is. NOTE: Ensure is a valid S3 bucket URL if passing in the param `--use-aws`
#           DEFAULTS to a folder named “sample_data” based on the value passed to `root-dir`.
# --case-name - Title of the test case.  Useful when you need to run multiple test cases in a row and understand how different settings impact overall performance time.
#           DEFAULTS to “dataset” if no value is passed in.
# --concurrency-process - Set the max number of CPU cores for all Singularity commands that utilize concurrent processing.
#           DEFAULTS to 1 if no value is passed in.
# --db-connection-string - Override the default DB connection by pointing to a specific instance.
#           DEFAULTS to sqlite3 DB that’s created in a folder named “db” found in `root-dir`.
# --storage-name - Name of the storage profile.
#           DEFAULTS to "<case-name>-source” if no value is passed in.
# --prep-name - Name of the preparation profile.
#           DEFAULTS to "<case-name>-prep” if no value is passed in.
# --output-path - An optional argument to override the default output path for the generated output CAR files.
#           By default, the cars files are saved to the directory specified for the argument, `--root-dir`.
#           Pass in a directory path for the agrument `--output-path` If you want to save the cars files to a different location.
#           Example:
#               output_cars_dir="/tmp/performance_test/output_cars"
#               --output-path="$output_cars_dir"
#
### Optional Argument flags. Passing in will trigger the following actions:
# --use-aws - Pass in this argument if you would like to use an S3 bucket instead of a local directory.  NOTE:  that `--sample-data-path` argument is a valid S3 bucket URL.
# --create-output - Pass in this argument if you would like to override inline-preparation by generating the output car files.
# --reset-db - An optional argument to perform a hard-reset of the database. This is useful when referencing an existing database to create new storage sources and preparations.
# --repack - Optional argument to perform the action of repacking the source content due to a failed `start-scan` task. This happens typically due to **Session Tokens** expiring.
#            Passing in this argument will update the specified storage source. This is useful when referencing an existing database to create new storage sources and preparations.
#
#   NOTE: If you are passing in the `--repack` flag, ensure that `--storage-name` and `--prep-name` are the same as the original source and preparation names. Account for `--case-name` if
#         it was set in previous runs as that is the suffix to the store and prep profile names.  Additionally, ensure that the `--root-dir` is correctly referenced as the default
#         sqlite3 DB is stored there and that `--sample-data-path` is the same as the original source path.
#   IMPORTANT: When using the `--repack` flag, it's crucial to ensure that the Singularity instance is properly configured to handle the repack operation. This includes having sufficient
#              disk space and CPU resources available. Failure to ensure this may result in incomplete or failed repack operations.
#
#---------------------------------------------------------------------------------------------------------

### Define the root directory for the performance results to be saved to
results_dir="/path/to/results_dir"

### Define the output directory for the generated cars
# Note: This is an optional parameter if you want to save the cars files to a different location
# output_cars_dir="/path/to/output_cars_dir"

# # Define the sample data directory or AWS S3 bucket path
# If you are passing in the `--use-aws` flag, the `sample_source_path` should be an AWS S3 bucket path.
# Otherwise, the `sample_source_path` should be a local directory path.
sample_source_path="/path/to/local/sample_data"

### AWS S3 bucket path examples
# sample_source_path="ornl-cumulus-prod-protected/gedi/GEDI_L4B_Gridded_Biomass_V2_1/"
# sample_source_path="ornl-cumulus-prod-protected/above/ABoVE_LVIS_VegetationStructure/"
# sample_source_path3="ornl-cumulus-prod-protected/gedi/GEDI_L4A_AGB_Density_GW/"
# sample_source_path3="lp-prod-protected/GEDI01_B.002/GEDI01_B_2023066100801_O23969_03_T09843_02_005_02_V002/"
#---------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------
# Source the script containing the function
script_dir=$(dirname "$0")
source "$script_dir/singularity-data-prep.sh"
#---------------------------------------------------------------------------------------------------------

prepare_data --storage-name="GEDI_L4B_Gridded_Biomass_V2_1_source" --prep-name="GEDI_L4B_Gridded_Biomass_V2_1_output__" --case-name="GEDI_L4B_Gridded_Biomass_V2_1" --root-dir="$results_dir" --sample-data-path="$sample_source_path" --reset-db --create-output --use-aws

### If you would like to prepare multiple datasets, you can run additional `prepare_data` commands below.
# prepare_data --storage-name="GEDI_L4A_AGB_Density_GW_source" --prep-name="GEDI_L4A_AGB_Density_GW_output" --case-name="GEDI_L4A_AGB_Density_GW" --root-dir="$results_dir" --sample-data-path="$sample_source_path3" --use-aws
# prepare_data --storage-name="GEDI_L1B_source" --prep-name="GEDI_L1B_source_output" --case-name="GEDI_L1B_source" --root-dir="$results_dir" --sample-data-path="$sample_source_path" --create-output --reset-db --use-aws
