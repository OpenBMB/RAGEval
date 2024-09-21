#!/bin/bash

# Parameters
MODEL_NAME="gpt-4o" # Name of the OpenAI model to use
DOMAIN="law"     # Domain for the input data (e.g., law, medical etc.)
LANGUAGE="zh"        # Language for the input data (e.g., zh for Chinese, en for English, etc.)
INPUT_DIR="output/${DOMAIN}/${LANGUAGE}/config" # Directory containing input JSON files
OUTPUT_DIR="output/${DOMAIN}/${LANGUAGE}" # Directory to store the generated QRAs
NUMBER=1 # Number of irrelevant questions to generate
JSON_IDX=0 # Index of the JSON files to process

run_python_script() {
    local model_name=$1
    local domain=$2
    local language=$3
    local input_dir=$4
    local output_dir=$5
    local number=$6
    local json_idx=$7

    echo "Running QRA generation for model: $model_name, domain: $domain, language: $language, input directory: $input_dir, output directory: $output_dir, number of json files to generate: $number, json index: $json_idx"
    python -u code/${domain}/${language}/qra_pipeline_irrelevant.py \
        --model_name "$model_name" \
        --input_dir "$input_dir" \
        --output_dir "$output_dir" \
        --number "$number" \
        --json_idx "$json_idx"
}

# Main execution
run_python_script "$MODEL_NAME" "$DOMAIN" "$LANGUAGE"  "$INPUT_DIR" "$OUTPUT_DIR" "$NUMBER" "$JSON_IDX"

echo "irrelevant QRA generation complete."