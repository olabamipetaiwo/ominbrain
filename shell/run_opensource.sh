#!/usr/bin/env bash
# Run open-source models. Qwen2.5-VL-7B is served via Ollama; Qwen3-VL-30B and
# InternVL3-38B need vLLM servers running first (see config/models.py for the
# `vllm serve` commands and ports).
#
#   ollama pull qwen2.5vl:7b
set -e
cd "$(dirname "$0")/.."

N_CASES=${N_CASES:-100}

for MODEL in "Qwen3-VL-30B" "InternVL3-38B" "Qwen2.5-VL-7B"; do
    echo ""
    echo "=========================================="
    echo " Starting: $MODEL"
    echo "=========================================="
    python3 run_omnibrain.py --model "$MODEL" --n-cases "$N_CASES" "$@"
done
