# RAG Document Generation Pipeline

This pipeline is designed to generate Documents based on configuration files. It supports multiple domains and languages, providing scripts for specific domain handling.

## Setup and Usage

### 1. Navigate to the `article_generation` Folder

Change your current directory to the `artical_generation` folder by running:

```bash
cd rageval/artical_generation
```

### 2. Set `OPENAI_API_KEY` and install openai package

Ensure that your `OPENAI_API_KEY` is correctly set. Mayby you can use `export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxx...`

### 3. Setup required Environment

Use the command `pip install -r requirements.txt' to install the required packages.

### 4. Prepare Input Schema

Place the schema files in the `output/$DOMAIN/$LANGUAGE/schema` folder.

### 5. Document Generation

The `scripts` directory contains scripts for generating documents across different domains. To generate documents, configure the parameters in `$DOMAIN/$LANGUAGE/config.sh`:

- **`json_idx`**: The OpenAI model name to use (default: `"gpt-4o"`)
- **`event_num`**: Path to the input data folder (example: `"data/law/en/config"`)
- **`schema_dir`**: Path to the output data folder (example: `"output/law/en/config"`)
- **`config_output_dir`**: Index of each domain (default: `0`)
- **`doc_output_dir`**: Index of each domain (default: `0`)

To specify the **OpenAI model** for generation, you can set **`model_name`** in each shell script.

### 6. Run `run.sh`

The `scripts` directory contains a shell script named `run.sh`, it receives 2 arguments: `language` and `domain`.

```bash
#!/bin/bash

language=$1
domain=$2

if [ -z "$language" ] || [ -z "$domain" ]; then
  echo "Usage: $0 <language> <domain>"
  exit 1
fi

script_path="./scripts/$domain/$language/run_all.sh"

echo "Running script: $script_path"
bash $script_path
```

You can run the script like `bash scipts/run.sh zh finance`. Make sure you are running under the 'article_generation' folder