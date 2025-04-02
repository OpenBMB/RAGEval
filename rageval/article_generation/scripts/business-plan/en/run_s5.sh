#!/bin/bash
source ./scripts/business-plan/en/config.sh

python ./code/business-plan/en/s5_concat_article.py \
    --file_dir_path ${article_output_dir} \
    --output_dir ${doc_output_dir} \
    --json_idx ${json_idx} 