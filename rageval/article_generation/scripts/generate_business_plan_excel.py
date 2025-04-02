#!/usr/bin/env python3
import os
import json
import glob
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

def load_business_plan(file_path: str) -> Optional[Dict]:
    """加载商业计划书JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {e}")
        return None

def extract_articles(base_dir: str, language: str) -> List[Dict]:
    """
    从指定目录中提取所有文章
    
    Args:
        base_dir: 基本目录路径
        language: 语言 ('en' 或 'zh')
    
    Returns:
        包含所有文章内容的列表
    """
    results = []
    
    # 获取所有行业目录
    industries = [d for d in os.listdir(os.path.join(base_dir, "article")) 
                 if os.path.isdir(os.path.join(base_dir, "article", d))]
    
    for industry in industries:
        # 获取dragonball文章
        dragonball_path = os.path.join(base_dir, "article", industry, "0", "business_plan.json")
        dragonball_data = load_business_plan(dragonball_path)
        
        # 获取zero-shot文章
        zero_shot_path = os.path.join(base_dir, "zero_shot", f"{industry}_zero_shot_*.txt")
        zero_shot_files = glob.glob(zero_shot_path)
        zero_shot_content = ""
        if zero_shot_files:
            with open(zero_shot_files[0], 'r', encoding='utf-8') as f:
                zero_shot_content = f.read()
        
        # 获取one-shot文章
        one_shot_path = os.path.join(base_dir, "one_shot", f"{industry}_one_shot_*.txt")
        one_shot_files = glob.glob(one_shot_path)
        one_shot_content = ""
        if one_shot_files:
            with open(one_shot_files[0], 'r', encoding='utf-8') as f:
                one_shot_content = f.read()
        
        # 获取dragonball文章内容
        dragonball_content = ""
        if dragonball_data:
            if language == "en":
                dragonball_content = dragonball_data.get("Generated Article", "")
            else:
                dragonball_content = dragonball_data.get("生成的文章", "")
        
        # 添加到结果列表
        results.append({
            "name": industry,
            "zeroshot": zero_shot_content,
            "oneshot": one_shot_content,
            "dragonball": dragonball_content,
            "zeroshot-安全性": "",
            "oneshot-安全性": "",
            "dragonball-安全性": "",
            "zeroshot-清晰度": "",
            "oneshot-清晰度": "",
            "dragonball-清晰度": "",
            "zeroshot-规范性": "",
            "oneshot-规范性": "",
            "dragonball-规范性": "",
            "zeroshot-丰富度": "",
            "oneshot-丰富度": "",
            "dragonball-丰富度": ""
        })
    
    return results

def save_to_excel(en_results: List[Dict], zh_results: List[Dict], output_file: str):
    """将结果保存到Excel文件，包含英文和中文两个sheet"""
    if not en_results and not zh_results:
        print(f"没有找到文章，不创建Excel文件: {output_file}")
        return
    
    # 设置列的顺序
    columns = [
        "name", "zeroshot", "oneshot", "dragonball",
        "zeroshot-安全性", "oneshot-安全性", "dragonball-安全性",
        "zeroshot-清晰度", "oneshot-清晰度", "dragonball-清晰度",
        "zeroshot-规范性", "oneshot-规范性", "dragonball-规范性",
        "zeroshot-丰富度", "oneshot-丰富度", "dragonball-丰富度"
    ]
    
    # 创建Excel写入器
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 保存英文数据
        if en_results:
            en_df = pd.DataFrame(en_results)
            en_df = en_df[columns]
            en_df.to_excel(writer, sheet_name='en', index=False)
            print(f"已将 {len(en_results)} 条英文记录保存到 {output_file} 的 en sheet")
        
        # 保存中文数据
        if zh_results:
            zh_df = pd.DataFrame(zh_results)
            zh_df = zh_df[columns]
            zh_df.to_excel(writer, sheet_name='zh', index=False)
            print(f"已将 {len(zh_results)} 条中文记录保存到 {output_file} 的 zh sheet")

def main():
    # 设置基础目录
    base_dir = "output/business-plan"
    
    # 处理英文文件
    en_base_dir = os.path.join(base_dir, "en")
    en_results = extract_articles(en_base_dir, "en")
    
    # 处理中文文件
    zh_base_dir = os.path.join(base_dir, "zh")
    zh_results = extract_articles(zh_base_dir, "zh")
    
    # 保存到单个Excel文件
    output_file = os.path.join(base_dir, "business_plans.xlsx")
    save_to_excel(en_results, zh_results, output_file)
    
    print("处理完成!")

if __name__ == "__main__":
    main() 