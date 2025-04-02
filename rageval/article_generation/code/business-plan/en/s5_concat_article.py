import sys
import os
import json
import argparse
import pathlib
import time
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

from dotenv import load_dotenv

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

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


def concat_article(file_path, output_dir, industry, json_idx):
    """Concatenate generated sections into a complete article."""
    try:
        data = load_json_data(file_path)
        article = data.get("Generated Article", "")

        # Save as txt
        save_output(
            output_dir,
            article,
            industry,
            str(json_idx),
            file_path.stem,
            "txt"
        )

        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def process_industry(industry, file_dir_path, json_idx, output_dir):
    """Process all articles for a single industry."""
    industry_safe = industry.replace(' ', '_')
    job_input_path = file_dir_path / industry_safe / str(json_idx)
    
    results = []
    for file in job_input_path.iterdir():
        if file.suffix == ".json":
            file_path = job_input_path / file.name
            results.append(concat_article(file_path, output_dir, industry_safe, json_idx))
    
    return all(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_dir_path', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--json_idx', type=int, default=0)
    args = parser.parse_args()
    
    file_dir_path = pathlib.Path(args.file_dir_path)
    output_dir = pathlib.Path(args.output_dir)
    json_idx = args.json_idx

    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=20) as executor:
        results = list(
            tqdm(
                executor.map(
                    process_industry,
                    industry_list,
                    [file_dir_path] * len(industry_list),
                    [json_idx] * len(industry_list),
                    [output_dir] * len(industry_list),
                ),
                total=len(industry_list),
            )
        )

    if all(results):
        print("All business plans successfully concatenated and saved.")
    else:
        print("Some business plans failed to process. Check errors above.")


if __name__ == "__main__":
    main() 