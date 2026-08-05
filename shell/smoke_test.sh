#!/usr/bin/env bash
# Quick smoke test — 5 cases on a single model to verify the pipeline end-to-end.
# Default model: Qwen2.5-VL-7B. Override with: bash shell/smoke_test.sh GPT-5
set -e
cd "$(dirname "$0")/.."

# Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

MODEL=${1:-"Qwen2.5-VL-7B"}

# Run all available multi-phase cases (10 total in dataset).
# --max-q-per-phase 3 keeps each run manageable (~150 API calls total).
echo "Smoke test: $MODEL — all multi-phase cases, 3 Qs/phase"
python3 run_omnibrain.py --model "$MODEL" --max-q-per-phase 3
