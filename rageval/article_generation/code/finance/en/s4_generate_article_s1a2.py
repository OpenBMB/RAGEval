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
    user_prompt += data["Generated Outline"]
    user_prompt += f"""

Based on the outline above, write a detailed paragraph about {data['Company Information']['Name']} to compose a complete report article. Ensure that each section is thoroughly expanded, containing in-depth analysis, specific data support, and relevant industry comparisons to make the content detailed and profound.
"""
    user_prompt += "- In the beginning of the article, I will provide a section based on the outline about the basic information of the company.\n"
    user_prompt += "- You are to write detailed content according to the article outline, discussing the specific details of the report indicators and their reasons, impacts in detail.\n"
    user_prompt += "- Use specific data and comparative analysis as much as possible to support the discussion of each part, enriching and making the report persuasive.\n"
    user_prompt += "- Ensure the article's logic and coherence for smooth, clear content.\n"
    
    user_prompt += '- The transition between events should not be abruptly made using transitional phrases like "firstly", "secondly", but rather, ensure a more natural logical relation between paragraphs.\n'
    user_prompt += "- Ensure a variety of tones in your writing style.\n"
    user_prompt += "- Do not use markdown format for the output.\n"
    user_prompt += '- When writing about important events, **you must directly integrate the event, sub-events, and involved indicators into one paragraph, please note that this paragraph should not have any bullet points, breaks, and should not explicitly mention "sub-event" but rather implicitly incorporate it in the text**.\n'
    user_prompt += "- Organize the description of all events in chronological order of occurrence.\n"
    user_prompt += "- For example, narrate an event as an aspect, describing the occurrence of the event and its sub-events, while indicating the affected indicators and analyzing the reasons behind the numbers and changes.\n"
    
    user_prompt += '- When writing the article, you should reflect all types of events and their related numerical indicators, there should be no separators or statements indicating separation between the summary and the main text.\n'
    user_prompt += '- Again, emphasize: this paragraph should not have any bullet points, breaks!!!\n'
    user_prompt += '- I have already introduced the general situation of the company at the beginning, you do not need to reintroduce it.\n'
    user_prompt += 'Please start writing:\n'
    user_prompt += data["Generated Summary"]
    
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
                original_data['Generated Article'] = response
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
