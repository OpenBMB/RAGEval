from concurrent.futures import ProcessPoolExecutor
import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv
import random
import argparse
import time
import pathlib
from pathlib import Path
from tqdm import tqdm

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


def generate_article(model_name, original_data, event_num=1):
    sub_data = {
        "报告类型": original_data["报告类型"],
        "报告时间": original_data["报告时间"],
        "公司信息": original_data["公司信息"],
    }
    system_prompt = "你是一名编造财务信息的专家，编造的财务信息天衣无缝，让人信服。"
    instruct_prompt = (
        f"""请根据以下提供的有关{sub_data['公司信息']['名称']}的重要事件信息，"""
        + """合理补充出与该重要事件直接相关的具体前置子事件。需要您详细列出每个前置子事件，这些子事件应该是**和报告同年发生的**，导致重要事件发生的直接步骤或决策，并应按照发生的时间顺序进行排序。请确保每个子事件都包括完整的信息，格式与重要事件的结构相同。
您补充的子事件应包含以下字段，并按此格式组织：
事件：子事件的名称或简短描述。
时间：子事件发生的具体日期或时间段。
描述：对子事件进行详细的描述，包括它是如何准备或导致重要事件发生的。
影响：子事件对公司或相关实体产生的具体影响。
请按照以下格式返回一个子事件列表，确保每个字段都被准确填写，且不要包含任何多余的文字性回复：
[
    {
        "事件": "子事件名称",
        "时间": "子事件发生的时间",
        "描述": "子事件的详细描述",
        "影响": "子事件产生的影响"
    },
    ...
]
请仅补充与所给重要事件最直接相关的子事件，并避免添加过于宽泛或不相关的子事件（例如“公司成立”等）。
"""
    )
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    important_event = original_data["报告内容"][0]["重要事件"]
    if event_num == 1:
        selected_idx = [0]
    else:
        selected_idx = random.sample(range(len(important_event)), event_num)
    for idx in selected_idx:
        sub_data["重要事件"] = important_event[idx]
        json_str = json.dumps(sub_data, ensure_ascii=False, indent=2)
        user_prompt = instruct_prompt + json_str
        while True:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                ).choices[0].message.content
                response = response[response.find("[") : response.rfind("]") + 1]
                response = json.loads(response)
                break
            except Exception as e:
                print(f"Error occurred: {e}. Retrying...")
                time.sleep(1)
        original_data["报告内容"][0]["重要事件"][idx]["子事件"] = response

    return original_data


def process_job(job, model_name, file_dir_path, json_idx, output_dir, event_num=1):
    time.sleep(random.random() * 1.5)
    job_input_path = file_dir_path / job / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                if (
                    "子事件" not in original_data["报告内容"][0]["重要事件"][0]
                    or original_data["报告内容"][0]["重要事件"][0]["子事件"] == ""
                ):
                    data = generate_article(model_name, original_data, event_num)
                    save_output(output_dir, data, job, json_idx, file.name.replace(".json", ""), "json")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")


# # 读取JSON文件
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='gpt-3.5-turbo')
    parser.add_argument('--file_dir_path', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    parser.add_argument("--event_num", type=int, default=1)
    args = parser.parse_args()
    file_dir_path = Path(args.file_dir_path)
    output_dir = Path(args.output_dir)
    model_name = args.model_name
    json_idx = args.json_idx
    event_num = args.event_num

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
                    [event_num] * len(job_list),
                ),
                total=len(job_list),
            )
        )


if __name__ == "__main__":
    main()
