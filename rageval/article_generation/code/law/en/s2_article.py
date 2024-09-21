import os
import json
import sys
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
    data_for_complete,
    crime_name,
    crime_detail,
):
    time.sleep(random.random() * 1.5)
    system_prompt = 'You are an experienced court clerk, you have rich experience in writing legal documents, and have a strong imagination.'
    user_prompt = f"""You need to write a detailed legal document sample.
You need to write a criminal judgment based on a JSON example (case key information in JSON form):
- Based on this completed information, write a legal document that is very detailed, supplementing the case history and details yourself, and writing in the tone of an experienced court clerk. It should be at least 8000 words.
- You should supplement the case history and details based on the information, such as the defendant's confession. You can freely elaborate, but it must comply with legal regulations.
- When writing the document, you should include the following sections: Court and Prosecutor Information, Defendant and Defense Lawyer Information, Case Procedures, Case Statement, Charge, Evidence Description, Sentencing Considerations, Judgment Result, Appeal Rights Explanation, etc. (do not include legal basis).
- When writing the document, the tone should use "This court" as the subject. Pay attention to the formal and official tone.
- Do not make the evidence description and case statement too brief. Describe the case process in detail, and do not use points (1. 2. 3. etc.) in this section.
- You do not need to write out the referenced legal provisions' content, only the article numbers.
The crime involved is: {crime_name}.
"""
    fatiao = crime_detail[crime_detail.find(' '):crime_detail.find('\n')]
    cankao_fatiao = f"Reference Article number is: No. {fatiao}\n"
    user_prompt += cankao_fatiao
    user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    ).choices[0].message.content
    response += '\n\n'
    response += f"""Reference Article is below：
{crime_detail}"""
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="single")
    parser.add_argument("--model_name", type=str, default='gpt-4o')
    parser.add_argument("--config_dir", type=str, default=None)
    parser.add_argument("--crime_names", type=str, default=None)
    parser.add_argument("--crime_name_idx", type=int, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()

    json_idx = args.json_idx
    model_name = args.model_name

    crime_dict_list = load_json_data(args.crime_names)
    crime_dict = crime_dict_list[args.crime_name_idx]
    crime_name, crime_detail = crime_dict['name'], crime_dict['details']
    data = load_json_data(pathlib.Path(args.config_dir) / crime_name / str(json_idx) / f'{str(json_idx)}.json')
    
    response = generate_article(model_name, data, crime_name, crime_detail)
    save_output(args.output_dir, response, crime_name, json_idx, None, "txt")


if __name__ == "__main__":
    main()
