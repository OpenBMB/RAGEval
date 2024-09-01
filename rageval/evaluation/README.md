# RAG Evaluation Piepline

This tool is designed to evaluate RAG (Retrieval-Augmented Generation) systems by processing JSONL files and calculating various metrics. Note that this is not a replicate for the paper experiment results though you could do that by yourself, this is the pipeline you can use to evaluate your own RAG system or dataset result.

## Setup and Usage

### 1. Navigate to the Evaluation Folder

Change your current directory to the `evaluation` folder by running the command:

```bash
cd rageval/evaluation
```

### 2. Install Dependencies

Before running the evaluation, make sure to install all required dependencies:

```bash
pip install -r requirements.txt
```


### 3. Prepare Input Data

Place your JSONL files for evaluation in the `data` folder. A sample file is provided for reference.

### 4. Bash Script Parameters

The `run_evaluation.sh` script accepts several parameters:

- `NUM_WORKERS`: Number of workers for parallel processing (default: 20)
- `LANGUAGE`: Language of the input data (default: "en")
- `INPUT_BASE_URL`: Path to the input data folder (default: "./data/")
- `OUTPUT_BASE_URL`: Path for intermediate results (default: "./result/intermediate_result/")
- `METRICS`: List of metrics to evaluate (default: "rouge-l precision recall eir keypoint_metrics")

**Important Note on Metrics:**
If you want to calculate completeness, irrelevance, and hallucination metrics, you must include `keypoint_metrics` in the `METRICS` list. However, please be aware that these metrics require the use of an OpenAI API key. **The cost of using these metrics can be substantial, so please consider the expense before enabling them.**

### 5. Run the Evaluation

To start the evaluation process, use the following command:

```bash
bash run_evaluation.sh
```

### 6. Intermediate Results

Intermediate results will be saved in the `./result/intermediate_result/` directory. Each metric will have its own output file.

### 7. Final Results

The final aggregated results can be found in the `result/final_result.json` file. This JSON file contains the average scores for each metric across all evaluated files.

## Note

Ensure that you have the necessary permissions to read from the `data` folder and write to the `result` folder. If you encounter any issues, check the file permissions and the paths specified in the script.