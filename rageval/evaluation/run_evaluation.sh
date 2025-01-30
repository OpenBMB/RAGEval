#!/bin/bash

# Parameters
NUM_WORKERS=5 # the number of workers to use for parallel processing for evaluation
LANGUAGE="auto" # the language of the input data, en or zh
INPUT_BASE_URL="./data/"
USE_MODEL="gpt-4o"
OUTPUT_BASE_URL="./result/intermediate_result/"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
export BASE_URL="" # if none, set to empty string
# Input files and output file list 
INPUT_FILES=("example_finance_en_gpt-4o.jsonl") # file name of the input data
KEYPOINT_VERSION="v2" # default version of the paper

# List of metrics to process
METRICS=("keypoint_metrics") #("rouge-l" "precision" "recall" "eir" "keypoint_metrics")

# Function: Get line count of a file
get_line_count() {
    local file=$1
    if [[ -f "$file" ]]; then
        wc -l < "$file"
    else
        echo 0
    fi
}

# Process each metric for each input file
for INPUT_FILE in "${INPUT_FILES[@]}"; do
    FULL_INPUT_PATH="${INPUT_BASE_URL}${INPUT_FILE}"
    echo "Processing file: $FULL_INPUT_PATH"

    for METRIC in "${METRICS[@]}"; do
        OUTPUT_FILE="${INPUT_FILE%.*}_${METRIC}_intermediate.jsonl"
        FULL_OUTPUT_PATH="${OUTPUT_BASE_URL}${OUTPUT_FILE}"

        # Check if input file exists
        if [[ ! -f "$FULL_INPUT_PATH" ]]; then
            echo "Error: Input file $FULL_INPUT_PATH does not exist."
            exit 1
        fi
        echo "Processing metric: $METRIC"
        echo "Output file: $FULL_OUTPUT_PATH"

        # Set USE_OPENAI based on the metric
        if [[ "$METRIC" == "keypoint_metrics" ]]; then
            USE_OPENAI="--use_openai"
            VERSION="$KEYPOINT_VERSION"
        else
            USE_OPENAI=""
            USE_MODEL=""
            VERSION=""
        fi

        # Initial line counts
        input_line_count=$(get_line_count "$FULL_INPUT_PATH")
        output_line_count=$(get_line_count "$FULL_OUTPUT_PATH")

        # Run Python script until line counts match
        while [[ "$input_line_count" -ne "$output_line_count" ]]; do
            echo "Processing $FULL_INPUT_PATH for metric $METRIC..."
            python main.py --input_file "$FULL_INPUT_PATH" --output_file "$FULL_OUTPUT_PATH" --num_workers $NUM_WORKERS --metric "$METRIC" --language "$LANGUAGE" $USE_OPENAI --model "$USE_MODEL" --version "$VERSION"
            
            # Get updated line counts
            input_line_count=$(get_line_count "$FULL_INPUT_PATH")
            output_line_count=$(get_line_count "$FULL_OUTPUT_PATH")
            
            if [[ "$input_line_count" -ne "$output_line_count" ]]; then
                echo "Line counts do not match for $FULL_INPUT_PATH ($METRIC). Waiting for 3 minutes before retrying..."
                sleep 180
            fi
        done

        echo "Processing complete for $FULL_INPUT_PATH ($METRIC). Input and output line counts match."
    done
done

echo "All files and metrics processed."

python process_intermediate.py

echo "Intermediate results processed. Results are stored in ./result/final_result.jsonl"