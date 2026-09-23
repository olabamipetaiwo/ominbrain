#!/usr/bin/env bash
# Run general-domain open models (Llama/Gemma family), all served via Ollama.
#
#   ollama pull gemma3:12b gemma3:27b llama4:scout
set -e
cd "$(dirname "$0")/.."

N_CASES=${N_CASES:-100}

for MODEL in "Gemma-3-12B" "Gemma-3-27B" "Llama-4-Scout"; do
    echo ""
    echo "=========================================="
    echo " Starting: $MODEL"
    echo "=========================================="
    python3 run_omnibrain.py --model "$MODEL" --n-cases "$N_CASES" "$@"
done
