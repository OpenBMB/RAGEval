#!/bin/bash
source ./scripts/medical/en/config.sh
run_command() {
    local schema_file=$1
    local reference_file=$2
    local ref_idx=$3
    local json_idx=$4
    python ./code/medical/en/s1_config.py \
        --mode single \
        --data_for_complete ${schema_dir}/${schema_file} \
        --data_for_reference ${schema_dir}/${reference_file} \
        --ref_idx $ref_idx \
        --output_dir ${config_output_dir} \
        --json_idx $json_idx
}

# 定义你的职业和章节名称数组
schema_file="zhuyuan_shoushu.json"
reference_file="disease_type_name_detail.json"

# 循环遍历并发执行
# 1,2,3,4 ... 10
for ref_idx in $(seq 0 18); do
    run_command $schema_file $reference_file $ref_idx $json_idx &
done
# run_command $schema_file $reference_file $json_idx
# 等待所有后台进程完成
wait
