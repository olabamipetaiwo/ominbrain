# 7 models for the causal chain benchmark: 4 open-weight (PRIMARY) + 3 API (OPTIONAL).
# (Deepseek-V3.1 and Janus-Pro-7B dropped — DeepSeek is not permitted on HiPerGator,
#  as an API provider or as an upstream model source.)
# (2026-09-21: professor's constraint — all China-developed models removed:
#  HuatuoGPT-V-34B, Lingshu-32B, Qwen3-VL-30B, InternVL3-38B, Qwen2.5-VL-7B.
#  Professor approved Llama/Gemma-family replacements, added below as "general" open models.)
#
# (2026-09-21: professor — "we can try with the open-weight models". Open-weight models are
#  the primary roster (MODELS, what --all-models runs). API models live in API_MODELS: still
#  selectable by name (--model GPT-5) and listed by --list-models, but NOT in --all-models,
#  so no API spend happens unless asked for explicitly.)
#
# Categories:
#   Medical       — MedGemma-4B
#   General open  — Gemma-3-12B, Gemma-3-27B, Llama-4-Scout (Ollama, default Q4 quant)
#   Proprietary   — Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet (optional, API_MODELS)
#
# (2026-09-21: Llama-3.2-Vision-11B dropped — Ollama 0.33.0, required for the RTX PRO 6000, cannot
#  load the 'mllama' architecture; replaced by Llama-4-Scout, same family.)
#
# Hardware: open-weight jobs run on hpg-rtx6000 (RTX PRO 6000, 96GB) — see
# shell/lumiere/lumiere_prelim_ollama.sbatch.
#
# Backends
#
# "openai"   Direct OpenAI API (base_url=None)
#            Requires: OPENAI_API_KEY
#
# "litellm"  LiteLLM proxy — OpenAI-compatible wrapper for other providers
#            Requires proxy running + provider API key in environment:
#              litellm --model claude-sonnet-4-5        --port 8001  (ANTHROPIC_API_KEY)
#              litellm --model gemini/gemini-2.5-pro    --port 8002  (GOOGLE_API_KEY)
#
# "ollama"   Small/medium open-weight models via Ollama (ollama pull <model>)
#            Best for: MedGemma-4B, Gemma-3, Llama-4-Scout
#

import os

API_MODELS = [  # optional — not run by --all-models
    {
        "name": "Gemini-3.6-Flash",
        "model": "gemini-3.6-flash",  # control model. gemini-2.5-pro: 404 (not available to new users); gemini-3.1-pro-preview: 429, free-tier quota 0 (2026-09-25)
        # Google's OpenAI-compatible endpoint, no LiteLLM proxy (2026-09-25; key in .env as GEMINI_API_KEY)
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "max_tokens": 16384,  # Gemini's hidden thinking tokens count against the cap; 800 would truncate
        "category": "proprietary",
    },
    {   # precision control (2026-09-25): Google's bf16 release of the model that runs at 4-bit in Ollama as Gemma-3-27B,
        # served by vLLM (shell/lumiere/lumiere_v4_bf16.sbatch). Not part of the registered four; see the preregistration change log.
        "name": "Gemma-3-27B-bf16",
        "model": "google/gemma-3-27b-it",
        "base_url": os.environ.get("VLLM_BASE_URL", "http://localhost:8127/v1"),
        "api_key": "local",
        "category": "precision-control",
        "backend": "vllm",
    },
    {
        "name": "GPT-5",
        "model": "gpt-5",
        "base_url": None,  # OpenAI API directly
        "api_key": None,  # reads OPENAI_API_KEY
        "category": "proprietary",
    },
    {
        "name": "Claude-4.5-Sonnet",
        "model": "claude-sonnet-4-5",
        "base_url": "http://localhost:8001/v1",
        "api_key": "local",  # LiteLLM reads ANTHROPIC_API_KEY
        "category": "proprietary",
    },
]

_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")  # per-job port override

MODELS = [  # primary open-weight roster
    # Medical-domain
    # (Llava-Med-7B removed 2026-09-21: cannot produce the required JSON output — see
    #  paper/update.md 2026-09-07 entry for the documented finding.)
    # Official Google build on Ollama: medgemma:4b (vision-capable)
    {
        "name": "MedGemma-4B",
        "model": "medgemma:4b",
        "base_url": _OLLAMA_URL,
        "api_key": "local",
        "category": "medical",
        "backend": "ollama",
    },
    # General-domain open models (Ollama official builds, default Q4 quantization —
    # note in methods; the vision-capable tags are gemma3:* and llama4:scout).
    {
        "name": "Gemma-3-12B",
        "model": "gemma3:12b",
        "base_url": _OLLAMA_URL,
        "api_key": "local",
        "category": "general",
        "backend": "ollama",
    },
    {
        "name": "Gemma-3-27B",
        "model": "gemma3:27b",
        "base_url": _OLLAMA_URL,
        "api_key": "local",
        "category": "general",
        "backend": "ollama",
    },
    {
        "name": "Llama-4-Scout",
        "model": "llama4:scout",
        "base_url": _OLLAMA_URL,
        "api_key": "local",
        "category": "general",
        "backend": "ollama",
    },
]

# Lookup by name
ALL_MODELS = MODELS + API_MODELS
MODEL_MAP = {m["name"]: m for m in ALL_MODELS}
