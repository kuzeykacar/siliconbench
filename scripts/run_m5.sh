#!/usr/bin/env bash
# The models I compare on a MacBook Pro M5 with 16 GB. Needs Ollama installed and running (https://ollama.com).
set -euo pipefail
cd "$(dirname "$0")/.."
MODELS=(qwen2.5:3b qwen2.5:7b llama3.2:3b gemma3:4b phi4-mini qwen2.5:7b-instruct-q8_0)
for m in "${MODELS[@]}"; do ollama pull "$m"; done
python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements.txt
python -m siliconbench run --models "${MODELS[@]}" --n 12 --out results/m5-16gb
