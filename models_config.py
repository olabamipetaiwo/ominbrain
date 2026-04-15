# 12 models selected for the causal chain benchmark.
#
# Grouped into 3 categories × 4 models each:
#   Proprietary   — Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet, Deepseek-V3.1
#   Medical       — HuatuoGPT-V-34B, Lingshu-32B, Llava-Med-7B, MedGemma-4B
#   Open-source   — Qwen3-VL-30B, InternVL3-38B, Qwen3-VL-8B, Janus-Pro-7B
#
# ── Backends ──────────────────────────────────────────────────────────────────
#
# "openai"   Direct OpenAI API (base_url=None)
#            Requires: OPENAI_API_KEY
#
# "litellm"  LiteLLM proxy — OpenAI-compatible wrapper for other providers
#            Requires proxy running + provider API key in environment:
#              litellm --model claude-sonnet-4-5        --port 8001  (ANTHROPIC_API_KEY)
#              litellm --model gemini/gemini-2.5-pro    --port 8002  (GOOGLE_API_KEY)
#              litellm --model deepseek/deepseek-chat   --port 8003  (DEEPSEEK_API_KEY)
#
# "ollama"   Small/medium open-weight models via Ollama (ollama pull <model>)
#            Best for: Qwen3-VL-8B, Janus-Pro-7B, Llava-Med-7B, MedGemma-4B
#
# "vllm"     Large open-weight vision models — requires vLLM server running
#            Best for: Qwen3-VL-30B, InternVL3-38B, HuatuoGPT-V-34B, Lingshu-32B
#            Start server:
#              vllm serve Qwen/Qwen3-VL-30B-Instruct         --port 8010 --tensor-parallel-size 2
#              vllm serve OpenGVLab/InternVL3-38B             --port 8011 --tensor-parallel-size 2
#              vllm serve FreedomIntelligence/HuatuoGPT-Vision-34B  --port 8012
#              vllm serve DUTIR-BioNLP/Lingshu-32B            --port 8013
#            vLLM serves an OpenAI-compatible API — same client, different base_url.

MODELS = [

    # ── Proprietary ────────────────────────────────────────────────────
    {
        "name":     "Gemini-2.5-Pro",
        "model":    "gemini/gemini-2.5-pro",
        "base_url": "http://localhost:8002/v1",
        "api_key":  "local",               # LiteLLM reads GOOGLE_API_KEY
        "category": "proprietary",
    },
    {
        "name":     "GPT-5",
        "model":    "gpt-5",
        "base_url": None,                  # OpenAI API directly
        "api_key":  None,                  # reads OPENAI_API_KEY
        "category": "proprietary",
    },
    {
        "name":     "Claude-4.5-Sonnet",
        "model":    "claude-sonnet-4-5",
        "base_url": "http://localhost:8001/v1",
        "api_key":  "local",               # LiteLLM reads ANTHROPIC_API_KEY
        "category": "proprietary",
    },
    {
        "name":     "Deepseek-V3.1",
        "model":    "deepseek-chat",
        "base_url": "http://localhost:8003/v1",
        "api_key":  "local",               # LiteLLM reads DEEPSEEK_API_KEY
        "category": "proprietary",
    },

    # ── Medical-domain ─────────────────────────────────────────────────
    # HF: FreedomIntelligence/HuatuoGPT-Vision-34B  — needs vLLM (34B)
    {
        "name":     "HuatuoGPT-V-34B",
        "model":    "FreedomIntelligence/HuatuoGPT-Vision-34B",
        "base_url": "http://localhost:8012/v1",
        "api_key":  "local",
        "category": "medical",
        "backend":  "vllm",
    },
    # HF: DUTIR-BioNLP/Lingshu-32B  — needs vLLM (32B)
    {
        "name":     "Lingshu-32B",
        "model":    "DUTIR-BioNLP/Lingshu-32B",
        "base_url": "http://localhost:8013/v1",
        "api_key":  "local",
        "category": "medical",
        "backend":  "vllm",
    },
    # HF: microsoft/llava-med-v1.5-mistral-7b  — Ollama ok (7B)
    {
        "name":     "Llava-Med-7B",
        "model":    "llava-med:7b",
        "base_url": "http://localhost:11434/v1",
        "api_key":  "local",
        "category": "medical",
        "backend":  "ollama",
    },
    # HF: google/medgemma-4b-it  — Ollama ok (4B)
    {
        "name":     "MedGemma-4B",
        "model":    "medgemma:4b",
        "base_url": "http://localhost:11434/v1",
        "api_key":  "local",
        "category": "medical",
        "backend":  "ollama",
    },

    # ── Open-source ────────────────────────────────────────────────────
    # HF: Qwen/Qwen3-VL-30B-Instruct  — needs vLLM (30B)
    {
        "name":     "Qwen3-VL-30B",
        "model":    "Qwen/Qwen3-VL-30B-Instruct",
        "base_url": "http://localhost:8010/v1",
        "api_key":  "local",
        "category": "open-source",
        "backend":  "vllm",
    },
    # HF: OpenGVLab/InternVL3-38B  — needs vLLM (38B)
    {
        "name":     "InternVL3-38B",
        "model":    "OpenGVLab/InternVL3-38B",
        "base_url": "http://localhost:8011/v1",
        "api_key":  "local",
        "category": "open-source",
        "backend":  "vllm",
    },
    # HF: Qwen/Qwen3-VL-8B-Instruct  — Ollama ok (8B, within-family size comparison)
    {
        "name":     "Qwen3-VL-8B",
        "model":    "qwen3-vl:8b",
        "base_url": "http://localhost:11434/v1",
        "api_key":  "local",
        "category": "open-source",
        "backend":  "ollama",
    },
    # HF: deepseek-ai/Janus-Pro-7B  — Ollama ok (7B)
    {
        "name":     "Janus-Pro-7B",
        "model":    "janus-pro:7b",
        "base_url": "http://localhost:11434/v1",
        "api_key":  "local",
        "category": "open-source",
        "backend":  "ollama",
    },
]

# Lookup by name
MODEL_MAP = {m["name"]: m for m in MODELS}
