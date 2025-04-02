#!/bin/bash
source ./scripts/business-plan/zh/config.sh

run_command() {
    local industry=$1
    local chapter_name=$2
    local json_idx=$3
    python ./code/business-plan/zh/s2-1_generate_config.py \
        --industry "${industry}" \
        --data_for_complete ${schema_dir}/${chapter_name}.json \
        --output_dir ${config_output_dir} \
        --json_idx $json_idx &
}

# 定义行业和章节名称
industries=("科技" "餐饮" "电子商务" "医疗健康" "教育" "金融服务" "咨询" "房地产" "可再生能源" "制造业" "交通运输" "旅游" "媒体与娱乐" "时尚" "农业" "零售" "建筑" "健身" "软件开发" "专业服务")
chapter_names=("business_plan")

# 循环并行执行
for industry in "${industries[@]}"; do
    for chapter_name in "${chapter_names[@]}"; do
        run_command "$industry" "$chapter_name" "$json_idx"
    done
done

# 等待所有后台进程完成
wait 