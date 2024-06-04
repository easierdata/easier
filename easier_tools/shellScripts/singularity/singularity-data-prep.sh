#!/bin/bash

# Other files to source
# Get the directory of the current script
script_dir=$(dirname "$0")
# source "$script_dir/token_renewal.sh"
source "$script_dir/_singularity_helpers.sh"

## DEFAULT GLOBAL VALUES
# Files names to store results
PROCESS_TIMES_FILENAME="process-times.txt"
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# S3 Authentication Options
#    --access-key-id value           AWS Access Key ID. [$ACCESS_KEY_ID]
#    --acl value                     Canned ACL used when creating buckets and storing or copying objects. [$ACL]
#    --endpoint value                Endpoint for S3 API. [$ENDPOINT]
#    --env-auth                      Get AWS credentials from runtime (environment variables or EC2/ECS meta data if no env vars). (default: false) [$ENV_AUTH]
#    --help, -h                      show help
#    --location-constraint value     Location constraint - must be set to match the Region. [$LOCATION_CONSTRAINT]
#    --region value                  Region to connect to. [$REGION]
#    --secret-access-key value       AWS Secret Access Key (password). [$SECRET_ACCESS_KEY]
#    --server-side-encryption value  The server-side encryption algorithm used when storing this object in S3. [$SERVER_SIDE_ENCRYPTION]
#    --sse-kms-key-id value          If using KMS ID you must provide the ARN of Key. [$SSE_KMS_KEY_ID]
#    --storage-class value           The storage class to use when storing new objects in S3. [$STORAGE_CLASS]
#    --session-token value           An AWS session token. [$SESSION_TOKEN]
REGION_NAME="us-west-2"
AWS_ENDPOINT="s3."$REGION_NAME".amazonaws.com"
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# Function to run performance test
prepare_data() {

    # Initialize named parameters with default values
    use_aws=0
    create_output=0
    reset_db=0
    repack=0
    root_dir=""
    sample_data_path=""
    output_path=""
    case_name="dataset"
    concurrency_workers=1
    db_connection_string=""
    storage_name=""
    prep_name=""
    output_storage_name=""

    # Parse named parameters
    for arg in "$@"
    do
        case $arg in
            --root-dir=*)
            root_dir="${arg#*=}"
            shift
            ;;
            --sample-data-path=*)
            sample_data_path="${arg#*=}"
            shift
            ;;
            --case-name=*)
            case_name="${arg#*=}"
            shift
            ;;
            --concurrency-process=*)
            concurrency_workers="${arg#*=}"
            shift
            ;;
            --db-connection-string=*)
            db_connection_string="${arg#*=}"
            shift
            ;;
            --storage-name=*)
            storage_name="${arg#*=}"
            shift
            ;;
            --prep-name=*)
            prep_name="${arg#*=}"
            shift
            ;;
            --use-aws)
            use_aws=1
            shift
            ;;
            --create-output)
            create_output=1
            shift
            ;;
            --output-path=*)
            output_path="${arg#*=}"
            shift
            ;;
            --reset-db)
            reset_db=1
            shift
            ;;
            --repack)
            repack=1
            shift
            ;;
            *)
            echo "Invalid argument: $arg"
            ;;
        esac
    done

    # Define the names for storage, prep, output profiles if no value is passed in
    if [ -z "$storage_name" ]; then
        storage_name="$case_name-source"
    fi

    if [ -z "$prep_name" ]; then
        prep_name="$case_name-prep"
    fi

    if [ -z "$output_storage_name" ]; then
        output_storage_name="$case_name-output"
    fi

    # Define the root directory path if it's not provided
    if [ -z "$root_dir" ]; then
        root_dir=$(pwd)
    fi

    # Create directory to store results case results. The directory name is the case name
    caseDir="$root_dir/$case_name"

    # Create the directory if it does not exist
    if [ ! -d "$caseDir" ]; then
        mkdir -p "$caseDir"
    # else # Remove the directory if it exists
    #     rm -rf "$caseDir"
    #     mkdir -p "$caseDir"
    fi

    # Set file path for process times file
    process_times="$caseDir/$PROCESS_TIMES_FILENAME"
    start=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "Start time: $start" >> "$process_times"

    # Define the sample data directory path if it's not provided
    if [ -z "$sample_data_dir" ]
    then
        sample_data_dir="$root_dir/sample_data"
    fi

    # Check if create_output is enabled and output_path is not specified
    if [ "$create_output" -eq 1 ] && [ -z "$output_path" ]; then
        # Set default output path
        output_path="$root_dir/$case_name-cars"
        echo "Output creation is enabled."
        echo "Output path: $output_path"
    fi

    # Define the database connection string for SQLite if it's not provided
    if [ -z "$db_connection_string" ]; then

        # Create and check if db directory if it does not exist. create the directory if it does not exist
        db_dir="$root_dir/db"
        if [ ! -d "$db_dir" ]; then
            mkdir -p "$db_dir"
        fi

        db_connection_string="sqlite:$root_dir/db/singularity.db"
        echo "Defaulting to SQLite database. To explore content, navigate to $root_dir/db/ once the process is complete."
    fi

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Write defined variables to the process times file
    echo "Defined Variables:" >> "$process_times"
    host_statements=("db_connection_string: $db_connection_string" "case_name: $case_name" "root_dir: $root_dir" "sample_data_path: $sample_data_path" "storage_name: $storage_name" "prep_name: $prep_name" "concurrency_workers: $concurrency_workers" "")
    for statement in "${host_statements[@]}"; do
        echo "$statement" >> "$process_times"
    done


    if [ $repack -eq 1 ]; then
        echo "Starting RESCAN/REPACK process to look for changes..."
        if [ $use_aws -eq 1 ]; then
            while true; do

                repack_preparation "$sample_data_path"
                output=$(run_dataset_worker)
                if [[ $output == *"ExpiredToken"* ]]; then
                    time_check=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
                    echo "Token expired. Renewing...($time_check)" >> "$process_times"
                    echo "Ran into a problem during the RESCAN/REPACK process. trying again...($time_check)"
                else
                    break
                fi
            done
        else
            # Initiate the start-pack process
            init_repack
            run_dataset_worker
        fi
    else
        echo "Starting the data preparation process..."
        ### ................................................................................................................................................................................................................................................
        # 1) Initialize the database to a manifest of CID details of our storages
        # Reset the database so it's empty. If a SQLite database is used, the database file is automatically created if it doesn't exist.
        if [ $reset_db -eq 1 ]; then
            echo "Command: singularity --database-connection-string=$db_connection_string admin reset --really-do-it" >> "$process_times"
            /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --database-connection-string="$db_connection_string" admin reset --really-do-it
        else
            echo "Initializing the database if it doesn't already exist..."
            echo "Command: singularity --database-connection-string=$db_connection_string admin init" >> "$process_times"
            /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --database-connection-string="$db_connection_string" admin init
        fi
        ### ................................................................................................................................................................................................................................................

        ### ................................................................................................................................................................................................................................................
        # 2) Create storage source profile
        check_storage_exists "$storage_name" "$sample_data_path" "$use_aws"
        ### ................................................................................................................................................................................................................................................


        ### ................................................................................................................................................................................................................................................
        # 2.a) Create output storage profile
        # This is OPTIONAL and is not required. It's only needed if you do not want to perform `Inline Preparation`
        if [ $create_output -eq 1 ]; then

            # # Delete output storage directory if it exists
            # if [ -d "$output_path" ]; then
            #     rm -rf "$output_path"
            # fi

            # Create output storage directory
            mkdir -p "$output_path"

            # Create output storage source
            check_storage_exists "$output_storage_name" "$output_path" 0
        fi
        ### ................................................................................................................................................................................................................................................

        ### ................................................................................................................................................................................................................................................
        # 3) Create dataset preparation profile
        check_prep_exists "$prep_name" "$storage_name"

        if [ $create_output -eq 1 ]; then
        # Optionally check if the dataset preparation profile contains an output storage profile and attach it if it doesn't
            check_prep_output_profile "$prep_name" "$output_storage_name"
        fi
        ### ................................................................................................................................................................................................................................................


        ### ................................................................................................................................................................................................................................................
        # 4) Initialize the dataset preparation tasks and run the Task Runners

        # Initiate the start-scan process
        init_start_scan

        # Check if $use_aws is true
        if [ $use_aws -eq 1 ]; then
            while true; do
                output=$(run_dataset_worker)
                if [[ $output == *"ExpiredToken"* ]]; then
                    time_check=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
                    echo "Token expired. Renewing...($time_check)" >> "$process_times"
                    echo "Token expired. Renewing...($time_check)"
                    repack_preparation "$sample_data_path"
                else
                    break
                fi
            done
        else
            run_dataset_worker
        fi
    fi

    # starting daggen process is only needed if create_output is enabled
    if [ $create_output -eq 1 ]; then
        # # Initiate the start-daggen process and run the dataset worker
        init_daggen
        run_dataset_worker
    fi
    ### ................................................................................................................................................................................................................................................

    # # Initiate the start-daggen process and run the dataset worker
    # init_daggen
    # run_dataset_worker

    # 5) Reviewing the results
    # List the pieces from the scanned preparation
    singularity --verbose --database-connection-string="$db_connection_string" prep list-pieces "$prep_name"

    end=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "End time: $end" >> "$process_times"

    start=$(date -d"$start" +%s)
    end=$(date -d"$end" +%s)
    duration=$((end - start))
    echo -e "Duration: $duration seconds\n\n" >> "$process_times"
}
