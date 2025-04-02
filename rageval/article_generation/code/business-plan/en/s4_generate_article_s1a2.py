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

def generate_article(model_name, data, idx=0):
    """Generate the complete business plan document."""
    system_prompt = "You are an expert business plan writer who creates professional, detailed, and compelling business plans for entrepreneurs and startups."
    
    user_prompt = ""
    user_prompt += data["Generated Outline"]
    user_prompt += f"""

Based on the outline above and the company summary below, write a complete, professional business plan for {data.get('company_name', 'the company')}. 

Follow these guidelines:
- Develop each section thoroughly with detailed, specific content
- Include realistic financial projections and market analysis
- Maintain a professional, confident tone throughout
- Ensure logical flow between sections
- Make the document comprehensive enough to serve as a complete business plan
- Do not use bullet points excessively; prefer well-developed paragraphs
- Include realistic details that would make this business plan compelling to potential investors
- Maintain consistent formatting throughout the document
- Do not mention that this is a generated document

Company Summary:
{data["Generated Summary"]}

Please write the complete business plan now:
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
    """Process a single industry file to generate a complete business plan."""
    time.sleep(random.random() * 1.5)
    industry_safe = industry.replace(' ', '_')
    job_input_path = file_dir_path / industry_safe / str(json_idx)

    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name

            try:
                original_data = load_json_data(file_path)
                response = generate_article(model_name, original_data)
                original_data['Generated Article'] = response
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
    
    file_dir_path = Path(args.file_dir_path)
    output_dir = Path(args.output_dir)
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