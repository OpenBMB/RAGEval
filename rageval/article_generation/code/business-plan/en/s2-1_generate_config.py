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

year_list = [2022, 2023, 2024]
funding_stages = ["Seed", "Series A", "Series B", "Bootstrapped", "Angel Investment"]


def generate_business_plan(
    model_name="gpt-3.5-turbo",
    industry="Technology",
    data_for_complete=None
):
    time.sleep(random.random() * 1.5)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    
    system_prompt = "You are an expert business consultant who specializes in developing comprehensive business plans. Your expertise helps entrepreneurs create detailed, realistic, and compelling business plans."
    
    user_prompt = """Below is a structured schema that you need to use as a guide to create a very detailed and comprehensive business plan for a company.

- Industry of the company: {industry}
- The schema provides the structure for the business plan. Please fill in all fields with realistic, specific, and detailed content.
- Create a compelling company name, business concept, and mission statement.
- Include detailed market analysis with industry trends and target market segments.
- Provide specific products/services with clear features and benefits.
- Develop a comprehensive marketing strategy.
- Include detailed operational plans and financial projections.
- The financial projections should include realistic revenue models, funding requirements, and projected P&L.
- Include thorough risk assessment and mitigation strategies.
- Make all content extremely detailed, specific, and realistic.
- You must reply in JSON format.

""".format(industry=industry)
    
    user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)

    while True:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            ).choices[0].message.content
            response = response[response.find("{") : response.rfind("}") + 1]
            response = json.loads(response)
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")
            time.sleep(1)
            
    response["industry"] = industry
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default='gpt-3.5-turbo')
    parser.add_argument("--industry", type=str, default="Technology")
    parser.add_argument("--data_for_complete", type=str, required=True)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()
    
    model_name = args.model_name
    data_for_complete = load_json_data(args.data_for_complete)
    field_name = args.data_for_complete.split("/")[-1].split(".")[0]

    industry = args.industry
    response = generate_business_plan(
        model_name, industry, data_for_complete
    )
    save_output(args.output_dir, response, industry.replace(' ', '_'), args.json_idx, field_name, "json")


if __name__ == "__main__":
    main() 