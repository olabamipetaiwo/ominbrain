#!/usr/bin/env bash
# Run medical-domain models. MedGemma-4B is served via Ollama.
#
#   ollama pull medgemma:4b
set -e
cd "$(dirname "$0")/.."

N_CASES=${N_CASES:-100}

for MODEL in "MedGemma-4B"; do
    echo ""
    echo "=========================================="
    echo " Starting: $MODEL"
    echo "=========================================="
    python3 run_omnibrain.py --model "$MODEL" --n-cases "$N_CASES" "$@"
done
