"""
Authoring-time prompt builders for drafting LUMIERE MCQ items from extracted
facts. Kept separate from src/prompts.py, which is fixed to the eval-time
{answer, visual_grounding, reasoning} contract — drafting has a different
system role, audience, and JSON schema.
"""

from __future__ import annotations

import json

import config

DRAFT_SYSTEM_PROMPT = (
    "You are a neuro-oncology question writer building a multiple-choice "
    "benchmark item from real, verified patient facts. "
    "Derive the correct answer STRICTLY from the given facts — never invent "
    "clinical information not present in them. "
    "Write 3-4 distractors that are clinically plausible (not obviously "
    "wrong), consistent with real glioblastoma cases in general, but "
    "factually inconsistent with THIS patient's given facts. "
    "Always respond with valid JSON only — no markdown, no extra text."
)

_DRAFT_JSON_SCHEMA = (
    "{\n"
    '  "question": "<the MCQ stem>",\n'
    '  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},\n'
    '  "answer": "<single letter matching the correct option>",\n'
    '  "distractor_rationale": "<one sentence per distractor on why it is wrong '
    'for this patient>",\n'
    '  "distractor_confidence": "<\'high\' if you are confident every distractor '
    "is clearly wrong to a domain expert, 'low' if you are unsure>\"\n"
    "}"
)

_PHASE_INSTRUCTIONS = {
    "AIA": (
        "Write a question about which imaging modalities/sequences were used "
        "to assess this patient at this timepoint, or basic image "
        "characteristics evident from the facts (e.g. presence of a lesion)."
    ),
    "LIL": (
        "Write a question about the lesion's location and how its volume has "
        "changed between the baseline and follow-up timepoint given in the "
        "facts. Ground the answer in the specific volumes_mm3/regions given."
    ),
    "DSCR": (
        "Write a question asking a quiz-taker to determine the disease course "
        "(RANO response category) at the follow-up timepoint from the imaging "
        "findings. The correct answer is the given rating_label, but the "
        "question STEM must NOT state or paraphrase that label — the "
        "quiz-taker should have to infer it from lesion/volume-change facts, "
        "the same way a radiologist would."
    ),
    "PJRF": (
        "Write a prognosis-related question (e.g. expected survival range, "
        "risk factors) grounded in the given demographic/pathology facts. "
        "Since LLM-only prognosis distractors are risky, keep distractors "
        "conservative and mark distractor_confidence 'low' unless you are "
        "highly confident in GBM prognostic literature."
    ),
    "TCM": (
        "Write a treatment-management question about this patient's care "
        "(e.g. standard-of-care protocol, or how to interpret an apparent "
        "progression given the possible_pseudoprogression_flag). Mark "
        "distractor_confidence 'low' if the question touches progression-vs-"
        "pseudoprogression, since that judgment call needs expert review."
    ),
}


def build_draft_prompt(
    patient_id: str,
    phase: str,
    phase_facts: dict,
    chain_context: list[dict],
) -> list[dict]:
    phase_name = config.PHASE_NAMES[phase]
    chain_block = ""
    if chain_context:
        chain_block = "\n\n--- PRIOR PHASES IN THIS PATIENT'S CHAIN ---\n"
        for entry in chain_context:
            chain_block += (
                f"[{entry['phase']}] Q: {entry['question']}\n"
                f"  Correct answer: {entry['answer']} — {entry['answer_text']}\n\n"
            )
        chain_block += "--- END PRIOR CHAIN ---"

    text = (
        f"Patient: {patient_id}\n"
        f"Phase: {phase_name} ({phase})\n\n"
        f"--- VERIFIED FACTS FOR THIS PHASE ---\n{json.dumps(phase_facts, indent=2, default=str)}\n"
        f"{chain_block}\n\n"
        f"Task: {_PHASE_INSTRUCTIONS[phase]}\n\n"
        f"Respond ONLY with this JSON:\n\n{_DRAFT_JSON_SCHEMA}"
    )

    return [
        {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
