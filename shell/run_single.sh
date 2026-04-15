#!/usr/bin/env bash
# Run evaluation for a single model.
#
# Usage:
#   bash shell/run_single.sh GPT-5
#   bash shell/run_single.sh Gemini-2.5-Pro --n-cases 200
#   bash shell/run_single.sh GPT-5 --no-gating         # flat accuracy baseline
#   bash shell/run_single.sh GPT-5 --n-cases 5         # smoke test (5 cases)
#
# API keys are read from environment variables:
#   OPENAI_API_KEY       — GPT-5
#   ANTHROPIC_API_KEY    — Claude-4.5-Sonnet  (via LiteLLM proxy on :8001)
#   GOOGLE_API_KEY       — Gemini-2.5-Pro     (via LiteLLM proxy on :8002)
#   DEEPSEEK_API_KEY     — Deepseek-V3.1      (via LiteLLM proxy on :8003)
set -e
cd "$(dirname "$0")/.."

MODEL=${1:?"Usage: bash shell/run_single.sh <model-name> [extra args]"}
shift

python3 run_omnibrain.py --model "$MODEL" "$@"
