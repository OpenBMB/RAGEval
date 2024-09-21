<h1 align="center">RAGEval: Scenario Specific RAG Evaluation Dataset Generation Framework</h1>
<div align="center">

[![Python 3.10](https://img.shields.io/badge/python-%E2%89%A53.10-blue)](https://www.python.org/downloads/release/python-3109/)
[![Arxiv](https://img.shields.io/badge/arXiv-2408.01262-red)](https://arxiv.org/pdf/2408.01262)

</div>

<div style="display: flex; justify-content: center;">
  <div style="width: 50%; transform: scale(1.0);">
    <img src="assets/dragonball.png" style="width: 100%;" alt="dragonball">
  </div>
</div>


## Introduction

RAGEval is a novel framework designed for automatically generating evaluation datasets to assess the knowledge usage ability of different Large Language Models (LLMs) in various Retrieval-Augmented Generation (RAG) scenarios. Unlike existing RAG benchmarks that focus on general knowledge, RAGEval enables the creation of domain-specific factual queries, allowing for a more nuanced evaluation of RAG systems across different vertical domains.

## News
- **[2024/9/21]** We have released our article generation pipeline and 'query-answer-reference' generation pipeline
- **[2024/8/31]** We have released our evaluation method at the ``rageval/evaluation`` folder.
- **[2024/8/25]** We have released our DragonBall dataset at the ``dragonball_dataset`` folder. The RAGEval pipeline is coming soon!

## Key Features

1. 🏗️ **Flexible Schema Generation**: Summarizes a schema from seed documents to capture domain-specific knowledge structures.

2. 🔄 **Diverse Document Generation**: Uses the schema to generate varied configurations and subsequently diverse documents across multiple domains.

3. ❓ **Comprehensive QA Pair Creation**: Constructs question-answering pairs based on generated documents and configurations.

4. 📊 **Novel Evaluation Metrics**: Introduces three new metrics - Completeness, Hallucination, and Irrelevance - for a more thorough assessment of RAG model responses.

5. 🌐 **Multi-Domain Support**: Covers various domains including finance, legal, and medical sectors in both Chinese and English languages.

## Components

1. **Schema Summary**: Extracts domain-specific knowledge structures from seed documents.
2. **Document Generation**: Creates diverse, factually rich documents based on the schema.
3. **QRA (Question-Reference-Answer) Generation**: Produces comprehensive evaluation triples.
4. **DRAGONBall Dataset**: A diverse RAG benchmark covering multiple domains and languages.
5. **Evaluation Metrics**: Novel metrics for assessing RAG system performance.


## Usage

- For Evaluation, please refer to [evaluation](https://github.com/OpenBMB/RAGEval/tree/main/rageval/evaluation)
- For Article Generation, please refer to [article_generation](https://github.com/OpenBMB/RAGEval/tree/main/rageval/article_generation)
- For QAR Generation, please refer to [QAR_generation](https://github.com/OpenBMB/RAGEval/tree/main/rageval/qar_generation)

## Experiments

RAGEval has been used to benchmark various LLMs and RAG configurations:

- Compared performance of 9 popular open/closed-source generation models
- Evaluated different retrieval models (BM25, GTE-Large, BGE-Large, BGE-M3)
- Analyzed impact of hyperparameters like TopK retrieval and chunk size

## Results

- GPT-4o showed the best overall performance, but open-source models like Llama3-8B-Instruct demonstrated competitive results.
- Language-specific optimization in retrieval models proved crucial for performance.
- Hyperparameter tuning revealed important trade-offs between retrieval accuracy and generation quality.

## Conclusion

RAGEval provides a comprehensive framework for evaluating RAG systems in domain-specific scenarios, offering more nuanced insights than existing benchmarks. It highlights the potential for significant improvements in open-source models for RAG tasks.


## Citation
Please cite the following paper if you find RAGEval helpful!
```bibtex
@misc{zhu2024ragevalscenariospecificrag,
      title={RAGEval: Scenario Specific RAG Evaluation Dataset Generation Framework}, 
      author={Kunlun Zhu and Yifan Luo and Dingling Xu and Ruobing Wang and Shi Yu and Shuo Wang and Yukun Yan and Zhenghao Liu and Xu Han and Zhiyuan Liu and Maosong Sun},
      year={2024},
      eprint={2408.01262},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2408.01262}, 
}
```

<p align="center">
<a href="https://star-history.com/#Significant-Gravitas/AutoGPT">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=openbmb/rageval&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=openbmb/rageval&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Significant-Gravitas/AutoGPT&type=Date" />
  </picture>
</a>
</p>
