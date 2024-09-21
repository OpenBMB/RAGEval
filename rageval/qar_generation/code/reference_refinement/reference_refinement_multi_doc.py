import sys
import os
import re
import glob
import logging
import argparse
from dotenv import load_dotenv
from typing import List, Dict
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
from data_processing.postprocess import postprocess_reference_check_multi_doc_zh, postprocess_reference_check_multi_doc_en
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

def question_format(
    domain: str, 
    language: str, 
    data: List[Dict]
):
    qa_pairs_information = []
    qa_pairs_compare = []
    
    if language == 'zh':
        if domain == 'finance':
            for item in data['qa_multi_document_information_integration']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "公司名": r['公司名'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "问题类型": item['问题类型'],
                    "问题": item['问题'],
                    'ref': new_refs,
                    "答案": item['答案'],
                }
                qa_pairs_information.append(obj)
            for item in data['qa_multi_document_compare']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "公司名": r['公司名'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "问题类型": item['问题类型'],
                    "问题": item['问题'],
                    'ref': new_refs,
                    "答案": item['答案'],
                }
                qa_pairs_compare.append(obj)
        if domain == 'law':
            for item in data['qa_multi_document_information_integration']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "法院名": r['法院名'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "问题类型": item['问题类型'],
                    "问题": item['问题'],
                    'ref': new_refs,
                    "答案": item['答案'],
                }
                qa_pairs_information.append(obj)
            for item in data['qa_multi_document_compare']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "法院名": r['法院名'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "问题类型": item['问题类型'],
                    "问题": item['问题'],
                    'ref': new_refs,
                    "答案": item['答案'],
                }
                qa_pairs_compare.append(obj)
        if domain == 'medical':
            for item in data['qa_multi_document_information_integration']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "医院_病人名": r['医院_病人名'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "问题类型": item['问题类型'],
                    "问题": item['问题'],
                    'ref': new_refs,
                    "答案": item['答案'],
                }
                qa_pairs_information.append(obj)
            for item in data['qa_multi_document_compare']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "医院_病人名": r['医院_病人名'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "问题类型": item['问题类型'],
                    "问题": item['问题'],
                    'ref': new_refs,
                    "答案": item['答案'],
                }
                qa_pairs_compare.append(obj)
    else:
        if domain == 'finance':
            for item in data['qa_multi_document_information_integration']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "company_name": r['company_name'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "question type": item['question type'],
                    "question": item['question'],
                    'ref': new_refs,
                    "answer": item['answer'],
                }
                qa_pairs_information.append(obj)
            for item in data['qa_multi_document_compare']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "company_name": r['company_name'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "question type": item['question type'],
                    "question": item['question'],
                    'ref': new_refs,
                    "answer": item['answer'],
                }
                qa_pairs_compare.append(obj)
        if domain == 'law':
            for item in data['qa_multi_document_information_integration']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "court_name": r['court_name'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "question type": item['question type'],
                    "question": item['question'],
                    'ref': new_refs,
                    "answer": item['answer'],
                }
                qa_pairs_information.append(obj)
            for item in data['qa_multi_document_compare']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "court_name": r['court_name'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "question type": item['question type'],
                    "question": item['question'],
                    'ref': new_refs,
                    "answer": item['answer'],
                }
                qa_pairs_compare.append(obj)
        if domain == 'medical':
            for item in data['qa_multi_document_information_integration']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "hospital_patient_name": r['hospital_patient_name'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "question type": item['question type'],
                    "question": item['question'],
                    'ref': new_refs,
                    "answer": item['answer'],
                }
                qa_pairs_information.append(obj)
            for item in data['qa_multi_document_compare']:
                new_refs = []
                for r in item['ref']:
                    r_obj = {
                        "hospital_patient_name": r['hospital_patient_name'],
                        "content": []
                    }
                    new_refs.append(r_obj)
                obj = {
                    "question type": item['question type'],
                    "question": item['question'],
                    'ref': new_refs,
                    "answer": item['answer'],
                }
                qa_pairs_compare.append(obj)
    return qa_pairs_information, qa_pairs_compare

