# 10 models selected for the causal chain benchmark.
# (Deepseek-V3.1 and Janus-Pro-7B dropped — DeepSeek is not permitted on HiPerGator,
#  as an API provider or as an upstream model source.)
#
# Grouped into 3 categories:
#   Proprietary   — Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet
#   Medical       — HuatuoGPT-V-34B, Lingshu-32B, Llava-Med-7B, MedGemma-4B
#   Open-source   — Qwen3-VL-30B, InternVL3-38B, Qwen2.5-VL-7B
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
#            Best for: Qwen2.5-VL-7B, Llava-Med-7B, MedGemma-4B
#
# "vllm"     Large open-weight vision models — requires vLLM server running
#            Best for: Qwen3-VL-30B, InternVL3-38B, HuatuoGPT-V-34B, Lingshu-32B
#            Start server:
#              vllm serve Qwen/Qwen3-VL-30B-A3B-Instruct                 --port 8010 --tensor-parallel-size 2
#              vllm serve OpenGVLab/InternVL3-38B                        --port 8011 --tensor-parallel-size 2
#              vllm serve FreedomIntelligence/HuatuoGPT-Vision-34B       --port 8012
#              vllm serve lingshu-medical-mllm/Lingshu-32B               --port 8013
#              vllm serve microsoft/llava-med-v1.5-mistral-7b            --port 8014
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
    # Medical-domain
    # HF: FreedomIntelligence/HuatuoGPT-Vision-34B-hf  — needs vLLM (34B).
    # The base (non "-hf") repo declares a custom `llava_llama` architecture from the
    # original 2023 LLaVA research codebase with no auto_map — vLLM/transformers can't
    # load it natively even with --trust-remote-code. This "-hf" repo (same org,
    # official) is the properly converted `LlavaForConditionalGeneration` checkpoint.
    # The -hf conversion's tokenizer ships no chat_template (transformers >=4.44
    # refuses to guess one) — vllm serve 400s on every request without it. Base LM is
    # Yi-34B (LlamaForCausalLM, 56 attn heads), whose native/official format is
    # ChatML — see config/chat_templates/chatml.jinja.
    {
        "name": "HuatuoGPT-V-34B",
        "model": "FreedomIntelligence/HuatuoGPT-Vision-34B-hf",
        "base_url": "http://localhost:8012/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "vllm",
        "chat_template": "config/chat_templates/chatml.jinja",
    },
    # HF: lingshu-medical-mllm/Lingshu-32B  — needs vLLM (32B)
    {
        "name": "Lingshu-32B",
        "model": "lingshu-medical-mllm/Lingshu-32B",
        "base_url": "http://localhost:8013/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "vllm",
    },
    # HF: chaoyinshe/llava-med-v1.5-mistral-7b-hf  — needs vLLM.
    # Microsoft's official repo declares a custom `llava_mistral` architecture from the
    # original 2023 LLaVA research codebase with no auto_map — vLLM/transformers can't
    # load it natively even with --trust-remote-code. This community "-hf" repo is a
    # properly converted `LlavaForConditionalGeneration` checkpoint of the same weights
    # (2,967 downloads) — third-party re-upload, not Microsoft's repo; note in methods.
    # Same missing-chat_template issue as HuatuoGPT-V-34B above. This checkpoint was
    # fine-tuned in the original LLaVA codebase's single-turn Vicuna-v1 format (not
    # Mistral's native [INST]...[/INST]) — see config/chat_templates/vicuna_v1.jinja.
    #
    # KNOWN FINDING, not a bug: this model cannot follow the strict JSON-only system
    # prompt (SYSTEM_PROMPT in src/prompts.py) — confirmed via direct API testing that
    # it produces a working, coherent free-text response to the same question/image
    # without that instruction, but degenerates to ~1 token (a space, then EOS) under
    # greedy decoding (temperature=0.0) once the "respond ONLY with valid JSON" demand
    # is added. Root cause: LLaVA-Med v1.5 was fine-tuned in 2023 on free-text medical
    # VQA answers, never on structured JSON output. Deliberately left unmodified and
    # run under the same standard prompt as every other model — the near-zero score
    # this produces is the intended, reported result ("this model cannot produce valid
    # structured output under instruction"), not something to work around.
    {
        "name": "Llava-Med-7B",
        "model": "chaoyinshe/llava-med-v1.5-mistral-7b-hf",
        "base_url": "http://localhost:8014/v1",
        "api_key": "local",
        "chat_template": "config/chat_templates/vicuna_v1.jinja",
        "category": "medical",
        "backend": "vllm",
    },
    # Official Google build on Ollama: medgemma:4b (vision-capable)
    {
        "name": "MedGemma-4B",
        "model": "medgemma:4b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "local",
        "category": "medical",
        "backend": "ollama",
    },
    # Open-source
    # HF: Qwen/Qwen3-VL-30B-A3B-Instruct  — needs vLLM (30B total / 3B active, MoE)
    {
        "name": "Qwen3-VL-30B",
        "model": "Qwen/Qwen3-VL-30B-A3B-Instruct",
        "base_url": "http://localhost:8010/v1",
        "api_key": "local",
        "category": "open-source",
        "backend": "vllm",
    },
    # HF: OpenGVLab/InternVL3-38B  — needs vLLM (38B).
    # Its own bundled chat template assumes plain-string message content and crashes
    # (`TypeError: can only concatenate str (not "list") to str`) on the OpenAI-style
    # multi-part list content our pipeline sends for every image question — this
    # wasn't caught by the earlier /v1/models liveness check, only by an actual real
    # eval run. LLM backbone is Qwen2ForCausalLM (see config.json), whose native
    # format is ChatML — reusing the same chatml.jinja that already works for
    # HuatuoGPT-V-34B bypasses the broken default template entirely.
    {
        "name": "InternVL3-38B",
        "model": "OpenGVLab/InternVL3-38B",
        "base_url": "http://localhost:8011/v1",
        "api_key": "local",
        "category": "open-source",
        "backend": "vllm",
        "chat_template": "config/chat_templates/chatml.jinja",
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
]

# Lookup by name
MODEL_MAP = {m["name"]: m for m in MODELS}
