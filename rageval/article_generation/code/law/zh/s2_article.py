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
    system_prompt = '你是一名经验丰富的法院书记员，你有丰富的法律文书撰写经验，并且有极强的想象力。'
    user_prompt = f"""你需要写一份详实的法律文书范文。
你需要根据一个法律文书的实例（JSON形式的案件关键信息），撰写一份**刑事判决书**：
- 根据这个完善的信息，撰写一份法律文书，要非常详细，自己补充案件经过和细节，按照一位资深法院文书撰写者的口吻写，起码8000字以上。
- 你应该根据信息补充案件的经过和细节，比如被告人的供述。你可以自由发挥，但是要符合法律规定。
- 在撰写文书时，你应该包括如下几个模块：法院及检察院信息、被告及辩护人信息、案件涉及程序、案情陈述、指控罪名、证据描述、量刑考量、判决结果、上诉权说明等（不需要包括法律依据）。
- 撰写文书时，口吻应该以“本院”等作为主语，要注意口吻的正式、正规性。
- 不要把证据描述和案情陈述写得太过简单，要详细描述案件的经过，并且在此处不应该分点（1. 2. 3.等）。
- 你不需要写出参考的法律条文内容，只需要写出参考法条条号即可。
犯人涉及的罪名是：{crime_name}。
"""
    cankao_fatiao = f"""参考法条条号为：
{crime_detail[crime_detail.find('第'):crime_detail.rfind('条')+1]}
"""
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
    response += f"""参考法条如下：
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
    crime_name, crime_detail = crime_dict['名称'], crime_dict['详情']
    data = load_json_data(pathlib.Path(args.config_dir) / crime_name / str(json_idx) / f'{str(json_idx)}.json')
    
    response = generate_article(model_name, data, crime_name, crime_detail)
    save_output(args.output_dir, response, crime_name, json_idx, None, "txt")


if __name__ == "__main__":
    main()
