from .rag_metrics.retrieval.precision import Precision
from .rag_metrics.retrieval.recall import Recall
from .rag_metrics.generation.rouge_l import ROUGELScore
from .rag_metrics.retrieval.eir import EIR
from .rag_metrics.generation.keypoint_metrics import KEYPOINT_METRICS

METRICS_REGISTRY = {
    "rouge-l": ROUGELScore,
    "precision": Precision,
    "recall": Recall,
    "eir": EIR,
    "keypoint_metrics": KEYPOINT_METRICS,
}


def get_metric(metric_name):
    return METRICS_REGISTRY[metric_name]
