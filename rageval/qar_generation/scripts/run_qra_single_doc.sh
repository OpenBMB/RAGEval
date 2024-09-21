#!/bin/bash

# Parameters
MODEL_NAME="gpt-4o"  # Name of the OpenAI model to use
DOMAIN="finance"     # Domain for the input data (e.g., finance, law, medical etc.)
LANGUAGE="zh"        # Language for the input data (e.g., zh for Chinese, en for English, etc.)
INPUT_DIR="data/${DOMAIN}/${LANGUAGE}/config"  # Directory containing input JSON files
OUTPUT_DIR="output/${DOMAIN}/${LANGUAGE}/config"  # Directory to store the generated QRA files
JSON_IDX=0  # Index of the JSON files to process

# Function: Run the Python script
run_python_script() {
    local model_name=$1
    local domain=$2
    local language=$3
    local input_dir=$4
    local output_dir=$5
    local json_idx=$6

    echo "Running QRA generation for model: $model_name, domain: $domain, language: $language, json index: $json_idx"
    python -u code/${domain}/${language}/qra_pipeline_single_doc.py \
        --model_name "$model_name" \
        --input_dir "$input_dir" \
        --output_dir "$output_dir" \
        --json_idx "$json_idx"
}

# Main execution
run_python_script "$MODEL_NAME" "$DOMAIN" "$LANGUAGE" "$INPUT_DIR" "$OUTPUT_DIR" "$JSON_IDX"

echo "single doc QRA generation complete."