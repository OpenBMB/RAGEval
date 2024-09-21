import os
import json
from openai import OpenAI
import time
import random
import sys
import argparse
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')
job_list = [
    "IT",
    "Finance",
    "Healthcare",
    "Retail",
    "Media",
    "Construction",
    "Manufacturing",
    "Energy",
    "Consumer Goods",
    "Education",
    "Agriculture",
    "Tourism",
    "Entertainment",
    "Government",
    "Environmental Protection",
    "Research and Development",
    "Culture",
    "Social",
    "Aviation",
    "Housekeeping"
]

def generate_article(model_name, data, idx=0):
    system_prompt = "You are an expert in report writing, who will carefully read the client's requirements for you and execute them to the letter."
    user_prompt = ""
    user_prompt += json.dumps(data["Company Information"], ensure_ascii=False, indent=1)
    user_prompt += (
        "\n\nPlease introduce the company's basic information in one sentence based on the JSON provided above.\n"
    )
    user_prompt += "Please begin writing:\n"
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
    job_input_path = file_dir_path / job.replace(' ', '_') / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_article(model_name, original_data)
                original_data['Generated Summary'] = response
                save_output(output_dir, original_data, job.replace(' ', '_'), json_idx, file.name.replace('.json', ''), "json")
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
