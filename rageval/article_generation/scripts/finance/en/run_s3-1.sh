#!/bin/bash
source ./scripts/finance/en/config.sh
for json_id in ${json_idx}; do
    python ./code/finance/en/s3-1_generate_outline.py \
    --file_dir_path ${config_output_dir} \
    --output_dir ${config_output_dir} \
    --json_idx ${json_id}
done
