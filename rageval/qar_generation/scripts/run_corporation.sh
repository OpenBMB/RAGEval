#!/bin/bash

# Parameters
OUTPUT_DIR="results" # Directory to store the output files
DOMAINS=("medical" "finance" "law") # List of domains
LANGUAGES=("en" "zh") # List of languages
TYPE='qra' # Type of corporation, either 'qra' or 'doc'

# Convert the DOMAINS array to a comma-separated string
DOMAINS_STR=$(IFS=,; echo "${DOMAINS[*]}")
LANGUAGES_STR=$(IFS=,; echo "${LANGUAGES[*]}")

# Function: Run the Python script
run_python_script() {
    local output_dir=$1
    local domains=$2
    local languages=$3
    local type=$4

    echo "Running QRA generation for domains: $domains, languages: $languages, output directory: $output_dir", type: $type
    python -u code/data_processing/${type}_corporation.py \
        --domains "$domains" \
        --languages "$languages" \
        --output_dir "$output_dir"
}

# Main execution
run_python_script "$OUTPUT_DIR" "$DOMAINS_STR" "$LANGUAGES_STR"

echo "$TYPE corporation complete."