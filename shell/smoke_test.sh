#!/usr/bin/env bash
# Quick smoke test — 5 cases on a single model to verify the pipeline end-to-end.
# Default model: GPT-5. Override with: bash shell/smoke_test.sh Gemini-2.5-Pro
set -e
cd "$(dirname "$0")/.."

MODEL=${1:-"GPT-5"}

echo "Smoke test: $MODEL — 5 cases"
python3 run_omnibrain.py --model "$MODEL" --n-cases 5
