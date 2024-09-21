import sys
import os
import json
import argparse
import logging
from dotenv import load_dotenv
from dataclasses import dataclass
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

# Load environment variables
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# Validate environment variables
if not openai_api_key:
    logging.error("OPENAI_API_KEY is not set in the environment.")
    sys.exit(1)

# Add root directory to system path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

from client import OpenAIClient as Client

@dataclass
class DataGeneration:
    """Class for generating data using a language model."""

    def __init__(self, openai_api_key, model_name):
        self.llm = Client(
            openai_api_key=openai_api_key,
            model_name=model_name,
        )
        
    def generate_data(self, jsonl_input: str, output_jsonl: str):
        """Generate data and write results to a file."""
        prompts = []
        with open('prompts/keypoint_prompt.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                json_data = json.loads(line)
                prompts.append(json_data)
                
        with open(jsonl_input, 'r', encoding='utf-8') as f:
            data_objects = [
                (json.loads(line), json.loads(line)["query"]["content"], json.loads(line)["ground_truth"]["content"])
                for line in f
            ]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_data = {
                executor.submit(self._process_data, data_object, question, ground_truth, prompts): data_object
                for data_object, question, ground_truth in data_objects
            }

            with open(output_jsonl, 'w', encoding='utf-8') as f:
                for future in tqdm(as_completed(future_to_data), total=len(data_objects)):
                    try:
                        data_object = future_to_data[future]
                        result = future.result()
                        f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    except Exception as exc:
                        logging.error(f"Generated an exception: {exc}")

    def _process_data(self, data_object: dict, question: str, ground_truth: str, prompts: List[Dict]) -> dict:
        """Process individual data objects in parallel."""
        for prompt in prompts:
            if prompt['prompt_type'].split('_')[-1] == data_object['language']:
                prompt_types = prompt
                break
            
        user_prompt = self._create_prompt(question, ground_truth, prompt_types)
        qa_tasks = [
            {
                "system_prompt": prompt_types['system_prompt'],
                "user_prompt": user_prompt,
            }
        ]
        model_response = self.llm.generate(qa_tasks)[0]
        data_object["ground_truth"]["keypoints"] = model_response.split("\n")
        return data_object

    def _create_prompt(self, question: str, ground_truth: str, prompt_types: List[Dict]) -> str:
        """Create a prompt for the language model."""

        return prompt_types['user_prompt'].format(question=question, ground_truth=ground_truth)

def main():
    parser = argparse.ArgumentParser(description='Generate keypoints using gpt model.')
    parser.add_argument('model_name', type=str, help='Name of the language model to use.')
    parser.add_argument('input_file_path', type=str, help='Path to the input JSONL file.')
    parser.add_argument('output_file_path', type=str, help='Path to the output JSONL file.')
    args = parser.parse_args()

    dg = DataGeneration(
        openai_api_key=openai_api_key,
        model_name=args.model_name
    )
    dg.generate_data(
        jsonl_input=args.input_file_path, 
        output_jsonl=args.output_file_path
    )

if __name__ == '__main__':
    main()