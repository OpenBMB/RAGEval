#!/bin/bash
source ./scripts/finance/zh/config.sh
for json_id in $json_idx; do
    python ./code/finance/zh/s4_generate_article_s1a2.py \
    --file_dir_path ${config_output_dir} \
    --output_dir ${config_output_dir} \
    --json_idx ${json_id}
done
