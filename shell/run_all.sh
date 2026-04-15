#!/usr/bin/env bash
# Run the full benchmark — all 12 models sequentially.
#
# Usage:
#   bash shell/run_all.sh                     # 100 cases per model (default)
#   bash shell/run_all.sh --n-cases 200       # larger run
#   bash shell/run_all.sh --no-gating         # flat accuracy baseline
#
# Results land in omnibrain/results/<ModelName>_<timestamp>/
#   raw_results.json    — full per-question outputs
#   report.txt          — chain eval summary
#   total_results.json  — OmniBrainBench-compatible format
#
# Estimated runtime (100 cases):
#   Proprietary API models  ~2–4 hrs total
#   Local models (Ollama)   ~4–8 hrs each depending on hardware
set -e
cd "$(dirname "$0")/.."

python3 run_omnibrain.py --all-models "$@"
