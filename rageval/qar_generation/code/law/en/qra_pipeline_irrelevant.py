import sys
import os
import glob
import argparse
import logging
from dotenv import load_dotenv
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# Validate environment variables
if not openai_api_key:
    logging.error("OPENAI_API_KEY is not set in the environment.")
    sys.exit(1)

# Add root directory to system path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(root_dir)

from client import OpenAIClient as Client
from data_processing.postprocess import postprocess_irrelevant_en
from utils.utils import read_prompt, read_config_json, write_config_json

def process_qra_document(model_name: str, file_path: str, prompts: List[str]) -> List:
    """Process each document to generate QRA triples."""
    gpt_client = Client(
        openai_api_key=openai_api_key, 
        model_name=model_name
    )
    config = read_config_json(file_path)
    doc = config['Generated Article']
    court_name = config['courtAndProcuratorate']['court']
    
    # Prepare prompt types
    prompt_types = {p['prompt_type']: p for p in prompts if p['prompt_type'] in ['Irrelevant Unsolvable Question']}
    
    # Prepare QRA tasks
    qa_tasks = [
        {
            "system_prompt": prompt_types['Irrelevant Unsolvable Question']['system_prompt'],
            "user_prompt": prompt_types['Irrelevant Unsolvable Question']['user_prompt'].format(doc=doc),
        }
    ]
    
    # Generate responses
    responses = gpt_client.generate(qa_tasks)
    
    responses = postprocess_irrelevant_en(
        response=responses[0],
        system_prompt=qa_tasks[0]['system_prompt'],
        user_prompt=qa_tasks[0]['user_prompt'],
        model_name=model_name,
        domain='law',
        name=court_name,
    )
    return responses

def generate_qra(model_name: str, input_dir: str, output_dir: str, json_idx: int, number: int) -> None:
    """Generate Irrelevant Unanswerable Question QRA triples in Law."""
    prompts = read_prompt(
        file_path='prompts/law_en.jsonl',
    )
    
    json_files = []
    for root, dirs, files in os.walk(input_dir):
        for dir_name in dirs:
            if dir_name == str(json_idx):
                json_files.extend(glob.glob(os.path.join(root, dir_name, '*.json')))
                
    count = 0
    output = []
    while count < number:
        for file_path in json_files:
            results = process_qra_document(
                model_name=model_name,
                file_path=file_path,
                prompts=prompts,
            )
            output.extend(results)
            count += len(results)
            if count >= number:
                break
    
    output_file_path = os.path.join(output_dir, f'qra_irrelevant.json')
    write_config_json(output_file_path, output)
    logging.info(f"Generated {count} QRA triples in '{output_file_path}'.")
    
def main():
    parser = argparse.ArgumentParser(description="Generate Irrelevant Unanswerable Question QRA triples in Law.")
    parser.add_argument('--model_name', type=str, required=True, help="The model name to use for generating QRA triples.")
    parser.add_argument('--input_dir', type=str, required=True, help="The input directory containing the JSON files.")
    parser.add_argument('--output_dir', type=str, required=True, help="The output directory to save the generated QRA triples.")
    parser.add_argument('--json_idx', type=int, required=True, help="The index of the JSON file to process.")
    parser.add_argument('--number', type=int, required=True, help="The number of QRA triples to generate.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    generate_qra(
        model_name=args.model_name,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        json_idx=args.json_idx,
        number=args.number,
    )
    
if __name__ == '__main__':
    main()
            
    