import sys
import os
import json
from openai import OpenAI
import random
import argparse
import time
import pathlib
from dotenv import load_dotenv
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor


load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')
industry_list = [
    "科技",
    "餐饮",
    "电子商务",
    "医疗健康",
    "教育",
    "金融服务",
    "咨询",
    "房地产",
    "可再生能源",
    "制造业",
    "交通运输",
    "旅游",
    "媒体与娱乐",
    "时尚",
    "农业",
    "零售",
    "建筑",
    "健身",
    "软件开发",
    "专业服务"
]


def generate_company_summary(model_name, data):
    """生成商业计划书的详细公司摘要。"""
    system_prompt = "你是一位专业的商业文案撰写专家，专门为商业计划书创建全面的公司摘要。"
    
    user_prompt = f"""
根据提供的商业计划数据，为{data.get('公司名称', '该公司')}创建一份详细的公司摘要部分。

摘要应提供以下方面的全面概述：
1. 公司的使命、愿景和价值观
2. 核心产品/服务和独特的价值主张
3. 目标市场和竞争优势
4. 当前业务阶段和关键成就
5. 领导团队背景（如有）

请确保摘要专业、引人入胜，适合作为正式商业计划书文档的一部分。

以下是商业计划数据：
"""
    user_prompt += json.dumps(data, ensure_ascii=False, indent=2)
    
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
        
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    ).choices[0].message.content
    
    return response


def process_industry(industry, model_name, file_dir_path, json_idx, output_dir):
    """处理单个行业文件以生成公司摘要。"""
    time.sleep(random.random() * 1.5)
    job_input_path = file_dir_path / industry / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_company_summary(model_name, original_data)
                original_data['生成的摘要'] = response
                save_output(output_dir, original_data, industry, str(json_idx), file.name.replace('.json', ''), "json")
            except Exception as e:
                print(f"处理 {file_path} 时出错: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='gpt-3.5-turbo')
    parser.add_argument('--file_dir_path', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--json_idx', type=int, default=0)
    args = parser.parse_args()
    
    file_dir_path = pathlib.Path(args.file_dir_path)
    output_dir = args.output_dir
    model_name = args.model_name
    json_idx = args.json_idx

    # 使用 ProcessPoolExecutor 进行并行处理
    with ProcessPoolExecutor(max_workers=20) as executor:
        list(
            tqdm(
                executor.map(
                    process_industry,
                    industry_list,
                    [model_name] * len(industry_list),
                    [file_dir_path] * len(industry_list),
                    [json_idx] * len(industry_list),
                    [output_dir] * len(industry_list),
                ),
                total=len(industry_list),
            )
        )


if __name__ == "__main__":
    main() 