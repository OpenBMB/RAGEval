import os
import json
import os
import json
import sys
import argparse
from dotenv import load_dotenv
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data


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

def save_output(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_dir_path', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--json_idx', type=int, default=0)
    args = parser.parse_args()
    file_dir_path = Path(args.file_dir_path)
    output_dir_path = Path(args.output_dir)
    json_idx = args.json_idx
    file_name_list = ["financial_report.json", "corporate_governance.json"]

    for job in job_list:
        article_list = []
        for idx, file_name in enumerate(file_name_list):
            file_path = file_dir_path / job.replace(' ', '_') / str(json_idx) / file_name
            data = load_json_data(file_path)
            article = data["Generated Article"]
            temp_list = article.split("\n")
            temp_list = [i.strip() for i in temp_list if i]
            article = "\n".join(temp_list)
            if idx == 0:
                article_list.append(data["Generated Summary"])
            article_list.append(article)
        article_to_save = '\n'.join(article_list)
        os.makedirs(output_dir_path / str(json_idx), exist_ok=True)
        output_file_path = output_dir_path / str(json_idx) /'_'.join(['company_report', job, f"{json_idx}.txt"])
        save_output(article_to_save, output_file_path)

if __name__ == "__main__":
    main()
