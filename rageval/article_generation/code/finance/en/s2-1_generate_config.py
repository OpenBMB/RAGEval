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
#     "Finance",
#     "Healthcare",
#     "Retail",
#     "Media",
#     "Construction",
#     "Manufacturing",
#     "Energy",
#     "Consumer Goods",
#     "Education",
#     "Agriculture",
#     "Tourism",
#     "Entertainment",
#     "Government",
#     "Environmental Protection",
#     "Research and Development",
#     "Culture",
#     "Social",
#     "Aviation",
#     "Housekeeping"
# ]
year_list = [2017, 2018, 2019, 2020, 2021]
season_list = ["Q1", "Q2", "Q3", "Q4"]
season_month_dict = {
    "Q1": [1, 2, 3],
    "Q2": [4, 5, 6],
    "Q3": [7, 8, 9],
    "Q4": [10, 11, 12],
}
month_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def sample_month(month_list, event_len):
    if event_len <= len(month_list):
        return random.sample(month_list, event_len)
    else:
        return random.choices(month_list, k=event_len)


def sort_event_by_time(report_contents):
    for item in report_contents:
        for event in item["Significant Events"]:
            event["Time OBJ"] = datetime.strptime(event["Time"], "%B, %Y")
        item["Significant Events"].sort(key=lambda x: x["Time OBJ"])
        for event in item["Significant Events"]:
            del event["Time OBJ"]


def assign_event_times(year, months, report_contents):
    # 为每个重要事件指定时间
    for item in report_contents:
        event_len = len(item["Significant Events"])
        selected_months = sample_month(months, event_len)
        for event in item["Significant Events"]:
            event["Time"] = f"{selected_months.pop()}, {year}"


def set_time(mode, data_for_complete, data_for_reference=None):
    if mode == "new":
        # 随机年度/季度报告时间
        year = random.choice(year_list)
        season = random.choice(season_list)
        # only 年度
        if random.random() > 0:
            data_for_complete["Report Time"] = f"{year}"
            assign_event_times(year, month_list, data_for_complete["Report Content"])
            sort_event_by_time(data_for_complete["Report Content"])
        else:
            data_for_complete["Report Time"] = f"{season}, {year}"
            assign_event_times(
                year, season_month_dict[season], data_for_complete["Report Content"]
            )
    else:
        year = data_for_reference["Report Time"]
        season = data_for_reference["Report Time"].split(", ")[0]
        if "Q" not in season:
            assign_event_times(year, month_list, data_for_complete["Report Content"])
        else:
            assign_event_times(
                year, season_month_dict[season], data_for_complete["Report Content"]
            )

    return data_for_complete


def no_value_check(response):
    # 检查response是否还有"请补充"的字段
    for item in response["Report Content"]:
        for metric in item["Involved Indicators"]:
            if "Value" in metric and metric["Value"] == "Please Fill in":
                return True
    return False

def generate_article(
    model_name="gpt-3.5-turbo",
    job_name="IT",
    mode="new",
    data_for_complete=None,
    data_for_reference=None,
    maintain_key_list=["Report Time", "Company Information"],
):
    time.sleep(random.random() * 1.5)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    system_prompt = "You are an expert in fabricating financial information, crafting it so seamlessly that it convinces others of its authenticity."
    user_prompt = "Below is a structured schema that you need to use as a guide to create a very real and complete set of financial information for a company.\n"
    user_prompt += f"- Industry of the company: {job_name}"
    user_prompt += """
- The value of each field in the structured information is an interpretative statement to help you understand; you need to fill these fields with specific events/data (like filling in the blanks) to generate a complete financial record for a company.
- All the values in the fields should appear very real, convincing someone that this company truly exists and these events really occurred. **Emphasis: The names of the company, projects, etc., should also be very realistic and clever, not just some example-type placeholder texts (e.g., XYZ, ABC) that definitely don't exist in the real world.**
- The "Significant Events" field provides some possible events for inspiration, but you **must make the utmost effort to invent a variety of different events that look very real** and populate this list with them.
- The "Future Outlook" field must include the company's future financial strategies, investment plans, risk management, etc., information that should look very real.
- You should and must perfect various details on your own (for example, in the "Involved Indicators" list, each indicator has a "value" field that is "please fill in," and you **must generate values to fill in**) to make the generated financial information look very real and logical.
- The events in the "Events" field in the example are all positive, but you can freely add negative events to make the generated financial information more realistic.
- You must reply in JSON format.

"""
    # set time
    data_for_complete = set_time(mode, data_for_complete, data_for_reference)
    for item in data_for_complete["Report Content"]:
        for metric in item["Involved Indicators"]:
            if "Value" not in metric:
                metric["Value"] = "Please Fill in"
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
            sort_event_by_time(response["Report Content"])
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")
            time.sleep(1)
    ## return json obj
    response["Company Information"]["Industry"] = job_name
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
        save_output(args.output_dir, response, job_name.replace(' ', '_'), args.json_idx, field_name, "json")
    else:
        job_name = data_for_reference["Company Information"]["Industry"]
        response = generate_and_validate_article(
            model_name,
            job_name,
            args.mode,
            data_for_complete,
            data_for_reference,
            maintain_key_list=["Report Time", "Company Information"],
        )
        save_output(args.output_dir, response, job_name.replace(' ', '_'), args.json_idx, field_name, "json")


if __name__ == "__main__":
    main()
