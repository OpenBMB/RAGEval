import sys
import os
import json
import random
import argparse
import time
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("BASE_URL")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema_file", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    schema = load_json_data(args.schema_file)
    output_dir = args.output_dir if args.output_dir else "./output/business-plan/zh/schema"

    # 保存过滤后的 schema
    save_output(output_dir, schema, "business_plan", 0, "business_plan", "json")


if __name__ == "__main__":
    main() 