import os
import json
import argparse
from typing import List

def doc_corporation(domains: List, languages: List, output_dir: str) -> None:
    output_list = []
    doc_id = 0
    for domain in domains:
        for language in languages:
            domain_dir = f'output/{domain}/{language}'
            for root, dirs, files in os.walk(domain_dir):
                for file in files:
                    if file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            jsonl_obj = {
                                "domain": domain.capitalize(),
                                "language": language,
                                "doc_id": doc_id,
                                "content": content
                            }
                            output_list.append(jsonl_obj)
                            doc_id += 1
    new_file_name = 'DRAGONBALL_docs.jsonl'
    with open(os.path.join(output_dir, new_file_name), 'w', encoding='utf-8') as f:
        for item in output_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="corporate docs.")
    parser.add_argument("--domains", type=str, required=True, help="Comma-separated list of domains")
    parser.add_argument("--languages", type=str, required=True, help="Comma-separated list of languages")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for the JSONL file")

    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Split the comma-separated domains and languages into a list
    domains = args.domains.split(',')
    languages = args.languages.split(',')

    doc_corporation(
        domains=domains, 
        languages=languages,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()