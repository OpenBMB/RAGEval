import numpy as np

class SNR:
    name: str = "SNR"
    
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

    def calculate_snr(self, retrieves, ground_truths, language=None) -> float:
        # Get the word counts of ground truth references that are contained within retrieves
        matched_word_count = 0
        for ground_truth in ground_truths:
            for retrieve in retrieves:
                if type(retrieve) == list:
                    retrieve = retrieve[0]
                if type(ground_truth) == list:
                    ground_truth = ground_truth[0]
                if ground_truth.strip() in retrieve.strip():
                    matched_word_count += self.count_words(ground_truth, language)
                    break

        # Get the total word count of the retrieved content
        total_word_count = sum(self.count_words(retrieve, language) for retrieve in retrieves)
        # Calculate the SNR value
        if matched_word_count == 0 or total_word_count - matched_word_count == 0:
            return 0.0

        snr_value = 10 * np.log10(matched_word_count / (total_word_count - matched_word_count))
        return snr_value

    def __call__(self, doc, ground_truth, results, language=None) -> float:
        retrieves = [r for r in doc["prediction"].get("references", [])]  # Retrieves from prediction
        ground_truths = [g['content'] for g in doc['ground_truth'].get('references', [])]
        new_retrieves = []
        new_ground_truths = []
        for retrieve in retrieves:
            if type(retrieve) == list:
                new_retrieves.append(retrieve[0])
            else:
                new_retrieves.append(retrieve)
        for ground_truth in ground_truths:
            if type(ground_truth) == list:
                new_ground_truths.append(ground_truth[0])
            else:
                new_ground_truths.append(ground_truth)

        if not retrieves or not ground_truths:
            return 0.0

        return self.calculate_snr(retrieves, ground_truths, language=language)