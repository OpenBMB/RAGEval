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
    system_prompt = "你是一名报告撰写专家，会认真阅读客户对你的要求，并一字不差地执行。"
    user_prompt = ""
    user_prompt += data["生成大纲"]
    user_prompt += f"""

根据上面的大纲，用一段话详细撰写一篇{data['公司信息']['名称']}完整的报告文章。请确保每个部分都充分展开，包含深入的分析、具体的数据支持，以及相关的行业比较。使内容详尽而深入：
"""
    user_prompt += "- 在文章的开头，我会提供一段基于大纲撰写的公司基本信息。\n"
    user_prompt += "- 请你根据文章大纲，逐点撰写详细的内容，详细讨论报告指标的具体细节及其原因，影响。\n"
    user_prompt += "- 请尽可能使用具体数据和比较分析来支持每个部分的讨论，使报告内容丰富、有说服力。\n"
    user_prompt += "- 请确保文章的逻辑性和连贯性，使文章内容通顺、清晰。\n"
    user_prompt += "- 在事件和事件之间的过渡，不可以过于生硬地使用转折语句如“首先”、“其次”等，而是要使段落之间的逻辑关系更加自然。\n"
    user_prompt += "- 确保撰写时语言语气的多样性。\n"
    user_prompt += "- 输出不要使用markdown格式。\n\n"
    user_prompt += '- 在对重要事件进行撰写时，**你必须将事件、子事件和涉及的指标直接糅合起来放在一段话中，请注意，这段话不要有任何的分点、分段，同时不要体现"子事件"这个名词，而是隐式写在文字中**。\n'
    user_prompt += "- 一定要按照发生的时间先后顺序对所有事件的描述进行组织。\n"
    user_prompt += "- 比如，应该将事件作为某某方面来叙述，详细介绍事件及其子事件的发生过程，同时表明事件所影响的指标，并对指标数字蕴含的信息和变化原因进行分析。\n"
    user_prompt += '- 撰写文章时，你要体现各类事件及其相关的各种指标数字，总结和正文之间不需要有任何分隔符或表示分隔的语句。\n'
    user_prompt += '- 再次强调：这段话不要有任何的分点、分段！！！\n'
    user_prompt += '- 我在开头已经有一句话介绍公司大致情况，你不需要重新介绍。\n'
    user_prompt += '请开始撰写：\n'
    user_prompt += data["生成总结"]

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


def process_job(job, model_name, file_dir_path, json_idx, output_dir):
    time.sleep(random.random() * 1.5)
    job_input_path = file_dir_path / job / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_article(model_name, original_data)
                original_data['生成文章'] = response
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
