#!/usr/bin/env bash
# Run proprietary API models only.
# Requires API keys in environment (see run_single.sh for key names).
# LiteLLM proxies must be running for Claude, Gemini, and DeepSeek.
#
# Start proxies first:
#   litellm --model claude-sonnet-4-5        --port 8001 &
#   litellm --model gemini/gemini-2.5-pro    --port 8002 &
#   litellm --model deepseek/deepseek-chat   --port 8003 &
set -e
cd "$(dirname "$0")/.."

N_CASES=${N_CASES:-100}

for MODEL in "Gemini-2.5-Pro" "GPT-5" "Claude-4.5-Sonnet" "Deepseek-V3.1"; do
    echo ""
    echo "=========================================="
    echo " Starting: $MODEL"
    echo "=========================================="
    python3 run_omnibrain.py --model "$MODEL" --n-cases "$N_CASES" "$@"
done
