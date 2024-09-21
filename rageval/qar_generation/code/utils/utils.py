import sys
import json
import logging
from typing import List, Dict

def read_prompt(file_path: str = 'prompts/finance_zh.jsonl') -> List[Dict]:
    """Read prompts from a JSONL file."""
    prompts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                prompts.append(json.loads(line))
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        sys.exit(1)
    return prompts

def read_config_json(json_path: str) -> Dict:
    """Read a JSON configuration file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError as e:
        logging.error(f'JSON Decode Error: {e} in {json_path}')
        sys.exit(1)
    except FileNotFoundError:
        logging.error(f"File not found: {json_path}")
        sys.exit(1)
    return config

def write_config_json(json_path: str, config: Dict) -> None:
    """Write configuration data to a JSON file."""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
