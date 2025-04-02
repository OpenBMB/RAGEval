#!/bin/bash
source ./scripts/business-plan/en/config.sh

python ./code/business-plan/en/s1_filter_schema.py \
    --schema_file ${schema_dir}/business_plan.json \
    --output_dir ${schema_dir} 