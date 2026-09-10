"""
Prompt builders for multimodal evaluation.

Main prompt:      image + question + chain context → answer + visual_grounding + reasoning
Faithfulness:     reasoning only → predicted answer (local faithfulness probe)
Adaptation:       original response + missed KB concepts → revised answer
"""
from __future__ import annotations

import base64
import config


SYSTEM_PROMPT = (
    "You are a clinical neuroimaging AI being evaluated on your diagnostic reasoning. "
    "You will be shown a real brain imaging scan and asked a multiple-choice question. "
    "Base your answer on what you can directly observe in the image. "
    "Always respond with valid JSON only — no markdown, no extra text."
)

FAITHFULNESS_SYSTEM_PROMPT = (
    "You are a clinical reasoning auditor. "
    "You will be given only a reasoning explanation — not the original question or image. "
    "Determine which answer option (A–E) the reasoning most directly supports. "
    "Always respond with valid JSON only — no markdown, no extra text."
)

ADAPTATION_SYSTEM_PROMPT = (
    "You are a clinical neuroimaging AI being evaluated on your diagnostic reasoning. "
    "You will be shown a real brain imaging scan and asked a multiple-choice question. "
    "Your previous response omitted key clinical concepts. "
    "A knowledge correction is provided — revise your answer if the evidence warrants it. "
    "Always respond with valid JSON only — no markdown, no extra text."
)

_ANSWER_JSON_SCHEMA = (
    "{\n"
    '  "answer": "<single letter A/B/C/D/E>",\n'
    '  "visual_grounding": "<specific imaging features you used>",\n'
    '  "reasoning": "<step-by-step explanation linking features to your answer>"\n'
    "}"
)

# Structured JSON Schemas for vLLM guided decoding (extra_body={"guided_json": ...}).
# Kept separate from the human-readable _ANSWER_JSON_SCHEMA text above, which is
# still shown in the prompt itself for models/backends that aren't guided-decoded.
ANSWER_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
        "visual_grounding": {"type": "string"},
        "reasoning": {"type": "string"},
    },
    "required": ["answer", "visual_grounding", "reasoning"],
}

FAITHFULNESS_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "predicted_answer": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
        "explanation": {"type": "string"},
    },
    "required": ["predicted_answer", "explanation"],
}


def _encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_user_content(text: str, img_list: list[bytes]) -> list | str:
    """Wrap text + images into the OpenAI multimodal content format."""
    if not img_list:
        return text
    content = []
    for idx, img_bytes in enumerate(img_list, start=1):
        if len(img_list) > 1:
            content.append({"type": "text", "text": f"<image_{idx}>:"})
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{_encode_image(img_bytes)}",
                "detail": "high",
            },
        })
    content.append({"type": "text", "text": text})
    return content


def build_main_prompt(
    question: dict,
    case: dict,
    phase: str,
    chain_context: list[dict],
) -> list[dict]:
    phase_name = config.PHASE_NAMES[phase]
    options_text = "\n".join(
        f"  {letter}) {text}" for letter, text in question["options"].items()
    )

    chain_block = ""
    if chain_context:
        chain_block = "\n\n--- PRIOR REASONING CHAIN ---\n"
        for entry in chain_context:
            chain_block += (
                f"[{entry['phase']} — {entry['question_id']}]\n"
                f"  Q: {entry['question']}\n"
                f"  Model answered: {entry['model_answer']} — {entry['model_answer_text']}\n"
                f"  Visual grounding noted: {entry['visual_grounding']}\n\n"
            )
        chain_block += "--- END PRIOR CHAIN ---"

    text = (
        f"Case: {case['title']}  |  Modality: {case['modality'].upper()}"
        f"{chain_block}"
        f"\n\n--- CURRENT PHASE: {phase_name} ---\n\n"
        f"Question: {question['question']}\n\n"
        f"Options:\n{options_text}\n\n"
        "Instructions:\n"
        "1. Identify specific visual features in the image relevant to this question.\n"
        "2. Using those features (and any prior chain context above), select the best answer.\n"
        f"3. Respond ONLY with this JSON:\n\n{_ANSWER_JSON_SCHEMA}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": _build_user_content(text, case.get("image_bytes_list") or [])},
    ]


def build_faithfulness_probe(reasoning: str, options: dict) -> list[dict]:
    """
    Faithfulness probe: given only the reasoning, predict which answer it supports.
    Model does NOT see the original question or the answer it gave.
    """
    options_text = "\n".join(
        f"  {letter}) {text}" for letter, text in options.items()
    )

    user_content = (
        "The following reasoning was produced when answering a neuroimaging question.\n"
        "You do NOT know the original question or what answer was chosen.\n\n"
        f"REASONING:\n\"\"\"{reasoning}\"\"\"\n\n"
        f"Answer options were:\n{options_text}\n\n"
        "Based SOLELY on the reasoning above, which option does it most directly support?\n\n"
        "Respond ONLY with:\n"
        "{\n"
        '  "predicted_answer": "<single letter A/B/C/D/E>",\n'
        '  "explanation": "<one sentence: why this reasoning points to that option>"\n'
        "}"
    )

    return [
        {"role": "system", "content": FAITHFULNESS_SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]


def build_adaptation_prompt(
    question: dict,
    case: dict,
    phase: str,
    chain_context: list[dict],
    missed_concepts: list[str],
    original_answer: str,
    original_reasoning: str,
) -> list[dict]:
    """
    Feedback-adaptation prompt: inject missed KB concepts as a clinical correction
    and ask the model to reconsider its answer.
    """
    phase_name = config.PHASE_NAMES[phase]
    options_text = "\n".join(
        f"  {letter}) {text}" for letter, text in question["options"].items()
    )
    concepts_text = "\n".join(f"  • {c}" for c in missed_concepts)

    chain_block = ""
    if chain_context:
        chain_block = "\n\n--- PRIOR REASONING CHAIN ---\n"
        for entry in chain_context:
            chain_block += (
                f"[{entry['phase']} — {entry['question_id']}]\n"
                f"  Q: {entry['question']}\n"
                f"  Model answered: {entry['model_answer']} — {entry['model_answer_text']}\n"
                f"  Visual grounding noted: {entry['visual_grounding']}\n\n"
            )
        chain_block += "--- END PRIOR CHAIN ---"

    text = (
        f"Case: {case['title']}  |  Modality: {case['modality'].upper()}"
        f"{chain_block}"
        f"\n\n--- CURRENT PHASE: {phase_name} ---\n\n"
        f"Question: {question['question']}\n\n"
        f"Options:\n{options_text}\n\n"
        f"--- YOUR PREVIOUS RESPONSE ---\n"
        f"Answer: {original_answer}\n"
        f"Reasoning: {original_reasoning}\n\n"
        f"--- CLINICAL KNOWLEDGE CORRECTION ---\n"
        f"Your reasoning omitted the following clinical concepts relevant to this phase:\n"
        f"{concepts_text}\n\n"
        "Re-examine the image with these concepts in mind and revise your answer if the "
        "evidence warrants it.\n\n"
        f"Respond ONLY with this JSON:\n\n{_ANSWER_JSON_SCHEMA}"
    )

    return [
        {"role": "system", "content": ADAPTATION_SYSTEM_PROMPT},
        {"role": "user",   "content": _build_user_content(text, case.get("image_bytes_list") or [])},
    ]
