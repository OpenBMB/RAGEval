#!/bin/bash
source ./scripts/finance/en/config.sh
run_command() {
    local job=$1
    local chapter_name=$2
    local json_idx=$3
    python ./code/finance/en/s2-1_generate_config.py \
        --mode continue \
        --data_for_complete ${schema_dir}/${chapter_name}.json \
        --data_for_reference ${config_output_dir}/${job// /_}/${json_idx}/financial_report.json \
        --output_dir ${config_output_dir} \
        --json_idx "$json_idx" &
}

# 定义你的职业和章节名称数组
jobs=("IT" "Finance" "Healthcare" "Retail" "Media" "Construction" "Manufacturing" "Energy" "Consumer Goods" "Education" "Agriculture" "Tourism" "Entertainment" "Government" "Environmental Protection" "Research and Development" "Culture" "Social" "Aviation" "Housekeeping")
chapter_names=("corporate_governance" "share_changes_and_shareholder_report")

# 循环遍历并发执行
for job in "${jobs[@]}"; do
    for chapter_name in "${chapter_names[@]}"; do
        run_command "$job" "$chapter_name" "$json_idx"
    done
done

# 等待所有后台进程完成
wait
