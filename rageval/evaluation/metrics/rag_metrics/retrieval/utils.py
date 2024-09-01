from typing import List
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

def exist_match(ground_truth: List[str], retrieves: List[str], language="zh") -> int:
    # Split the ground_truth into sentences
    if type(ground_truth) == list:
        ground_truth = " ".join(ground_truth)
    sentences = split_sentences(ground_truth, language)
    
    # Check if all sentence is in the retrieves list
    for sentence in sentences:
        match = False
        for retrieve in retrieves:
            if sentence in retrieve:
                match = True
                break
        if not match:
            return 0
    
    return 1
