import sys
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import time
import random
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import argparse


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

def generate_article(model_name, data, idx=0):
    """生成完整的商业计划书文档。"""
    system_prompt = "你是一位专业的商业计划书撰写专家，为企业家和创业公司创建专业、详细且有说服力的商业计划书。"
    
    user_prompt = ""
    user_prompt += data["生成的大纲"]
    user_prompt += f"""

根据上面的大纲和下面的公司摘要，为{data.get('公司名称', '该公司')}撰写一份完整、专业的商业计划书。

请遵循以下指南：
- 充分详细地发展每个部分，内容具体而详尽
- 包含真实的财务预测和市场分析
- 始终保持专业、自信的语调
- 确保各部分之间的逻辑流畅
- 文档要足够全面，可作为完整的商业计划书
- 不要过度使用项目符号；优先使用发展完善的段落
- 包含能使这份商业计划书对潜在投资者有吸引力的真实细节
- 整个文档格式保持一致
- 不要提及这是一份生成的文档

公司摘要：
{data["生成的摘要"]}

请现在撰写完整的商业计划书：
"""
    
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
    """处理单个行业文件以生成完整的商业计划书。"""
    time.sleep(random.random() * 1.5)
    job_input_path = file_dir_path / industry / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_article(model_name, original_data)
                original_data['生成的文章'] = response
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
    
    file_dir_path = Path(args.file_dir_path)
    output_dir = Path(args.output_dir)
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