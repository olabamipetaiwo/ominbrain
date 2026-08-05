# 12 models selected for the causal chain benchmark.
#
# Grouped into 3 categories × 4 models each:
#   Proprietary   — Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet, Deepseek-V3.1
#   Medical       — HuatuoGPT-V-34B, Lingshu-32B, Llava-Med-7B, MedGemma-4B
#   Open-source   — Qwen3-VL-30B, InternVL3-38B, Qwen2.5-VL-7B, Janus-Pro-7B
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
#              litellm --model deepseek/deepseek-chat   --port 8003  (DEEPSEEK_API_KEY)
#
# "ollama"   Small/medium open-weight models via Ollama (ollama pull <model>)
#            Best for: Qwen3-VL-8B, Janus-Pro-7B, Llava-Med-7B, MedGemma-4B
#
# "vllm"     Large open-weight vision models — requires vLLM server running
#            Best for: Qwen3-VL-30B, InternVL3-38B, HuatuoGPT-V-34B, Lingshu-32B
#            Start server:
#              vllm serve Qwen/Qwen3-VL-30B-Instruct                    --port 8010 --tensor-parallel-size 2
#              vllm serve OpenGVLab/InternVL3-38B                        --port 8011 --tensor-parallel-size 2
#              vllm serve FreedomIntelligence/HuatuoGPT-Vision-34B       --port 8012
#              vllm serve DUTIR-BioNLP/Lingshu-32B                       --port 8013
#              vllm serve microsoft/llava-med-v1.5-mistral-7b            --port 8014
#              vllm serve deepseek-ai/Janus-Pro-7B                       --port 8015
#            vLLM serves an OpenAI-compatible API — same client, different base_url.

MODELS = [
    # Proprietary
    {
        "name": "Gemini-2.5-Pro",
        "model": "gemini/gemini-2.5-pro",
        "base_url": "http://localhost:8002/v1",
        "api_key": "local",  # LiteLLM reads GOOGLE_API_KEY
        "category": "proprietary",
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
    {
        "name": "Deepseek-V3.1",
        "model": "deepseek-chat",
        "base_url": "http://localhost:8003/v1",
        "api_key": "local",  # LiteLLM reads DEEPSEEK_API_KEY
        "category": "proprietary",
    },
    # Medical-domain
    # HF: FreedomIntelligence/HuatuoGPT-Vision-34B  — needs vLLM (34B)
    {
        "name": "HuatuoGPT-V-34B",
        "model": "FreedomIntelligence/HuatuoGPT-Vision-34B",
        "base_url": "http://localhost:8012/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "vllm",
    },
    # HF: DUTIR-BioNLP/Lingshu-32B  — needs vLLM (32B)
    {
        "name": "Lingshu-32B",
        "model": "DUTIR-BioNLP/Lingshu-32B",
        "base_url": "http://localhost:8013/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "vllm",
    },
    # HF: microsoft/llava-med-v1.5-mistral-7b  — NOT in Ollama registry; needs vLLM
    {
        "name": "Llava-Med-7B",
        "model": "microsoft/llava-med-v1.5-mistral-7b",
        "base_url": "http://localhost:8014/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "vllm",
    },
    # HF: google/medgemma-4b-it  — NOT in Ollama registry; needs vLLM
    {
        "name": "MedGemma-4B",
        "model": "google/medgemma-4b-it",
        "base_url": "http://localhost:8016/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "vllm",
    },
    # Open-source
    # HF: Qwen/Qwen3-VL-30B-Instruct  — needs vLLM (30B)
    {
        "name": "Qwen3-VL-30B",
        "model": "Qwen/Qwen3-VL-30B-Instruct",
        "base_url": "http://localhost:8010/v1",
        "api_key": "local",
        "category": "open-source",
        "backend": "vllm",
    },
    # HF: OpenGVLab/InternVL3-38B  — needs vLLM (38B)
    {
        "name": "InternVL3-38B",
        "model": "OpenGVLab/InternVL3-38B",
        "base_url": "http://localhost:8011/v1",
        "api_key": "local",
        "category": "open-source",
        "backend": "vllm",
    },
    # HF: Qwen/Qwen2.5-VL-7B-Instruct  — official Ollama tag: qwen2.5vl:7b
    # (Qwen3-VL not yet in Ollama registry; Qwen2.5-VL is same family, one version back)
    {
        "name": "Qwen2.5-VL-7B",
        "model": "qwen2.5vl:7b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "local",
        "category": "open-source",
        "backend": "ollama",
    },
    # HF: deepseek-ai/Janus-Pro-7B  — NOT in Ollama registry; needs vLLM
    {
        "name": "Janus-Pro-7B",
        "model": "deepseek-ai/Janus-Pro-7B",
        "base_url": "http://localhost:8015/v1",
        "api_key": "local",
        "category": "open-source",
        "backend": "vllm",
    },
]

# Lookup by name
MODEL_MAP = {m["name"]: m for m in MODELS}
