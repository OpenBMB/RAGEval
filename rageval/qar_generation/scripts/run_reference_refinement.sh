#!/bin/bash

# Parameters
DOMAINS=("finance" "law" "medical") # List of domains
LANGUAGES=("en" "zh") # List of languages
MODEL_NAME='gpt-4o' # Model name
TYPE='single_doc' # Type of reference refinement, either 'single_doc' or 'multi_doc'

# Convert the DOMAINS array to a comma-separated string
DOMAINS_STR=$(IFS=,; echo "${DOMAINS[*]}")
LANGUAGES_STR=$(IFS=,; echo "${LANGUAGES[*]}")

# Function: Run the Python script
run_python_script() {
    local domains=$1
    local languages=$2
    local model_name=$3
    local type=$4

    echo "Running QRA generation for domains: $domains, languages: $languages, model: $model_name", type: $type
    python -u code/reference_refinement/reference_refinement_${type}.py \
        --domains "$domains" \
        --languages "$languages"\
        --model_name "$model_name"
}

# Main execution
run_python_script "$DOMAINS_STR" "$LANGUAGES_STR" "$MODEL_NAME" "$TYPE"

echo "reference refinement complete."