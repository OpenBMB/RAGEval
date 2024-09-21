#!/bin/bash
source ./scripts/finance/zh/config.sh
for json_id in $json_idx; do
    python ./code/finance/zh/s5_concat_article.py \
    --file_dir_path ${config_output_dir} \
    --output_dir ${doc_output_dir} \
    --json_idx ${json_id}
done
