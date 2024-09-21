import sys
import os
import re
import logging
import argparse
from dotenv import load_dotenv
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from pysbd import Segmenter

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
from data_processing.postprocess import postprocess_reference_check_single_doc_zh, postprocess_reference_check_single_doc_en
from utils.utils import read_config_json, write_config_json, read_prompt

# Initialize segmenters for English
segmenter_en = Segmenter(language='en')

def cut_sent(para):
    """
    Split Chinese text into sentences.
    """
    para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)  
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  
    para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)
    para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
    para = para.rstrip()
    return para.split("\n")

def split_sentences(text: str, language: str) -> List[str]:
    """
    Split text into sentences based on the specified language.
    
    Args:
        text (str): The text to be split.
        language (str): The language of the text ('en' or 'zh').

    Returns:
        List[str]: A list of sentences.
    """
    if language == 'en':
        return segmenter_en.segment(text)
    else:
        return cut_sent(text)

def process_document(
    domain: str,
    language: str,
    file_path: str,
    prompts: List[dict],
    model_name: str
) -> None:
    """
    Process a single document to generate and refine QA pairs using OpenAI API.
    
    Args:
        domain (str): The domain of the document (e.g., 'finance').
        language (str): The language of the document ('en' or 'zh').
        file_path (str): The path to the JSON file containing document data.
        prompts (List[dict]): A list of prompts for generating questions.
        model_name (str): The name of the OpenAI model to use.
    """
    gpt_client = Client(
        openai_api_key=openai_api_key,
        model_name=model_name
    )
    config = read_config_json(file_path)

    # Split sentences based on domain and language
    if domain == 'finance':
        if language == 'zh':
            sentences = split_sentences(config['生成总结'] + config['生成文章'], language)
        else:
            sentences = split_sentences(config['Generated Summary'] + ' ' + config['Generated Article'], language)
    else:
        if language == 'zh':
            sentences = split_sentences(config['生成文章'], language)
        else:
            sentences = split_sentences(config['Generated Article'], language)

    # Number sentences
    new_sentences = [f'[{i}] {sentence}' for i, sentence in enumerate(sentences, start=1)]

    qa_pairs_fact_based = []
    qa_pairs_multi_hop = []
    qa_pairs_summary = []

    # Prepare QA pairs based on language
    if language == 'zh':
        for item in config['qa_fact_based']:
            qa_pairs_fact_based.append({
                "问题类型": item['问题类型'],
                "问题": item['问题'],
                "答案": item['答案']
            })
        for item in config['qa_multi_hop']:
            qa_pairs_multi_hop.append({
                "问题类型": item['问题类型'],
                "问题": item['问题'],
                "答案": item['答案']
            })
        for item in config['qa_summary']:
            qa_pairs_summary.append({
                "问题类型": item['问题类型'],
                "问题": item['问题'],
                "答案": item['答案']
            })
    else:
        for item in config['qa_fact_based']:
            qa_pairs_fact_based.append({
                "question type": item['question type'],
                "question": item['question'],
                "answer": item['answer']
            })
        for item in config['qa_multi_hop']:
            qa_pairs_multi_hop.append({
                "question type": item['question type'],
                "question": item['question'],
                "answer": item['answer']
            })
        for item in config['qa_summary']:
            qa_pairs_summary.append({
                "question type": item['question type'],
                "question": item['question'],
                "answer": item['answer']
            })

    # Prepare tasks and generate responses
    qa_tasks = []
    if language == 'zh':
        for prompt in prompts:
            if prompt['prompt_type'] == 'reference_refinement_single_doc_zh':
                system_prompt = prompt['system_prompt']
                user_prompt = prompt['user_prompt']
        
        qa_tasks = [
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc=new_sentences, qa_pairs=qa_pairs_fact_based)},
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc=new_sentences, qa_pairs=qa_pairs_multi_hop)},
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc=new_sentences, qa_pairs=qa_pairs_summary)},
        ]

        responses = gpt_client.generate(qa_tasks)
        responses = [postprocess_reference_check_single_doc_zh(responses[i], new_sentences, qa_tasks[i]['system_prompt'], qa_tasks[i]['user_prompt'], 'gpt-4o') for i in range(3)]
    else:
        for prompt in prompts:
            if prompt['prompt_type'] == 'reference_refinement_single_doc_en':
                system_prompt = prompt['system_prompt']
                user_prompt = prompt['user_prompt']
        
        qa_tasks = [
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc=new_sentences, qa_pairs=qa_pairs_fact_based)},
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc=new_sentences, qa_pairs=qa_pairs_multi_hop)},
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc=new_sentences, qa_pairs=qa_pairs_summary)},
        ]

        responses = gpt_client.generate(qa_tasks)
        responses = [postprocess_reference_check_single_doc_en(responses[i], new_sentences, qa_tasks[i]['system_prompt'], qa_tasks[i]['user_prompt'], 'gpt-4o') for i in range(3)]

    json_obj = {
        "qa_fact_based": responses[0],
        "qa_multi_hop": responses[1],
        "qa_summary": responses[2]
    }
    config.update(json_obj)
    write_config_json(file_path, config)
    print(f"Finished processing {file_path}.")

def ref_refine(domain: str, language: str, model_name: str) -> None:
    """
    Refine references for all documents in the specified domain and language.
    
    Args:
        domain (str): The domain of the documents (e.g., 'finance').
        language (str): The language of the documents ('en' or 'zh').
    """
    prompts = read_prompt(file_path='prompts/reference_refinement_prompt.jsonl')
    json_files = []

    # Collect all JSON files for processing
    for root, _, files in os.walk(f'output/{domain}/{language}/config'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                json_files.append(file_path)

    # Process documents concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_document, domain, language, file_path, prompts, model_name) for file_path in json_files]
        for future in as_completed(futures):
            future.result()

def main():
    parser = argparse.ArgumentParser(description="Refine references for all documents in the specified domain and language.")
    parser.add_argument("--model_name", type=str, required=True, help="The name of the OpenAI model to use")
    parser.add_argument("--domains", type=str, required=True, help="Comma-separated list of domains")
    parser.add_argument("--languages", type=str, required=True, help="Comma-separated list of languages")

    args = parser.parse_args()

    # Split the comma-separated domains into a list
    domains = args.domains.split(',')
    languages = args.languages.split(',')
    
    for domain in domains:
        for language in languages:
            ref_refine(
                domain=domain, 
                language=language, 
                model_name=args.model_name
            )

if __name__ == '__main__':
    main()