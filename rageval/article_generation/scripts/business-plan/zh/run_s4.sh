#!/bin/bash
source ./scripts/business-plan/zh/config.sh

python ./code/business-plan/zh/s4_generate_article_s1a2.py \
    --model_name gpt-3.5-turbo \
    --file_dir_path ${summary_output_dir} \
    --output_dir ${article_output_dir} \
    --json_idx ${json_idx} 