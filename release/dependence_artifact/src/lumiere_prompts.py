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
    "Answer-length rule: the correct option must NOT be recognisable by its "
    "form. Make all options similar in length (within ~15% of each other), "
    "level of detail, hedging and register — if the correct answer needs a "
    "qualifier or rationale clause, give every distractor an equally detailed "
    "clause; never make distractors absolute or curt while the correct answer "
    "is nuanced. Vary which letter is correct. "
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
        "pseudoprogression, since that judgment call needs expert review. "
        "STYLE RULE: every option must read like a cautious, real-world clinical "
        "recommendation with the same structure — an action, a monitoring or "
        "reassessment element (e.g. repeat imaging interval, tumor-board review), "
        "and a rationale clause. Do NOT make distractors abrupt or absolute "
        "(avoid 'immediately', 'definitively', 'directly', 'without', 'regardless'); "
        "they should be plausible options a clinician could defend, wrong only "
        "because of THIS patient's specific facts. Do NOT make the correct answer "
        "the only one that mentions monitoring, repeat imaging or pseudoprogression."
    ),
}


# Leak-free (v3) rewrite — see src/lumiere_leakage.py for the rules these instructions state and the
# check the drafter retries against. The chain only works if each phase's answer must come from the
# images or the quiz-taker's OWN earlier answers, so no stem/option may restate an earlier phase's answer.
_LEAK_FREE_RULE = (
    "CHAIN RULE (strict): this item is one step in a multi-step case. The quiz-taker answers earlier steps "
    "themselves and sees their own earlier answers, so this item must NOT reveal any earlier step's answer. "
    "In the STEM, you may state ONLY: the patient id, timepoint ids, and non-imaging clinical facts (age, sex, "
    "IDH/MGMT status, extent of resection, treatment protocol). The stem must NOT state any imaging finding: no "
    "percentages, no volumes or measurements, no lesion location/region names, no words describing change "
    "(increase, decrease, growth, shrinkage, resolution, progression, regression, enlargement), and no RANO "
    "response category. Instead, refer the quiz-taker to 'the imaging' and 'your earlier assessment of this "
    "patient'. Do not invent clinical details (e.g. steroid dose, neurological status) that are not in the facts."
)

_PHASE_INSTRUCTIONS_LEAK_FREE = {
    "LIL": (
        "Write a question about the lesion's location and how its volume changed between the baseline and "
        "follow-up timepoints given in the facts. Ground the answer in the given volumes_mm3/regions. The STEM "
        "may name the timepoints and the baseline location, but must NOT state the follow-up location, the "
        "percentage change, or the direction of change — those are what the quiz-taker must read off the images."
    ),
    "PJRF": (
        _PHASE_INSTRUCTIONS["PJRF"] + " The STEM must NOT state the patient's survival time (that is the answer). "
        "OPTIONS must differ only in the prognosis (e.g. survival range) and prognostic reasoning from "
        "demographic/molecular factors; they must NOT mention imaging findings, volume change, or any RANO "
        "response category."
    ),
    "TCM": (
        _PHASE_INSTRUCTIONS["TCM"] + " The correct management follows from this patient's actual disease course "
        "(given in the prior-chain block for YOUR reference only). OPTIONS must differ by the management action "
        "and its monitoring plan, and must NOT restate the disease state: no RANO category, no percentages or "
        "volumes, no words describing tumor change (increase, decrease, growth, progression, regression, "
        "resolution). The quiz-taker must work out the disease state from their own earlier answers."
    ),
}


def build_draft_prompt(
    patient_id: str,
    phase: str,
    phase_facts: dict,
    chain_context: list[dict],
    leak_free: bool = False,
) -> list[dict]:
    phase_name = config.PHASE_NAMES[phase]
    chain_block = ""
    if chain_context:
        chain_block = ("\n\n--- PRIOR PHASES IN THIS PATIENT'S CHAIN (for your consistency only — do NOT "
                       "restate these answers in this item) ---\n" if leak_free
                       else "\n\n--- PRIOR PHASES IN THIS PATIENT'S CHAIN ---\n")
        for entry in chain_context:
            chain_block += (
                f"[{entry['phase']}] Q: {entry['question']}\n"
                f"  Correct answer: {entry['answer']} — {entry['answer_text']}\n\n"
            )
        chain_block += "--- END PRIOR CHAIN ---"

    task = (f"{_PHASE_INSTRUCTIONS_LEAK_FREE[phase]}\n\n{_LEAK_FREE_RULE}"
            if leak_free and phase in _PHASE_INSTRUCTIONS_LEAK_FREE else _PHASE_INSTRUCTIONS[phase])
    text = (
        f"Patient: {patient_id}\n"
        f"Phase: {phase_name} ({phase})\n\n"
        f"--- VERIFIED FACTS FOR THIS PHASE ---\n{json.dumps(phase_facts, indent=2, default=str)}\n"
        f"{chain_block}\n\n"
        f"Task: {task}\n\n"
        f"Respond ONLY with this JSON:\n\n{_DRAFT_JSON_SCHEMA}"
    )

    return [
        {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
