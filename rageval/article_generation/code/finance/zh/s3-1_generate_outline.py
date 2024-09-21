import os
import json
import time
import sys
import random
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor
import argparse

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')
job_list = [
    "IT",
    "金融",
    "医疗",
    "零售",
    "媒体",
    "建筑",
    "制造",
    "能源",
    "消费品",
    "教育",
    "农业",
    "旅游",
    "娱乐",
    "政府",
    "环保",
    "研发",
    "文化",
    "社交",
    "航空",
    "家政",
]


def generate_article(model_name, data, idx=0):
    system_prompt = "你是一名专业的报告撰写专家。"
    user_prompt = f"""以下JSON是一家公司的信息，请你根据这些信息撰写一份{data['报告类型']}大纲，需要注意的要点要求如下：
"""
    user_prompt += "- 请你体现各种事件和指标影响。\n"
    user_prompt += "- 每一段应该写得完整，**不要过于精简**。\n"
    user_prompt += "- 你一定要仔细列出JSON中涉及到的**所有的时间点**。\n"
    user_prompt += "- 描述事件时，可以采用[事件名](时间点)的方式。\n"
    user_prompt += "- 描述指标时，可以采用[指标名](数值)的方式。\n"
    user_prompt += "- 你必须完全列出所有数据，包括**重要事件及其子事件**。\n"
    
    user_prompt += (
        "- 你只需要返回撰写的报告大纲，而**不要出现你自己对此请求的回复**。\n"
    )
    user_prompt += "- 再次强调，你一定要仔细列出JSON中涉及到的**所有的时间点**！！！\n"

    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    if idx != 0:
        company_info = data.pop("公司信息", None)
    user_prompt += json.dumps(data, ensure_ascii=False, indent=1)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    ).choices[0].message.content
    if idx != 0:
        data['公司信息'] = company_info
    return response


def process_job(job, model_name, file_dir_path, json_idx, output_dir):
    time.sleep(random.random() * 1.5)
    job_input_path = file_dir_path / job / str(json_idx)

    for idx, file in enumerate(job_input_path.iterdir()):
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_article(model_name, original_data, idx)
                original_data['生成大纲'] = response
                save_output(output_dir, original_data, job, json_idx, file.name.replace(".json", ""), "json")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")


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

    # 使用ProcessPoolExecutor并行处理
    with ProcessPoolExecutor(max_workers=20) as executor:
        # 使用executor.map来并发执行
        list(
            tqdm(
                executor.map(
                    process_job,
                    job_list,
                    [model_name] * len(job_list),
                    [file_dir_path] * len(job_list),
                    [json_idx] * len(job_list),
                    [output_dir] * len(job_list),
                ),
                total=len(job_list),
            )
        )


if __name__ == "__main__":
    main()
