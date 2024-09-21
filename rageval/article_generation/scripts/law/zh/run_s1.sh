#!/bin/bash
source ./scripts/law/zh/config.sh
run_command() {
    local schema_file=$1
    local crime_names=$2
    local crime_name_idx=$3
    local json_idx=$4
    python ./code/law/zh/s1_config.py \
        --mode single \
        --data_for_complete ${schema_dir}/${schema_file} \
        --crime_names ${schema_dir}/${crime_names} \
        --crime_name_idx $crime_name_idx \
        --output_dir ${config_output_dir} \
        --json_idx $json_idx
}

# 定义你的职业和章节名称数组
schema_file="刑事.json"
crime_names="罪名.json"

# 循环遍历并发执行
# 1,2,3,4 ... 10
for crime_name_idx in $(seq 1 10); do
    run_command $schema_file $crime_names $crime_name_idx $json_idx &
done

# 等待所有后台进程完成
wait
