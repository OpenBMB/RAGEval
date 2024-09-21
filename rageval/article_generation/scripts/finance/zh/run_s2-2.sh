#!/bin/bash
source ./scripts/finance/zh/config.sh
for json_id in $json_idx; do
    python ./code/finance/zh/s2-2_generate_config_subevent.py \
    --file_dir_path ${config_output_dir} \
    --output_dir ${config_output_dir} \
    --json_idx ${json_id} \
    --event_num ${event_num}
done