def get_origin_text(domain: str, language: str, file_path: str) -> List[str]:
    """
    Get the original text from the JSON file.
    
    Args:
        domain (str): The domain of the document (e.g., 'finance').
        language (str): The language of the document ('en' or 'zh').
        file_path (str): The path to the JSON file containing document data.
        
    Returns:
        List[str]: A list of sentences in the original text.
    """
    sentences_1 = []
    sentences_2 = []
    if domain == 'finance':
        file = file_path.split('/')[-1]
        json_idx = file_path.split('/')[-2]
        if language == 'zh':
            topic_1 = file.split('_')[0]
            topic_2 = file.split('_')[1]
            chapter = file.split('_')[2]
            
            file_path_1 = f'output/{domain}/{language}/config/{topic_1}/{json_idx}/{chapter}'
            file_path_2 = f'output/{domain}/{language}/config/{topic_2}/{json_idx}/{chapter}'
            
            config_1 = read_config_json(file_path_1)
            config_2 = read_config_json(file_path_2)
            
            sentences_1 = split_sentences(config_1['生成总结'] + config_1['生成文章'], language)
            sentences_2 = split_sentences(config_2['生成总结'] + config_2['生成文章'], language)
        
        if language == 'en':
            topic_list = [
                "Agriculture", "Aviation", "Construction", "Consumer_Goods", "Culture", "Education", "Energy", "Entertainment", "Environmental_Protection", "Finance", "Government", "Healthcare", "Housekeeping", "IT", "Manufacturing", "Media", "Research_and_Development", "Retail", "Social", "Tourism"
            ]
            topic_list_temp = file.split('_')[:-2]
            topics = []
            for t in topic_list_temp:
                for topic in topic_list:
                    if t in topic:
                        topics.append(topic)
            topics = list(set(topics))
            topic_1 = topics[0]
            topic_2 = topics[1]
            chapter = file.split('_')[-2] + '_' + file.split('_')[-1]

            file_path_1 = f'output/{domain}/{language}/config/{topic_1}/{json_idx}/{chapter}'
            file_path_2 = f'output/{domain}/{language}/config/{topic_2}/{json_idx}/{chapter}'
            
            config_1 = read_config_json(file_path_1)
            config_2 = read_config_json(file_path_2)
            
            sentences_1 = split_sentences(config_1['Generated Summary'] + ' ' + config_1['Generated Article'], language)
            sentences_2 = split_sentences(config_2['Generated Summary'] + ' ' + config_2['Generated Article'], language)
    
    if domain == 'law':
        file = file_path.split('/')[-1]
        
        topic_1 = file.split('_')[0].split('-')[0]
        topic_2 = file.split('_')[1].split('-')[0]
        json_idx_1 = file.split('_')[0].split('-')[1]
        json_idx_2 = file.split('_')[1].split('-')[1].split('.json')[0]
        
        file_path_1 = f'output/{domain}/{language}/config/{topic_1}/{json_idx_1}/{json_idx_1}.json'
        file_path_2 = f'output/{domain}/{language}/config/{topic_2}/{json_idx_2}/{json_idx_2}.json'
        
        config_1 = read_config_json(file_path_1)
        config_2 = read_config_json(file_path_2)
        
        if language == 'zh':
            sentences_1 = split_sentences(config_1['生成文章'], language)
            sentences_2 = split_sentences(config_2['生成文章'], language)
        else:
            sentences_1 = split_sentences(config_1['Generated Article'], language)
            sentences_2 = split_sentences(config_2['Generated Article'], language)

    if domain == 'medical':
        json_idx = file_path.split('/')[-2]
        file = file_path.split('/')[-1]
        topic_1 = file.split('_')[0]
        topic_2 = file.split('_')[1].split('.json')[0]
        
        json_files = []
        for root, dirs, files in os.walk(f'output/{domain}/{language}/config'):
            for dir_name in dirs:
                if dir_name == str(json_idx):
                    json_files.extend(glob.glob(os.path.join(root, dir_name, f'{topic_1}.json')))
                    json_files.extend(glob.glob(os.path.join(root, dir_name, f'{topic_2}.json')))
        
        file_path_1 = json_files[0]
        file_path_2 = json_files[1]
        
        config_1 = read_config_json(file_path_1)
        config_2 = read_config_json(file_path_2)
        
        if language == 'zh':
            sentences_1 = split_sentences(config_1['生成文章'], language)
            sentences_2 = split_sentences(config_2['生成文章'], language)
        else:
            sentences_1 = split_sentences(config_1['Generated Article'], language)
            sentences_2 = split_sentences(config_2['Generated Article'], language)

    return sentences_1, sentences_2
        
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
    
    data = read_config_json(file_path)
    
    sentences_1 = get_origin_text(domain, language, file_path)[0]
    sentences_2 = get_origin_text(domain, language, file_path)[1]
    
    # Number sentences
    new_sentences_1 = [f'[{i}] {sentence}' for i, sentence in enumerate(sentences_1, start=1)]
    new_sentences_2 = [f'[{i}] {sentence}' for i, sentence in enumerate(sentences_2, start=1)]
    
    qa_pairs_information = []
    qa_pairs_compare = []
    
    # Prepare QA pairs based on language
    qa_pairs_information, qa_pairs_compare = question_format(domain, language, data)
    
    # Prepare tasks and generate responses
    qa_tasks = []
    if language == 'zh':
        for prompt in prompts:
            if prompt['prompt_type'] == 'reference_refinement_multi_doc_zh':
                system_prompt = prompt['system_prompt']
                user_prompt = prompt['user_prompt']
        
        qa_tasks = [
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc_1=new_sentences_1, doc_2=new_sentences_2, qa_pairs=qa_pairs_information)},
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc_1=new_sentences_1, doc_2=new_sentences_2, qa_pairs=qa_pairs_compare)}
        ]
        
        responses = gpt_client.generate(qa_tasks)
        responses = [postprocess_reference_check_multi_doc_zh(responses[i], domain, new_sentences_1, new_sentences_2, qa_tasks[i]['system_prompt'], qa_tasks[i]['user_prompt'], model_name) for i in range(2)]
    
    else:
        for prompt in prompts:
            if prompt['prompt_type'] == 'reference_refinement_multi_doc_en':
                system_prompt = prompt['system_prompt']
                user_prompt = prompt['user_prompt']
        
        qa_tasks = [
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc_1=new_sentences_1, doc_2=new_sentences_2, qa_pairs=qa_pairs_information)},
            {"system_prompt": system_prompt, "user_prompt": user_prompt.format(doc_1=new_sentences_1, doc_2=new_sentences_2, qa_pairs=qa_pairs_compare)}
        ]
        
        responses = gpt_client.generate(qa_tasks)
        responses = [postprocess_reference_check_multi_doc_en(responses[i], domain, new_sentences_1, new_sentences_2, qa_tasks[i]['system_prompt'], qa_tasks[i]['user_prompt'], model_name) for i in range(2)]
    
    json_obj = {
        "qa_multi_document_information_integration": responses[0],
        "qa_multi_document_compare": responses[1]
    }
    data.update(json_obj)
    write_config_json(file_path, data)
    print(f"Finished processing {file_path}")
    
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
    for root, _, files in os.walk(f'output_1/{domain}/{language}/qra_multidoc'):
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
    parser.add_argument("--domains", type=str, required=True, help="Comma-separated list of domains")
    parser.add_argument("--languages", type=str, required=True, help="Comma-separated list of languages")
    parser.add_argument("--model_name", type=str, required=True, help="Name of the OpenAI model to use")

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