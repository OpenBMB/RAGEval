#!/bin/bash
source ./scripts/business-plan/en/config.sh

run_command() {
    local industry=$1
    local chapter_name=$2
    local json_idx=$3
    python ./code/business-plan/en/s2-1_generate_config.py \
        --industry "${industry}" \
        --data_for_complete ${schema_dir}/${chapter_name}.json \
        --output_dir ${config_output_dir} \
        --json_idx $json_idx &
}

# Define your industries and chapter names
industries=("Technology" "Food & Beverage" "E-commerce" "Healthcare" "Education" "Financial Services" "Consulting" "Real Estate" "Renewable Energy" "Manufacturing" "Transportation" "Tourism" "Media & Entertainment" "Fashion" "Agriculture" "Retail" "Construction" "Fitness" "Software Development" "Professional Services")
chapter_names=("business_plan")

# Loop through and execute in parallel
for industry in "${industries[@]}"; do
    for chapter_name in "${chapter_names[@]}"; do
        run_command "$industry" "$chapter_name" "$json_idx"
    done
done

# Wait for all background processes to complete
wait 