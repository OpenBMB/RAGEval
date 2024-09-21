import os
import sys
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
    system_prompt = 'You are an experienced attending physician, you have extensive experience in writing hospitalization record, and you have a strong imagination.'
    user_prompt = f"""You are writing a medical record for a patient.
You need to write a full hospital record based on a JSON example file (key information in JSON format).
- The disease to be written this time is: {disease_name}-{disease_detail}.
- Provide a detailed description of the condition, covering all relevant symptoms and signs.
- Each part of the case should be logically coherent, from the patient's chief complaint, present illness history, past history, marital and family history, to physical examination, auxiliary examination, diagnosis, treatment, etc., with clear causal relationships in each part.
- Include necessary fields such as patient information, medical history, examination results, diagnosis, treatment plan, and follow-up.
- Your reply should not use markdown, **only include the full text of the medical record without your evaluation of it**.
- DO NOT USE JSON FORMAT AS RESPONSE.
The JSON example of the hospital record is as follows:
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
    parser.add_argument("--model_name", type=str, default='gpt-4o')
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
        disease_name = disease_item['Name']
        data = load_json_data(pathlib.Path(args.config_dir) / disease_type / str(json_idx) / f"{disease_name}.json")
        response = generate_article(model_name, disease_type, disease_detail, data)
        save_output(args.output_dir, response, disease_type, args.json_idx, disease_name, "txt")


if __name__ == "__main__":
    main()
