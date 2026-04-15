#!/usr/bin/env bash
# Run open-source models via Ollama.
#
# Pull models first (one-time):
#   ollama pull qwen3-vl:30b
#   ollama pull internvl3:38b
#   ollama pull qwen3-vl:8b
#   ollama pull janus-pro:7b
set -e
cd "$(dirname "$0")/.."

N_CASES=${N_CASES:-100}

for MODEL in "Qwen3-VL-30B" "InternVL3-38B" "Qwen3-VL-8B" "Janus-Pro-7B"; do
    echo ""
    echo "=========================================="
    echo " Starting: $MODEL"
    echo "=========================================="
    python3 run_omnibrain.py --model "$MODEL" --n-cases "$N_CASES" "$@"
done
