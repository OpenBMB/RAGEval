import os
import json
import argparse
from typing import List, Dict

def read_jsonl_doc(
    doc_path: str
) -> list:
    docs_data = []
    with open(doc_path, 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            docs_data.append(doc)   
    return docs_data
    

def qa_format_single_doc(
    domain: str,
    language: str,
    docs: List[Dict]
) -> List[Dict]:
    key_list = [
        "qa_fact_based",
        "qa_multi_hop",
        "qa_summary"
    ]
    
    input_path = f'output/{domain}/{language}/config'
    
    output = []
    
    for root, dirs, files in os.walk(input_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                if domain == 'finance':
                    if language == 'zh':
                        company_name = json_data['公司信息']['名称']
                    else:
                        company_name = json_data['Company Information']['Name']
                    
                    for doc in docs:
                        if 'company_name' in doc:
                            if doc['company_name'] == company_name:
                                doc_id = doc['doc_id']
                                break
                        
                if domain == 'law':
                    if language == 'zh':
                        court_name = json_data['法院和检察院']['法院']
                    else:
                        court_name = json_data['courtAndProcuratorate']['court']
                    
                    for doc in docs:
                        if 'court_name' in doc:
                            if doc['court_name'] == court_name:
                                doc_id = doc['doc_id']
                                break
                        
                if domain == 'medical':
                    if language == 'zh':
                        hospital_patient_name = json_data['住院病历']['基本信息']['医院名称'] + '_' + json_data['住院病历']['基本信息']['姓名']
                    else:
                        hospital_patient_name = json_data['Hospitalization Record']['Basic Information']['Hospital Name'] + '_' + json_data['Hospitalization Record']['Basic Information']['Name']
                    
                    for doc in docs:
                        if 'hospital_patient_name' in doc:
                            if doc['hospital_patient_name'] == hospital_patient_name:
                                doc_id = doc['doc_id']
                                break
                
                for key in key_list:
                    for qa in json_data[key]:
                        if language == 'zh':
                            jsonl_obj = {
                                "domain": domain.capitalize(),
                                "language": language,
                                "query": {
                                    "query_id": 0,
                                    "query_type": qa['问题类型'],
                                    "content": qa['问题'],
                                },
                                "ground_truth": {
                                    "doc_ids": [doc_id],
                                    "content": qa['答案'],
                                    "references": qa['ref'],
                                    "keypoints": ""
                                },
                                "prediction": {
                                    "content": "",
                                    "references": []
                                }
                            }
                        else:
                            jsonl_obj = {
                                "domain": domain.capitalize(),
                                "language": language,
                                "query": {
                                    "query_id": 0,
                                    "query_type": qa['question type'],
                                    "content": qa['question'],
                                },
                                "ground_truth": {
                                    "doc_ids": [doc_id],
                                    "content": qa['answer'],
                                    "references": qa['ref'],
                                    "keypoints": ""
                                },
                                "prediction": {
                                    "content": "",
                                    "references": []
                                }
                            }
                        output.append(jsonl_obj)           
    return output
            
def qa_format_multi_doc(
    domain: str,
    language: str,
    docs: List[Dict]
) -> List[Dict]:
    
    key_list = [
        'qa_multi_document_information_integration',
        'qa_multi_document_compare'
    ]
    
    input_path = f'output/{domain}/{language}/qra_multidoc'
    
    output = []
    
    for root, dirs, files in os.walk(input_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                for key in key_list:
                    doc_ids = []
                    for qa in json_data[key]:
                        ref_list = []
                        
                        for ref in qa['ref']:
                            for doc in docs:
                                if domain == 'finance':
                                    if language == 'zh' and 'company_name' in doc:
                                        if ref['公司名'] == doc['company_name']:
                                            doc_id = doc['doc_id']
                                            for r in ref['content']:
                                                ref_list.append(r)
                                            doc_ids.append(doc_id)
                                            break
                                    if language == 'en' and 'company_name' in doc:
                                        if ref['company_name'] == doc['company_name']:
                                            doc_id = doc['doc_id']
                                            for r in ref['content']:
                                                ref_list.append(r)
                                            doc_ids.append(doc_id)
                                            break
                                if domain == 'law':
                                    if language == 'zh' and 'court_name' in doc:
                                        if ref['法院名'] == doc['court_name']:
                                            doc_id = doc['doc_id']
                                            for r in ref['content']:
                                                ref_list.append(r)
                                            doc_ids.append(doc_id)
                                            break
                                    if language == 'en' and 'court_name' in doc:
                                        if ref['court_name'] == doc['court_name']:
                                            doc_id = doc['doc_id']
                                            for r in ref['content']:
                                                ref_list.append(r)
                                            doc_ids.append(doc_id)
                                            break
                                if domain == 'medical':
                                    if language == 'zh' and 'hospital_patient_name' in doc:
                                        if ref['医院_病人名'] == doc['hospital_patient_name']:
                                            doc_id = doc['doc_id']
                                            for r in ref['content']:
                                                ref_list.append(r)
                                            doc_ids.append(doc_id)
                                            break
                                    if language == 'en' and 'hospital_patient_name' in doc:
                                        if ref['hospital_patient_name'] == doc['hospital_patient_name']:
                                            doc_id = doc['doc_id']
                                            for r in ref['content']:
                                                ref_list.append(r)
                                            doc_ids.append(doc_id)
                                            break
                                        
                        doc_ids = list(set(doc_ids))   
                        
                        if language == 'zh':
                            jsonl_obj = {
                                "domain": domain.capitalize(),
                                "language": language,
                                "query": {
                                    "query_id": 0,
                                    "query_type": qa['问题类型'],
                                    "content": qa['问题'],
                                },
                                "ground_truth": {
                                    "doc_ids": doc_ids,
                                    "content": qa['答案'],
                                    "references": ref_list,
                                    "keypoints": ""
                                },
                                "prediction": {
                                    "content": "",
                                    "references": []
                                }
                            }
                        if language == 'en':
                            jsonl_obj = {
                                "domain": domain.capitalize(),
                                "language": language,
                                "query": {
                                    "query_id": 0,
                                    "query_type": qa['question type'],
                                    "content": qa['question'],
                                },
                                "ground_truth": {
                                    "doc_ids": doc_ids,
                                    "content": qa['answer'],
                                    "references": ref_list,
                                    "keypoints": ""
                                },
                                "prediction": {
                                    "content": "",
                                    "references": []
                                }
                            }
                        output.append(jsonl_obj)
                        doc_ids = []
    return output

def qa_format_irrelevant(
    domain: str,
    language: str,
    docs: List[Dict]
) -> List[Dict]:
    
    irrelevant_json_path = f'output/{domain}/{language}/qra_irrelevant.json'
    with open(irrelevant_json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    output = []
    for item in json_data:
        if language == 'zh':
            if domain == 'law':
                for doc in docs:
                    if 'court_name' in doc:
                        if doc['court_name'] == item['法院名']:
                            doc_id = doc['doc_id']
                            break
            if domain == 'medical':
                for doc in docs:
                    if 'hospital_patient_name' in doc:
                        if doc['hospital_patient_name'] == item['医院_病人名']:
                            doc_id = doc['doc_id']
                            break
            jsonl_obj = {
                "domain": domain.capitalize(),
                "language": language,
                "query": {
                    "query_id": 0,
                    "query_type": item['问题类型'],
                    "content": item['问题'],
                },
                "ground_truth": {
                    "doc_ids": [doc_id],
                    "content": item['答案'],
                    "references": item['ref'],
                    "keypoints": ""
                },
                "prediction": {
                    "content": "",
                    "references": []
                }
            }
            output.append(jsonl_obj)
        else:
            if domain == 'law':
                for doc in docs:
                    if 'court_name' in doc:
                        if doc['court_name'] == item['court_name']:
                            doc_id = doc['doc_id']
                            break
            if domain == 'medical':
                for doc in docs:
                    if 'hospital_patient_name' in doc:
                        if doc['hospital_patient_name'] == item['hospital_patient_name']:
                            doc_id = doc['doc_id']
                            break
            jsonl_obj = {
                "domain": domain.capitalize(),
                "language": language,
                "query": {
                    "query_id": 0,
                    "query_type": item['question type'],
                    "content": item['question'],
                },
                "ground_truth": {
                    "doc_ids": [doc_id],
                    "content": item['answer'],
                    "references": item['ref'],
                    "keypoints": ""
                },
                "prediction": {
                    "content": "",
                    "references": []
                }
            }
            output.append(jsonl_obj)
    return output
    
                                                 
def main():
    parser = argparse.ArgumentParser(description="corporate docs.")
    parser.add_argument("--domains", type=str, required=True, help="Comma-separated list of domains")
    parser.add_argument("--languages", type=str, required=True, help="Comma-separated list of languages")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for the JSONL file")

    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Split the comma-separated domains into a list
    domains = args.domains.split(',')
    languages = args.languages.split(',')
    
    jsonl_docs = read_jsonl_doc(
        doc_path='results/DRAGONBALL_docs.jsonl'
    )
    
    query_list = []
    for domain in domains:
        for language in languages:
            query_list.extend(
                qa_format_single_doc(
                    domain=domain,
                    language=language,
                    docs=jsonl_docs
                )
            )
            query_list.extend(
                qa_format_multi_doc(
                    domain=domain,
                    language=language,
                    docs=jsonl_docs
                )
            )
            if domain == 'law' or domain == 'medical':
                query_list.extend(
                    qa_format_irrelevant(
                        domain=domain,
                        language=language,
                        docs=jsonl_docs
                    )
                )
    i = 0
    for item in query_list:
        item['query']['query_id'] = i
        i += 1
    
    output_path = args.output_dir + '/DRAGONBALL_query.jsonl'
    with open(output_path, 'w') as f:
        for item in query_list:
            json_string = json.dumps(item, ensure_ascii=False)
            f.write(json_string + '\n')
    
if __name__ == '__main__':
    main()