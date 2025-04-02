#!/usr/bin/env python3
import os
import json
import csv
import glob
import pandas as pd

def extract_articles(base_dir, article_key=None):
    """
    从指定目录中提取所有business_plan.json文件中的文章内容字段
    
    Args:
        base_dir: 基本目录路径，如 'output/business-plan/en'
        article_key: 文章内容的键名，默认会根据目录自动选择
    
    Returns:
        包含所有文章内容的列表
    """
    print(f"处理目录: {base_dir}")
    
    # 根据目录自动选择键名
    if article_key is None:
        if "/en/" in base_dir:
            article_key = "Generated Article"
        elif "/zh/" in base_dir:
            article_key = "生成的文章"
        else:
            article_key = "Generated Article"  # 默认使用英文键名
            
    print(f"使用键名: {article_key}")
    
    # 查找所有符合模式的json文件
    pattern = os.path.join(base_dir, "article", "*", "0", "business_plan.json")
    files = glob.glob(pattern)
    
    # 记录结果，包含行业和文章内容
    results = []
    
    for file_path in files:
        # 从路径中提取行业信息
        parts = file_path.split(os.sep)
        industry = parts[-3]  # article/{industry}/0/business_plan.json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if article_key in data:
                    article = data[article_key]
                    results.append({
                        "industry": industry,
                        "generated_article": article,
                        "safety": "",
                        "clarity": "",
                        "normative": "",
                        "richness": ""
                    })
                else:
                    print(f"警告: 在 {file_path} 中没有找到 '{article_key}' 字段")
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            
    return results

def save_to_csv(results, output_file):
    """
    将结果保存到CSV文件
    
    Args:
        results: 包含文章内容的列表
        output_file: 输出CSV文件的路径
    """
    if not results:
        print(f"没有找到文章，不创建CSV文件: {output_file}")
        return
    
    # 使用pandas创建DataFrame并保存为CSV
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"已将 {len(results)} 条记录保存到 {output_file}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    # 处理英文文件
    en_base_dir = os.path.join(root_dir, "output", "business-plan", "en")
    en_results = extract_articles(en_base_dir, article_key="Generated Article")
    en_output = os.path.join(root_dir, "output", "business-plan", "en_articles.csv")
    save_to_csv(en_results, en_output)
    
    # 处理中文文件
    zh_base_dir = os.path.join(root_dir, "output", "business-plan", "zh")
    zh_results = extract_articles(zh_base_dir, article_key="生成的文章")
    zh_output = os.path.join(root_dir, "output", "business-plan", "zh_articles.csv")
    save_to_csv(zh_results, zh_output)
    
    print("处理完成!")

if __name__ == "__main__":
    main() 