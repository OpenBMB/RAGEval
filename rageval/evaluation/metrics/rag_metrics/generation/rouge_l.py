from rouge import Rouge
import numpy as np
import rouge_chinese
import jieba # you can use any other word cutting library

class ROUGELScore:
    name:str = "ROUGELScore"
    def __init__(self, language="zh"):
        self.rouge = Rouge(metrics=["rouge-l"])
        self.language = language

    def __call__(self, doc, ground_truth, results, language="zh") -> dict:
        hypothesis = doc["prediction"]["content"]
        reference = doc["ground_truth"]["content"]
        if language == "zh":
            hypothesis = ' '.join(jieba.cut(hypothesis))
            reference = ' '.join(jieba.cut(reference))
            if hypothesis=='' or reference=='':
                return 0.0
            score = self._calculate_rouge_l_score_chinese(hypothesis, reference)
            return score
        if hypothesis=='' or reference=='':
            return 0.0
        return self._calculate_rouge_l_score(hypothesis, reference)

    def _calculate_rouge_l_score(self, hypothesis, reference) -> float:
        scores = self.rouge.get_scores(hypothesis, reference)
        return scores[0]["rouge-l"]['f']
    
    def _calculate_rouge_l_score_chinese(self, hypothesis, reference) -> float:
        rouge = rouge_chinese.Rouge()
        try:
            scores = rouge.get_scores(hypothesis, reference)
        except ValueError:
            print("ValueError: hypothesis or reference")
            return 0.0
        return scores[0]["rouge-l"]['f']

