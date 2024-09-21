import sys
import os
import json
from openai import OpenAI
import random
import argparse
import time
import pathlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')

def generate_article(
    model_name, 
    disease_name,
    disease_detail,
    data
):
    time.sleep(random.random() * 1.5)
    system_prompt = '你是一名经验丰富的主治医生，你有丰富的住院病历撰写经验，并且有极强的想象力。'
    user_prompt = f"""你正在为一位病人撰写病历。
你需要根据一个住院病历的JSON实例文件（JSON形式的病历关键信息），撰写一份住院病历的全文：
- 本次需要撰写的病种是：{disease_name}-{disease_detail}。
- 提供详细的病情描述，涵盖所有相关症状和体征。
- 病例的各部分应该逻辑连贯，从病人的主诉、现病史、既往史、婚育史及家族史到体格检查、辅助检查、诊断、诊疗等，每一部分都应有明确的因果关系。
- 包含必要的字段，例如患者信息、病史、检查结果、诊断、治疗方案和随访情况等。
- 你的回复不要使用markdown，**仅需包含病历全文，不需要包含你对它的评价**。
住院病历的JSON实例如下：
"""

    user_prompt += json.dumps(data, ensure_ascii=False, indent=1)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    while True:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        ).choices[0].message.content
        break
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="new")
    parser.add_argument("--model_name", type=str, default="gpt-4o")
    parser.add_argument("--config_dir", type=str, default=None)
    parser.add_argument("--data_for_reference", type=str, default=None)
    parser.add_argument("--ref_idx", type=int, default=0)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()

    json_idx = args.json_idx
    model_name = args.model_name

    disease_type, disease_detail = list(load_json_data(args.data_for_reference).items())[args.ref_idx]
    for disease_item in disease_detail:
        disease_name = disease_item['名称']
        data = load_json_data(pathlib.Path(args.config_dir) / disease_type / str(json_idx) / f"{disease_name}.json")
        response = generate_article(model_name, disease_type, disease_detail, data)
        save_output(args.output_dir, response, disease_type, args.json_idx, disease_name, "txt")


if __name__ == "__main__":
    main()
