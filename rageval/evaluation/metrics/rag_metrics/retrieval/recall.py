from .utils import exist_match

class Recall:
    name:str = "Recall"
    def __init__(self):
        pass

    def calculate_recall(self, retrieves, ground_truths, language=None) -> float:
        match_count = sum(
            exist_match(ground_truth, retrieves, language=language)
            for ground_truth in ground_truths
        )
        return  match_count / len(ground_truths) if ground_truths else 0

    def __call__(self, doc, ground_truth, results, language) -> float:
        retrieves = [r for r in doc["prediction"].get("references", [])]  # Retrieves from prediction
        ground_truths =doc['ground_truth'].get('references', [])
        return self.calculate_recall(retrieves, ground_truths, language=language)