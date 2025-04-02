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
    "Technology",
    "Food & Beverage",
    "E-commerce",
    "Healthcare",
    "Education",
    "Financial Services",
    "Consulting",
    "Real Estate",
    "Renewable Energy",
    "Manufacturing",
    "Transportation",
    "Tourism",
    "Media & Entertainment",
    "Fashion",
    "Agriculture",
    "Retail",
    "Construction",
    "Fitness",
    "Software Development",
    "Professional Services"
]


def generate_company_summary(model_name, data):
    """Generate a detailed company summary for a business plan."""
    system_prompt = "You are an expert business writer specializing in creating comprehensive company summaries for business plans."
    
    user_prompt = f"""
Based on the business plan data provided, create a detailed company summary section for {data.get('company_name', 'the company')}. 

The summary should provide a comprehensive overview of:
1. The company's mission, vision, and values
2. Core products/services and unique value proposition
3. Target market and competitive advantage
4. Current stage of business and key achievements
5. Leadership team background (if available)

Make the summary professionally written, engaging, and suitable for inclusion in a formal business plan document.

Here is the business plan data:
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
    """Process a single industry file to generate a company summary."""
    time.sleep(random.random() * 1.5)
    industry_safe = industry.replace(' ', '_')
    job_input_path = file_dir_path / industry_safe / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_company_summary(model_name, original_data)
                original_data['Generated Summary'] = response
                save_output(output_dir, original_data, industry_safe, str(json_idx), file.name.replace('.json', ''), "json")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")


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

    # Use ProcessPoolExecutor for parallel processing
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