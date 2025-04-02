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
    "科技",
    "餐饮",
    "电子商务",
    "医疗健康",
    "教育",
    "金融服务",
    "咨询",
    "房地产",
    "可再生能源",
    "制造业",
    "交通运输",
    "旅游",
    "媒体与娱乐",
    "时尚",
    "农业",
    "零售",
    "建筑",
    "健身",
    "软件开发",
    "专业服务"
]

year_list = [2022, 2023, 2024]
funding_stages = ["种子轮", "A轮", "B轮", "自筹资金", "天使投资"]


def generate_business_plan(
    model_name="gpt-3.5-turbo",
    industry="科技",
    data_for_complete=None
):
    time.sleep(random.random() * 1.5)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    
    system_prompt = "你是一位专业的商业顾问，专门为企业家制定全面、详细且具有说服力的商业计划书。"
    
    user_prompt = """下面是一个结构化的模板，请你根据这个模板创建一份非常详细和全面的商业计划书。

- 公司所属行业：{industry}
- 这个模板提供了商业计划书的结构。请用真实、具体且详细的内容填充所有字段。
- 创建一个引人注目的公司名称、商业理念和使命宣言。
- 包含详细的市场分析，包括行业趋势和目标市场细分。
- 提供具体的产品/服务，清晰描述其特点和优势。
- 制定全面的营销策略。
- 包含详细的运营计划和财务预测。
- 财务预测应包括真实的收入模式、资金需求和预计损益。
- 包含全面的风险评估和减轻策略。
- 所有内容都要极其详细、具体且真实。
- 你必须以JSON格式回复。

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
            print(f"发生错误: {e}. 重试中...")
            time.sleep(1)
            
    response["行业"] = industry
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default='gpt-3.5-turbo')
    parser.add_argument("--industry", type=str, default="科技")
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
    save_output(args.output_dir, response, industry, args.json_idx, field_name, "json")


if __name__ == "__main__":
    main() 