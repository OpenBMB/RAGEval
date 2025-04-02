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


def generate_outline(model_name, data):
    """生成商业计划书的详细大纲。"""
    system_prompt = "你是一位专业的商业顾问，专门为企业家创建全面的商业计划书大纲。"
    user_prompt = f"""
根据提供的商业计划数据，为{data.get('公司名称', '该公司')}创建一份详细的商业计划书大纲。

大纲应包括标准商业计划书的所有主要部分：
1. 执行摘要
2. 业务描述
3. 市场分析
4. 产品和服务
5. 营销和销售策略
6. 运营计划
7. 财务计划
8. 风险分析
9. 结论

对于每个部分，包括主要子部分和应该涵盖的要点。大纲应该足够详细，可以作为编写完整商业计划书的综合指南。

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
    """处理单个行业文件以生成大纲。"""
    time.sleep(random.random() * 1.5)
    job_input_path = file_dir_path / industry / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_outline(model_name, original_data)
                original_data['生成的大纲'] = response
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