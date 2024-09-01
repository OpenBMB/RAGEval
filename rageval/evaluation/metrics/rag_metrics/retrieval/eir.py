import numpy as np
import re
from typing import List
from pysbd import Segmenter
segmenter = Segmenter()

class EIR:
    name: str = "EIR"
    
    def __init__(self, threshold=0.2):
        self.threshold = threshold
    
    def count_words(self, text, language):
        """Count words considering the language."""
        if language == 'zh':
            # In Chinese, we consider each character as a word
            return len(text)
        else:
            # For other languages, we split by spaces
            return len(text.split())

    def calculate_eir(self, retrieves, ground_truths, language=None) -> float:
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

        # Combine retrieves into a single string
        combined_retrieves = ' '.join([retrieve[0] if isinstance(retrieve, list) else retrieve for retrieve in retrieves])

        # Get the word counts of ground truth references that are contained within combined_retrieves
        matched_word_count = 0
        for ground_truth in ground_truths:
            ground_truth_text = ground_truth[0] if isinstance(ground_truth, list) else ground_truth
            sentences = split_sentences(ground_truth_text, language)
            for sentence in sentences:
                if sentence in combined_retrieves:
                    matched_word_count += self.count_words(sentence, language)

        # Get the total word count of the retrieved content
        total_word_count = self.count_words(combined_retrieves, language)

        # Calculate the EIR value
        if matched_word_count == 0 or total_word_count == 0:
            return 0.0

        eir_value = matched_word_count / total_word_count
        return eir_value

    def __call__(self, doc, ground_truth, results, language=None) -> float:
        retrieves = [r for r in doc["prediction"].get("references", [])]  # Retrieves from prediction
        ground_truths = doc['ground_truth'].get('references', [])
        new_retrieves = []
        new_ground_truths = []

        for retrieve in retrieves:
            if isinstance(retrieve, list):
                retrieve = retrieve[0]
            # Check if the first character is '('
            if retrieve:
                if retrieve[0] == '（':
                    # delete the metadata part for calculating the EIR
                    # Find the position of the first ')'
                    print('Deleting Metadata in Chinese!!!!')
                    end_pos = retrieve.find('）')
                    # If ')' is found, remove the substring from '(' to ')'
                    if end_pos != -1:
                        retrieve = retrieve[end_pos + 1:]
                elif retrieve[0] == '(':
                    print('Deleting Metadata in english!!!!')
                    # delete the metadata part for calculating the EIR
                    # Find the position of the first ')'
                    end_pos = retrieve.find(')')
                    # If ')' is found, remove the substring from '(' to ')'
                    if end_pos != -1:
                        retrieve = retrieve[end_pos + 1:]
            new_retrieves.append(retrieve)

        for ground_truth in ground_truths:
            if isinstance(ground_truth, list):
                ground_truth = ground_truth[0]
            new_ground_truths.append(ground_truth)

        if not retrieves or not ground_truths:
            return 0.0

        return self.calculate_eir(new_retrieves, new_ground_truths, language=language)
