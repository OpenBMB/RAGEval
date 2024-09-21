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
from data_processing.postprocess import postprocess_zh
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
        "法院和检察院": config_1_raw['法院和检察院'],
        "审判长": config_1_raw['审判长'],
        "审判员": config_1_raw['审判员'],
        "书记员": config_1_raw['书记员'],
        "被告人": config_1_raw['被告人'],
        "辩护人": config_1_raw['辩护人'],
        "案件经过": config_1_raw['案件经过'],
        "犯罪事实": config_1_raw['犯罪事实'],
        "法律程序": config_1_raw['法律程序'],
    }
    config_2 = {
        "法院和检察院": config_2_raw['法院和检察院'],
        "审判长": config_2_raw['审判长'],
        "审判员": config_2_raw['审判员'],
        "书记员": config_2_raw['书记员'],
        "被告人": config_2_raw['被告人'],
        "辩护人": config_2_raw['辩护人'],
        "案件经过": config_2_raw['案件经过'],
        "犯罪事实": config_2_raw['犯罪事实'],
        "法律程序": config_2_raw['法律程序'],
    }
    
    # Prepare prompt types
    prompt_types = {p['prompt_type']: p for p in prompts if p['prompt_type'] in ['多文档信息整合问题', '多文档比较问题', '多文档reference抽取']}
    
    # Prepare QRA tasks
    qa_tasks = [
        {
            "system_prompt": prompt_types[key]['system_prompt'],
            "user_prompt": prompt_types[key]['user_prompt'].format(
                config_1=config_1,
                config_2=config_2
            )
        }
        for key in ['多文档信息整合问题', '多文档比较问题']
    ]
    
    # Generate responses
    responses = gpt_client.generate(qa_tasks)
    
    # Postprocess and update the config
    for i, key in enumerate(['qa_multi_document_information_integration', 'qa_multi_document_compare']):
        responses[i] = postprocess_zh(
            response=responses[i],
            system_prompt=qa_tasks[i]['system_prompt'],
            user_prompt=qa_tasks[i]['user_prompt'],
            model_name=model_name
        )
        config_1[key] = responses[i]
    
    # Additional processing for reference extraction
    doc_content_1 = config_1_raw['生成文章']
    doc_content_2 = config_2_raw['生成文章']
    qa_tasks = [
        {
            "system_prompt": prompt_types['多文档reference抽取']['system_prompt'],
            "user_prompt": prompt_types['多文档reference抽取']['user_prompt'].format(
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
        responses[i] = postprocess_zh(
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
        file_path='prompts/law_zh.jsonl',
    )
    
    topic_list = [
        "盗窃罪", "故意杀人罪", "过失致人死亡罪", "交通肇事罪", "挪用公款罪", "逃避追缴欠税罪", "伪造货币罪", "销售假冒注册商标的商品罪", "寻衅滋事罪", "徇私枉法罪"
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
    parser.add_argument('--json_idx', type=int, default=0)
    parser.add_argument('--number', type=int, default=1)
    
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