from typing import List, Union
import re
from nltk.tokenize import sent_tokenize
from pysbd import Segmenter

segmenter = Segmenter()

def split_sentences(text: str, language: str) -> List[str]:
    if language == 'en':
        sentences = segmenter.segment(text)
        
    elif language == 'zh':
        # Split by Chinese punctuation or newlines
        sentences = re.split(r'(?<=[。！？])\s*|\n', text)
    else:
        raise ValueError("Unsupported language")
    
    # 去掉空白的句子
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences

def exist_match(query_text: Union[List[str], str], reference_texts: List[str], language="zh") -> int:
    # Split the ground_truth into sentences
    if type(query_text) == list:
        query_text = " ".join(query_text)
    q_sentences = split_sentences(query_text, language)
    
    # Check if all sentence from the query is in the reference list
    for q in q_sentences:
        match = False
        for r in reference_texts:
            if q in r:
                match = True
                break
        if not match:
            return 0
    
    return 1
