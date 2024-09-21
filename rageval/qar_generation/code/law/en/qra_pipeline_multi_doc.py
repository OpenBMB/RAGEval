import sys
import os
import argparse
import logging
import random
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

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
from data_processing.postprocess import postprocess_en
from utils.utils import read_prompt, read_config_json, write_config_json

def process_qra_documents(model_name: str,
    input_dir: str,
    output_dir: str,
    topic_1: str,
    topic_2: str,
    select_number_1: int,
    select_number_2: int,
    prompts: List[Dict]
) -> None:
    """Processes QRA documents using GPT client."""
    
    gpt_client = Client(
        openai_api_key=openai_api_key, 
        model_name=model_name
    )
    select_chapter_1 = f'{select_number_1}.json'
    select_chapter_2 = f'{select_number_2}.json'
    topic_path_1 = os.path.join(input_dir, topic_1, str(select_number_1), select_chapter_1)
    topic_path_2 = os.path.join(input_dir, topic_2, str(select_number_2), select_chapter_2)
    
    config_1_raw = read_config_json(topic_path_1)
    config_2_raw = read_config_json(topic_path_2)
    
    config_1 = {
        "courtAndProcuratorate": config_1_raw['courtAndProcuratorate'],
        "chiefJudge": config_1_raw['chiefJudge'],
        "judge": config_1_raw['judge'],
        "clerk": config_1_raw['clerk'],
        "defendant": config_1_raw['defendant'],
        "defenseLawyer": config_1_raw['defenseLawyer'],
        "caseProcess": config_1_raw['caseProcess'],
        "criminalFacts": config_1_raw['criminalFacts'],
        "legalProcedure": config_1_raw['legalProcedure'],
    }
    config_2 = {
        "courtAndProcuratorate": config_2_raw['courtAndProcuratorate'],
        "chiefJudge": config_2_raw['chiefJudge'],
        "judge": config_2_raw['judge'],
        "clerk": config_2_raw['clerk'],
        "defendant": config_2_raw['defendant'],
        "defenseLawyer": config_2_raw['defenseLawyer'],
        "caseProcess": config_2_raw['caseProcess'],
        "criminalFacts": config_2_raw['criminalFacts'],
        "legalProcedure": config_2_raw['legalProcedure'],
    }
    
    # Prepare prompt types
    prompt_types = {p['prompt_type']: p for p in prompts if p['prompt_type'] in ['Multi-document Information Integration Question', 'Multi-document Comparison Question', 'multi document reference']}
    
    # Prepare QRA tasks
    qa_tasks = [
        {
            "system_prompt": prompt_types[key]['system_prompt'],
            "user_prompt": prompt_types[key]['user_prompt'].format(
                config_1=config_1,
                config_2=config_2
            )
        }
        for key in ['Multi-document Information Integration Question', 'Multi-document Comparison Question']
    ]
    
    # Generate responses
    responses = gpt_client.generate(qa_tasks)
    
    # Postprocess and update the config
    for i, key in enumerate(['qa_multi_document_information_integration', 'qa_multi_document_compare']):
        responses[i] = postprocess_en(
            response=responses[i],
            system_prompt=qa_tasks[i]['system_prompt'],
            user_prompt=qa_tasks[i]['user_prompt'],
            model_name=model_name
        )
        config_1[key] = responses[i]
    
    # Additional processing for reference extraction
    doc_content_1 = config_1_raw['Generated Article']
    doc_content_2 = config_2_raw['Generated Article']
    qa_tasks = [
        {
            "system_prompt": prompt_types['multi document reference']['system_prompt'],
            "user_prompt": prompt_types['multi document reference']['user_prompt'].format(
                doc_1=doc_content_1,
                doc_2=doc_content_2,
                qa_pairs=config_1[key]
            )
        }
        for key in ['qa_multi_document_information_integration', 'qa_multi_document_compare']
    ]
    
    # Generate responses
    responses = gpt_client.generate(qa_tasks)
    
    result_json_obj = {
        'qa_multi_document_information_integration': [],
        'qa_multi_document_compare': []
    }
    
    # Postprocess and create multi-doc json files
    for i, key in enumerate(['qa_multi_document_information_integration', 'qa_multi_document_compare']):
        responses[i] = postprocess_en(
            response=responses[i],
            system_prompt=qa_tasks[i]['system_prompt'],
            user_prompt=qa_tasks[i]['user_prompt'],
            model_name=model_name
        )
        result_json_obj[key] = responses[i]
    
    new_file_name = f'{topic_1}-{select_number_1}_{topic_2}-{select_number_2}.json'
    new_file_path = os.path.join(output_dir, new_file_name)
    write_config_json(new_file_path, result_json_obj)
    logging.info(f"Finished processing {new_file_path}.")

def generate_qra(model_name: str,
    input_dir: str,
    output_dir: str,
    json_idx: int,
    number: int
) -> None:
    """Generate QRA triples for random two documents in the specific json_idx in Finance."""
    prompts = read_prompt(
        file_path='prompts/law_en.jsonl',
    )
    
    topic_list = [
        "Crime of Bending the Law for Personal Gain", "Crime of Counterfeiting Currency", "Crime of Embezzlement", "Crime of Evading Tax Arrears Recovery", "Crime of Intentional Homicide", "Crime of Negligent Homicide", "Crime of Picking Quarrels and Provoking Trouble", "Crime of Selling Counterfeit Registered Trademark Goods", "Crime of Theft", "Crime of Traffic Accident"
    ]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(number):
            select_list_topic = random.sample(topic_list, 2)
            topic_1, topic_2 = select_list_topic
            select_list_number = random.choices(range(json_idx + 1), k=2)
            select_number_1, select_number_2 = select_list_number[0], select_list_number[1]
            futures.append(executor.submit(
                process_qra_documents, model_name, input_dir, output_dir, topic_1, topic_2, select_number_1, select_number_2, prompts
            ))
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error processing future: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='gpt-4o')
    parser.add_argument('--input_dir', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--number', type=int, default=1)
    parser.add_argument('--json_idx', type=int, default=0)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    generate_qra(
        model_name=args.model_name, 
        input_dir=args.input_dir, 
        output_dir=args.output_dir, 
        json_idx=args.json_idx, 
        number=args.number
    )
    
if __name__ == "__main__":
    main()
        
    
    
    