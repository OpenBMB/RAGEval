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
    system_prompt = "You are a professional report writing expert."
    user_prompt = f"""Below is a JSON containing a company's information. Based on this data, please create an outline for a {data['Report Type']} report. The key points to note are as follows:
    """
    user_prompt += "- Please reflect the impacts of various events and indicators.\n"
    user_prompt += "- Each paragraph should be complete, **do not be overly concise**.\n"
    user_prompt += "- You must meticulously list **all the time points** mentioned in the JSON.\n"
    user_prompt += "- When describing events, you may use the format [event name](time point).\n"
    user_prompt += "- When describing indicators, you may use the format [indicator name](value).\n"
    user_prompt += "- You must fully list all the data, including **important events and their sub-events**.\n"

    user_prompt += (
        "- You only need to return the written report outline, and **do not include your own response to this request**.\n"
    )
    user_prompt += "- Again, it is imperative that you meticulously list **all the time points** mentioned in the JSON!!!\n"

    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    if idx != 0:
        company_info = data.pop("Company Information", None)
    user_prompt += json.dumps(data, ensure_ascii=False, indent=1)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    ).choices[0].message.content
    if idx != 0:
        data['Company Information'] = company_info
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
                original_data['Generated Outline'] = response
                save_output(output_dir, original_data, job.replace(' ', '_'), str(json_idx), file.name.replace('.json', ''), "json")
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
