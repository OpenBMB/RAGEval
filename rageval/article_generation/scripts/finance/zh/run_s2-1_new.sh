#!/bin/bash
source ./scripts/finance/zh/config.sh
run_command() {
    local job=$1
    local chapter_name=$2
    local json_idx=$3
    python ./code/finance/zh/s2-1_generate_config.py \
        --mode new \
        --data_for_complete ${schema_dir}/${chapter_name}.json \
        --job_name $job \
        --output_dir ${config_output_dir} \
        --json_idx $json_idx &
}

# 定义你的职业和章节名称数组
jobs=("IT" "金融" "医疗" "零售" "媒体" "建筑" "制造" "能源" "消费品" "教育" "农业" "旅游" "娱乐" "政府" "环保" "研发" "文化" "社交" "航空" "家政")
chapter_names=("财务报告")

# 循环遍历并发执行
for job in "${jobs[@]}"; do
    for chapter_name in "${chapter_names[@]}"; do
        run_command "$job" "$chapter_name" "$json_idx"
    done
done

# 等待所有后台进程完成
wait