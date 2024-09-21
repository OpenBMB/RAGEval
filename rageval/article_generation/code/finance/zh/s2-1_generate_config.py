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
# job_list = [
#     "IT",
#     "金融",
#     "医疗",
#     "零售",
#     "媒体",
#     "建筑",
#     "制造",
#     "能源",
#     "消费品",
#     "教育",
#     "农业",
#     "旅游",
#     "娱乐",
#     "政府",
#     "环保",
#     "研发",
#     "文化",
#     "社交",
#     "航空",
#     "家政",
# ]

year_list = [2017, 2018, 2019, 2020, 2021]
season_list = ["一季度", "二季度", "三季度", "四季度"]
season_month_dict = {
    "一季度": [1, 2, 3],
    "二季度": [4, 5, 6],
    "三季度": [7, 8, 9],
    "四季度": [10, 11, 12],
}
month_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def sample_month(month_list, event_len):
    if event_len <= len(month_list):
        return random.sample(month_list, event_len)
    else:
        return random.choices(month_list, k=event_len)

def sort_event_by_time(report_contents):
    for item in report_contents:
        for event in item["重要事件"]:
            event["时间对象"] = datetime.strptime(event["时间"], "%Y年%m月")
        item["重要事件"].sort(key=lambda x: x["时间对象"])
        for event in item["重要事件"]:
            del event["时间对象"]


def assign_event_times(year, months, report_contents):
    # 为每个重要事件指定时间
    for item in report_contents:
        event_len = len(item["重要事件"])
        selected_months = sample_month(months, event_len)
        for event in item["重要事件"]:
            event["时间"] = f"{year}年{selected_months.pop()}月"


def set_time(mode, data_for_complete, data_for_reference=None):
    if mode == "new":
        # 随机年度/季度报告时间
        year = random.choice(year_list)
        season = random.choice(season_list)
        # only 年度
        if random.random() > 0:
            data_for_complete["报告时间"] = f"{year}年度"
            assign_event_times(year, month_list, data_for_complete["报告内容"])
            sort_event_by_time(data_for_complete["报告内容"])
        else:
            data_for_complete["报告时间"] = f"{year}年{season}"
            assign_event_times(year, season_month_dict[season], data_for_complete["报告内容"])
    else:
        year = data_for_reference["报告时间"].split("年")[0]
        season = data_for_reference["报告时间"].split("年")[-1]
        if "季度" not in season:
            assign_event_times(year, month_list, data_for_complete["报告内容"])
        else:
            assign_event_times(
                year, season_month_dict[season], data_for_complete["报告内容"]
            )

    return data_for_complete


def no_value_check(response):
    # 检查response是否还有"请补充"的字段
    for item in response["报告内容"]:
        for metric in item["涉及的指标"]:
            if "值" in metric and metric["值"] == "请补充":
                return True
    return False


def generate_article(
    model_name="gpt-3.5-turbo",
    job_name="IT",
    mode="new",
    data_for_complete=None,
    data_for_reference=None,
    maintain_key_list=["报告时间", "公司信息"],
):
    time.sleep(random.random() * 1.5)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    system_prompt = "你是一名编造财务信息的专家，编造的财务信息天衣无缝，让人信服。"
    user_prompt = """下面是一份结构化的Schema，你需要根据这份Schema信息编造一份看起来**非常真实和完整的公司财务信息**。\n"""
    user_prompt += f"- 公司所属行业：{job_name}"
    user_prompt += """
- 结构化信息中的每个字段的值都是帮助你理解的解释性语句，你需要用具体的事件/数据填充这些字段（就是做填空题），以生成一家公司完整的财务信息记录。
- 所有的字段中的值应该非常真实，使人相信真正存在这家公司，真正发生了这些事件。**强调：公司、子公司、项目等也应该有非常真实、巧妙的名字，而不仅是一些示例型的占位文本（例如XYZ，ABC等肯定不存在于真实世界中的名字）。**
- "重要事件"字段给出了一些可能的事件，这只是对你的一些启发，你**必须尽最大可能编造多种不同的事件，使其看起来非常真实**，并且填充到这个列表中。
- "未来展望"字段必须包含公司未来的财务策略、投资计划、风险管理等信息，这些信息应该看起来非常真实。
- 你应该且必须自己完善各种细节（比如"涉及的指标"列表中，每个指标都有一个"值"字段是"请补充"的，你**必须自己生成值以填充**），使得生成的财务信息看起来非常真实，并且符合逻辑。
- "事件"字段中的事件在示例中都是正面的，你可以自由添加负面事件，使得生成的财务信息更加真实。
- 你必须以JSON格式回复。

"""
    # set time
    data_for_complete = set_time(mode, data_for_complete, data_for_reference)
    for item in data_for_complete["报告内容"]:
        for metric in item["涉及的指标"]:
            if "值" not in metric:
                metric["值"] = "请完善"
    # for mode == continue, set some fields to the same as the reference
    if mode == "new":
        user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    else:
        for key in maintain_key_list:
            data_for_complete[key] = data_for_reference[key]
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
            sort_event_by_time(response["报告内容"])
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")
            time.sleep(1)

    response["公司信息"]["行业"] = job_name
    return response


def generate_and_validate_article(model_name, job_name, mode, data_for_complete, data_for_reference=None, maintain_key_list=None):
    """Generate an article and validate it, with retries for 'no value' responses and handle json.loads exceptions."""
    
    response = generate_article(model_name, job_name, mode, data_for_complete, data_for_reference, maintain_key_list)
    # 检查响应值是否有效，如果无效（即no_value_check为True），继续内部循环直到有效
    while no_value_check(response):
        response = generate_article(model_name, job_name, mode, data_for_complete, data_for_reference, maintain_key_list)

    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="new")
    parser.add_argument("--model_name", type=str, default='gpt-3.5-turbo')
    parser.add_argument("--job_name", type=str, default="IT")
    parser.add_argument("--data_for_complete", type=str, required=True)
    parser.add_argument("--data_for_reference", type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()
    model_name = args.model_name

    # Load data
    data_for_complete = load_json_data(args.data_for_complete)
    data_for_reference = (
        load_json_data(args.data_for_reference) if args.data_for_reference else None
    )

    field_name = args.data_for_complete.split("/")[-1].split(".")[0]

    if args.mode == "new":
        job_name = args.job_name
        response = generate_and_validate_article(
            model_name, job_name, args.mode, data_for_complete
        )
        save_output(args.output_dir, response, job_name, args.json_idx, field_name, "json")
    else:
        job_name = data_for_reference["公司信息"]["行业"]
        response = generate_and_validate_article(
            model_name,
            job_name,
            args.mode,
            data_for_complete,
            data_for_reference,
            maintain_key_list=["报告时间", "公司信息"],
        )
        save_output(args.output_dir, response, job_name, args.json_idx, field_name, "json")


if __name__ == "__main__":
    main()
