#!/bin/bash

# Get the directory of the current script
script_dir=$(dirname "$0")

# Function to run dataset-worker
run_dataset_worker() {
    # Run the dataset worker and return its output
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string run dataset-worker --concurrency $concurrency_workers --exit-on-error --exit-on-complete" >> "$process_times"
    output=$(/usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --verbose --database-connection-string="$db_connection_string" run dataset-worker --concurrency "$concurrency_workers" --exit-on-error --exit-on-complete 2>&1)
    echo $output
}

# Function to update storage
update_storage() {
    # Source ~/.env
    source ~/.env

    # Update the storage with the new token session details
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string storage update s3 aws --client-scan-concurrency $concurrency_workers --region $REGION_NAME --endpoint $AWS_ENDPOINT --session-token $SESSION_TOKEN --access-key-id $ACCESS_KEY_ID --secret-access-key $SECRET_ACCESS_KEY $storage_name" >> "$process_times"
    /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --verbose --database-connection-string="$db_connection_string" storage update s3 aws --client-scan-concurrency "$concurrency_workers" --region "$REGION_NAME" --endpoint "$AWS_ENDPOINT" --session-token "$SESSION_TOKEN" --access-key-id "$ACCESS_KEY_ID" --secret-access-key "$SECRET_ACCESS_KEY" "$storage_name"
}

# Function to repack failed preperation
repack_preparation() {
    # Source the token renewal script to get a new token
    source "$script_dir/token_renewal.sh"
    generate_token
    update_storage
    init_repack
    # Update storage after generating new token
}

# Function to start repack
init_repack() {
    # Start the pack task.  If the preperation fails to finish packing jobs during `start-scan`, the pack task will need to be called
    echo "Starting the start-pack preparation task..."
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep start-pack $prep_name $storage_name" >> "$process_times"
    singularity --verbose --database-connection-string="$db_connection_string" prep start-pack "$prep_name" "$storage_name"

}

# Function to start daggen task
init_daggen() {
    # Start the daggen task.  If the preperation fails to finish packing jobs during `start-scan`, the daggen task will need to be called
    echo "Starting the start-daggen preparation task..."
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep start-daggen $prep_name $storage_name" >> "$process_times"
    singularity --verbose --database-connection-string="$db_connection_string" prep start-daggen "$prep_name" "$storage_name"
}

# Function to initiate start-scan task
init_start_scan() {
    # Start the start-scan task.  If the preperation fails to finish packing jobs during `start-scan`, the pack task will need to be called
    echo "Starting the start-scan preparation task..."
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep start-scan $prep_name $storage_name" >> "$process_times"
    singularity --verbose --database-connection-string="$db_connection_string" prep start-scan "$prep_name" "$storage_name"
}
