#!/bin/bash
source ./scripts/medical/en/config.sh
run_command() {
    local crime_names=$1
    local crime_name_idx=$2
    local json_idx=$3
    python ./code/medical/en/s2_article.py \
        --mode single \
        --config_dir ${config_output_dir} \
        --data_for_reference ${schema_dir}/${reference_file} \
        --ref_idx $ref_idx \
        --output_dir ${doc_output_dir} \
        --json_idx $json_idx
}

# 定义你的职业和章节名称数组
reference_file="disease_type_name_detail.json"

# 循环遍历并发执行
# 1,2,3,4 ... 10
for ref_idx in $(seq 0 18); do
    run_command $reference_file $ref_idx $json_idx &
done

# 等待所有后台进程完成
wait
