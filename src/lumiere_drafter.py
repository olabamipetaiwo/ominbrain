"""
LLM-drafts MCQ items from verified LUMIERE facts (src/lumiere_facts.py output).

Uses an existing proprietary model from config/models.py (default: GPT-5,
direct OpenAI API — no LiteLLM proxy needed) purely for its client wiring, the
same way src/evaluator.py does. No new model-serving infrastructure.

Runs one call per (patient, phase), in causal order, feeding prior phases'
drafted Q/A as authoring-time chain context so the chain reads coherently
end-to-end. Output is written per patient to data/lumiere/drafts/<id>.json,
already shaped like the OmniBrainBench flat-question schema plus the
additional fields lumiere_loader.py needs (patient_id, timepoint,
fact_provenance, review_status, needs_expert_judgment).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from openai import OpenAI

import config
import config.lumiere as lcfg
from config.models import MODEL_MAP
from src.lumiere_prompts import build_draft_prompt

LETTERS = "ABCDE"


def _call_model(client: OpenAI, model: str, messages: list[dict], label: str = "") -> str:
    """Same retry pattern as src/evaluator.py::_call_model, kept as a small
    local copy so this module doesn't depend on evaluator.py internals."""
    for attempt in range(config.API_RETRY_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages,
                max_tokens=config.MAX_TOKENS, temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            is_last = attempt == config.API_RETRY_ATTEMPTS - 1
            print(f"  [API error{f' ({label})' if label else ''}] attempt {attempt+1}: {e}")
            if is_last:
                return ""
            time.sleep(config.API_RETRY_DELAY * (2 ** attempt))
    return ""


def _parse_json(text: str, required_keys: list[str]) -> dict | None:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        data = json.loads(text)
        if all(k in data for k in required_keys):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if all(k in data for k in required_keys):
                return data
        except json.JSONDecodeError:
            pass
    return None


def build_client(model_name: str = "GPT-5") -> tuple[OpenAI, str]:
    model_cfg = MODEL_MAP[model_name]
    kwargs = {}
    if model_cfg.get("base_url"):
        kwargs["base_url"] = model_cfg["base_url"]
    kwargs["api_key"] = model_cfg.get("api_key") or None
    client = OpenAI(**{k: v for k, v in kwargs.items() if v is not None})
    return client, model_cfg["model"]


def _timepoint_for_phase(facts: dict, phase: str) -> str:
    lil = facts["phase_facts"]["LIL"]
    if phase == "AIA":
        return lil["baseline"]["timepoint_id"]
    if phase in ("LIL", "DSCR"):
        return lil["followup"]["timepoint_id"]
    return facts["followup_timepoint"]


def draft_patient_chain(patient_id: str, facts: dict, client: OpenAI, model: str) -> list[dict]:
    chain_context: list[dict] = []
    questions: list[dict] = []

    for phase in config.PHASES:
        phase_facts = facts["phase_facts"].get(phase)
        if not phase_facts:
            continue

        messages = build_draft_prompt(patient_id, phase, phase_facts, chain_context)
        raw = _call_model(client, model, messages, label=f"{patient_id}/{phase}")
        parsed = _parse_json(raw, ["question", "options", "answer"])
        if parsed is None:
            print(f"  [skip] {patient_id}/{phase}: draft parse failed")
            continue

        answer = parsed["answer"].strip().upper()
        options = {k: v for k, v in parsed["options"].items() if k in LETTERS}
        if answer not in options or not (3 <= len(options) <= 5):
            print(f"  [skip] {patient_id}/{phase}: invalid options/answer shape")
            continue

        q = {
            "id": f"{patient_id}_{phase}",
            "question": parsed["question"],
            "options": options,
            "correct_answer": answer,
            "correct_answer_text": options[answer],
            "task_label": lcfg.LUMIERE_TASK_LABEL_MAP[phase],
            "clinical_phase": config.PHASE_NAMES[phase],
            "patient_id": patient_id,
            "timepoint": _timepoint_for_phase(facts, phase),
            "facts_used": phase_facts,
            "distractor_rationale": parsed.get("distractor_rationale", ""),
            "distractor_confidence": parsed.get("distractor_confidence", "high"),
            "needs_expert_judgment": bool(phase_facts.get("needs_expert_judgment", phase in ("PJRF", "TCM"))),
            "review_status": "pending",
            "_image_path": "",  # filled in by lumiere_loader.py from rendered slices
            "_image_dir": "",
        }
        questions.append(q)
        chain_context.append({
            "phase": phase,
            "question": q["question"],
            "answer": answer,
            "answer_text": q["correct_answer_text"],
        })
        time.sleep(0.3)

    return questions


def draft_all(patient_ids: list[str], model_name: str = "GPT-5",
              facts_dir: Path | None = None, out_dir: Path | None = None,
              force: bool = False) -> None:
    facts_dir = facts_dir or Path(lcfg.LUMIERE_DATA_DIR) / "facts"
    out_dir = out_dir or Path(lcfg.LUMIERE_DATA_DIR) / "drafts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Skip patients already drafted — avoids re-spending API credit when
    # re-running against an expanded patient list (see plan: idempotency fix).
    # An empty [] file means every phase failed last time (e.g. the LLM proxy
    # was down) — that must NOT count as "done", or a transient outage would
    # permanently strand those patients with no drafted items.
    to_process = []
    for pid in patient_ids:
        out_path = out_dir / f"{pid}.json"
        if out_path.exists() and not force:
            existing = json.loads(out_path.read_text())
            if existing:
                print(f"  [skip] draft already exists for {pid} ({len(existing)} items)")
                continue
            print(f"  [retry] {pid} had an empty/failed draft — redrafting")
        to_process.append(pid)

    if not to_process:
        print("Nothing new to draft.")
        return

    client, model = build_client(model_name)
    for pid in to_process:
        fpath = facts_dir / f"{pid}.json"
        if not fpath.exists():
            print(f"  [skip] no facts for {pid}")
            continue
        facts = json.loads(fpath.read_text())
        print(f"Drafting chain for {pid}…")
        questions = draft_patient_chain(pid, facts, client, model)
        out_path = out_dir / f"{pid}.json"
        out_path.write_text(json.dumps(questions, indent=2, default=str))
        print(f"  -> {out_path} ({len(questions)} phases drafted)")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="LLM-draft LUMIERE MCQ items from facts")
    p.add_argument("--patients", type=str, default=None,
                    help="comma-separated patient IDs; default: all in data/lumiere/facts/")
    p.add_argument("--model", type=str, default="GPT-5")
    p.add_argument("--force", action="store_true", help="re-draft even if output already exists")
    args = p.parse_args()

    if args.patients:
        ids = args.patients.split(",")
    else:
        facts_dir = Path(lcfg.LUMIERE_DATA_DIR) / "facts"
        ids = sorted(p.stem for p in facts_dir.glob("Patient-*.json"))

    draft_all(ids, model_name=args.model, force=args.force)
