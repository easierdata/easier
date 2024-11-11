#!/bin/bash

# Other files to source
# Get the directory of the current script
script_dir=$(dirname "$0")
source "$script_dir/token_renewal.sh"

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

# Function to repack failed preparation
repack_preparation() {
    local storage_data_path="$1"
    generate_token "$storage_data_path"
    update_storage
    init_repack
    # Update storage after generating new token
}

# Function to start repack
init_repack() {
    # Start the pack task.  If the preparation fails to finish packing jobs during `start-scan`, the pack task will need to be called
    echo "Starting the start-pack preparation task..."
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep start-pack $prep_name $storage_name" >> "$process_times"
    singularity --verbose --database-connection-string="$db_connection_string" prep start-pack "$prep_name" "$storage_name"
}

# Function to start daggen task
init_daggen() {
    # Start the daggen task.  If the preparation fails to finish packing jobs during `start-scan`, the daggen task will need to be called
    echo "Starting the start-daggen preparation task..."
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep start-daggen $prep_name $storage_name" >> "$process_times"
    singularity --verbose --database-connection-string="$db_connection_string" prep start-daggen "$prep_name" "$storage_name"
}

# Function to initiate start-scan task
init_start_scan() {
    # Start the start-scan task.  If the preparation fails to finish packing jobs during `start-scan`, the pack task will need to be called
    echo "Starting the start-scan preparation task..."
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep start-scan $prep_name $storage_name" >> "$process_times"
    singularity --verbose --database-connection-string="$db_connection_string" prep start-scan "$prep_name" "$storage_name"
}


# Function to check if a given storage profile exists
check_storage_exists() {
    local storage_profile_name="$1"
    local storage_data_path="$2"
    local is_aws_source="$3"
    # Check if the storage profile exists
    cmd_output=$(singularity --database-connection-string="$db_connection_string" storage list 2>&1)
    echo "Checking if the storage profile exists..." >> "$process_times"
    if ! echo "$cmd_output" | grep -q "$storage_profile_name"; then
        if [ $is_aws_source -eq 1 ]; then
            generate_token "$storage_data_path"
            create_aws_storage_profile $storage_profile_name $storage_data_path
        else
            create_local_storage_profile $storage_profile_name $storage_data_path
        fi
    else
        echo "The profile "$storage_profile_name" already exists. Skipping..."  >> "$process_times"
    fi
}

# Function to create an aws storage profile
create_aws_storage_profile() {
    local aws_storage_name="$1"
    local aws_sample_data_path="$2"
    echo "Creating the profile "$aws_storage_name"..."  >> "$process_times"
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string storage create s3 aws --client-scan-concurrency $concurrency_workers --region $REGION_NAME --endpoint $AWS_ENDPOINT --session-token $SESSION_TOKEN --access-key-id $ACCESS_KEY_ID --secret-access-key $SECRET_ACCESS_KEY --name $aws_storage_name --path $aws_sample_data_path" >> "$process_times"
    /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --verbose --database-connection-string="$db_connection_string" storage create s3 aws --client-scan-concurrency "$concurrency_workers" --region "$REGION_NAME" --endpoint "$AWS_ENDPOINT" --session-token "$SESSION_TOKEN" --access-key-id "$ACCESS_KEY_ID" --secret-access-key "$SECRET_ACCESS_KEY" --name "$aws_storage_name" --path "$aws_sample_data_path"
}

create_local_storage_profile() {
    local local_storage_name="$1"
    local local_sample_data_path="$2"
    echo "Creating the profile "$local_storage_name"..."  >> "$process_times"
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string storage create local --client-scan-concurrency $concurrency_workers --name $local_storage_name --path $local_sample_data_path" >> "$process_times"
    /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --verbose --database-connection-string="$db_connection_string" storage create local --client-scan-concurrency "$concurrency_workers" --name "$local_storage_name" --path "$local_sample_data_path"
}

# Function to check if a given preparation profile exists
check_prep_exists() {
    local prep_profile_name="$1"
    local storage_profile_name="$2"
    # Check if the preparation profile exists
    cmd_output=$(singularity --database-connection-string="$db_connection_string" prep list 2>&1)
    echo "Checking if the preparation profile exists..." >> "$process_times"
    if ! echo "$cmd_output" | grep -q "$prep_profile_name"; then
        create_prep_profile "$prep_profile_name" "$storage_profile_name"
    else
        echo "The profile "$prep_profile_name" already exists. Skipping..."  >> "$process_times"
    fi
}

create_prep_profile() {
    local prep_profile_name="$1"
    local storage_profile_name="$2"
    echo "Creating the profile "$prep_profile_name"..."  >> "$process_times"
    # Create the preparation profile
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep create --name $prep_name --source $storage_profile_name" >> "$process_times"
    /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --verbose --database-connection-string="$db_connection_string" prep create --name "$prep_profile_name" --source "$storage_profile_name"
}

# Check if preparation profiles contains a given output profile storage
check_prep_output_profile() {
    local prep_profile_name="$1"
    local output_profile_name="$2"
    # Check if the preparation profile contains the output profile storage
    cmd_output=$(singularity --database-connection-string="$db_connection_string" prep status "$prep_profile_name" 2>&1)
    echo "Checking if the preparation profile contains the output profile storage..."
    if ! echo "$cmd_output" | grep -q "$output_profile_name"; then
        add_output_profile "$prep_profile_name" "$output_profile_name"
    else
        echo "The profile "$output_profile_name" already exists in the preparation profile "$prep_profile_name". Skipping..."  >> "$process_times"
    fi
}

# Function to add an output profile to a preparation profile
add_output_profile() {
    local prep_profile_name="$1"
    local output_profile_name="$2"
    echo "Adding the output profile "$output_profile_name" to the preparation profile "$prep_profile_name"..."  >> "$process_times"
    # Add the output profile to the preparation profile
    echo "Command: singularity --verbose --database-connection-string=$db_connection_string prep attach-output $prep_profile_name $output_profile_name" >> "$process_times"
    /usr/bin/time -o "$process_times" -a -f "Command Execution Time:\n\t Real: %E\n\t User: %U\n\t System: %S" singularity --verbose --database-connection-string="$db_connection_string" prep attach-output "$prep_profile_name" "$output_profile_name"
}
