#!/usr/bin/env bash
# Run medical-domain models. MedGemma-4B is served via Ollama; HuatuoGPT-V-34B,
# Lingshu-32B, and Llava-Med-7B need vLLM servers running first (see
# config/models.py for the `vllm serve` commands and ports).
#
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
