#!/usr/bin/env bash
# Run medical-domain models via Ollama.
#
# Pull models first (one-time):
#   ollama pull huatuogpt-vision:34b
#   ollama pull lingshu:32b
#   ollama pull llava-med:7b
#   ollama pull medgemma:4b
set -e
cd "$(dirname "$0")/.."

N_CASES=${N_CASES:-100}

for MODEL in "HuatuoGPT-V-34B" "Lingshu-32B" "Llava-Med-7B" "MedGemma-4B"; do
    echo ""
    echo "=========================================="
    echo " Starting: $MODEL"
    echo "=========================================="
    python3 run_omnibrain.py --model "$MODEL" --n-cases "$N_CASES" "$@"
done
