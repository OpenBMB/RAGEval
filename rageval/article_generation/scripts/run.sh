#!/bin/bash

# set the parameters
language=$1 # en or zh
domain=$2 # domain name, currently support: finance, law, medical

# 检查参数是否为空
if [ -z "$language" ] || [ -z "$domain" ]; then
  echo "Usage: $0 <language> <domain>"
  exit 1
fi

# create the script path
script_path="./scripts/$domain/$language/run_all.sh"

echo "Running script: $script_path"
bash $script_path
