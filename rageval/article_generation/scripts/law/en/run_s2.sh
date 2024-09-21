#!/bin/bash
source ./scripts/law/en/config.sh
run_command() {
    local crime_names=$1
    local crime_name_idx=$2
    local json_idx=$3
    python ./code/law/en/s2_article.py \
        --mode single \
        --config_dir ${config_output_dir} \
        --crime_names ${schema_dir}/${crime_names} \
        --crime_name_idx $crime_name_idx \
        --output_dir ${doc_output_dir} \
        --json_idx $json_idx
}

# 定义你的职业和章节名称数组
crime_names="charge.json"

# 循环遍历并发执行
# 1,2,3,4 ... 10
for crime_name_idx in $(seq 1 10); do
    run_command $crime_names $crime_name_idx $json_idx &
done

# 等待所有后台进程完成
wait
