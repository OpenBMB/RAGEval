#!/bin/bash
source ./scripts/business-plan/zh/config.sh

python ./code/business-plan/zh/s3-1_generate_outline.py \
    --model_name gpt-3.5-turbo \
    --file_dir_path ${config_output_dir} \
    --output_dir ${outline_output_dir} \
    --json_idx ${json_idx} 