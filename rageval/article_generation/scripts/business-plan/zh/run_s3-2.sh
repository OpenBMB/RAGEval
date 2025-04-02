#!/bin/bash
source ./scripts/business-plan/zh/config.sh

python ./code/business-plan/zh/s3-2_generate_company_info.py \
    --model_name gpt-3.5-turbo \
    --file_dir_path ${outline_output_dir} \
    --output_dir ${summary_output_dir} \
    --json_idx ${json_idx} 