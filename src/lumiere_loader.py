"""
Adapter: reviewed LUMIERE items -> CausalChainEvaluator case format.

Mirrors src/data_loader.py's build_cases()/load_omnibrain() shape exactly, so
CausalChainEvaluator, KBAligner, check_gate, and the prompt builders all run
completely unmodified on LUMIERE cases (confirmed by reading their source —
they only ever consume the case/question dict shape, never source_file
semantics beyond an opaque label).

Key schema-mismatch resolutions (see plan):
  - source_file (stitched multi-patient bucket) -> patient_id (the genuine
    chain key). evaluator.py only reads case.get("source_file", "") for
    logging, so this is a safe drop-in.
  - grounding_terms come from facts_used (region names, RANO label, etc.)
    rather than TASK_GROUNDING_TERMS, since LUMIERE's task labels are mapped
    from config/lumiere.py's LUMIERE_TASK_LABEL_MAP and TASK_GROUNDING_TERMS
    already has entries for those exact task labels (reused, not reinvented).
  - _image_path points at the rendered slice PNGs from
    lumiere_facts.render_slices_for_patient().
"""

from __future__ import annotations

import json
from pathlib import Path

import config
import config.lumiere as lcfg
from src.phase_map import TASK_GROUNDING_TERMS

LETTERS = "ABCDE"


def _grounding_terms_for(task_label: str) -> list[str]:
    return list(TASK_GROUNDING_TERMS.get(task_label, []))


def _image_path_for(question: dict) -> str | list[str]:
    facts = question.get("facts_used", {})
    phase = None
    for abbr, name in config.PHASE_NAMES.items():
        if name == question.get("clinical_phase"):
            phase = abbr
            break

    slices_dir = Path(lcfg.LUMIERE_DATA_DIR) / "slices" / question["patient_id"]
    if phase == "LIL":
        baseline_tp = facts.get("baseline", {}).get("timepoint_id")
        followup_tp = facts.get("followup", {}).get("timepoint_id")
        paths = [p for p in (
            f"{baseline_tp}.png" if baseline_tp else None,
            f"{followup_tp}.png" if followup_tp else None,
        ) if p]
        return paths if len(paths) > 1 else (paths[0] if paths else "")

    tp = question.get("timepoint")
    return f"{tp}.png" if tp and (slices_dir / f"{tp}.png").exists() else ""


def _image_dir_for(question: dict) -> Path:
    return Path(lcfg.LUMIERE_DATA_DIR) / "slices" / question["patient_id"]


def merge_reviewed(reviewed_dir: Path | None = None) -> list[dict]:
    """Combine all data/lumiere/reviewed/<patient_id>_<phase>.json items,
    keeping only approved/edited (dropping rejected)."""
    reviewed_dir = reviewed_dir or Path(lcfg.LUMIERE_DATA_DIR) / "reviewed"
    items = []
    for fpath in sorted(reviewed_dir.glob("*.json")):
        data = json.loads(fpath.read_text())
        rows = data if isinstance(data, list) else [data]
        for row in rows:
            if row.get("review_status") in ("approved", "edited"):
                items.append(row)
    return items


def build_lumiere_cases(items: list[dict], n_cases: int | None = None,
                          min_phases: int = 2) -> list[dict]:
    """Groups reviewed items by patient_id (the genuine chain key) into cases
    in the exact shape CausalChainEvaluator/data_loader.build_cases() uses."""
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(item["patient_id"], []).append(item)

    cases = []
    for patient_id, questions in groups.items():
        phase_buckets: dict[str, list[dict]] = {}
        for q in questions:
            abbr = next((a for a, n in config.PHASE_NAMES.items() if n == q["clinical_phase"]), None)
            if abbr:
                phase_buckets.setdefault(abbr, []).append(q)

        if len(phase_buckets) < min_phases:
            continue

        phases_dict: dict[str, list[dict]] = {}
        for phase_abbr in config.PHASES:
            bucket = phase_buckets.get(phase_abbr)
            if not bucket:
                continue
            phase_qs = []
            for q in bucket:
                options = q["options"]
                if not (3 <= len(options) <= 5) or q["correct_answer"] not in options:
                    continue  # ingest-time validation per plan
                phase_qs.append({
                    "id": q["id"],
                    "question": q["question"],
                    "options": options,
                    "correct_answer": q["correct_answer"],
                    "correct_answer_text": q["correct_answer_text"],
                    "task_label": q["task_label"],
                    "grounding_terms": _grounding_terms_for(q["task_label"]),
                    "chain_grounding_terms": [],
                    "_image_path": _image_path_for(q),
                    "_image_dir": _image_dir_for(q),
                })
            if phase_qs:
                phases_dict[phase_abbr] = phase_qs

        if not phases_dict:
            continue

        cases.append({
            "id": patient_id,
            "title": f"LUMIERE GBM Case ({patient_id})",
            "modality": "mri",
            "source_file": patient_id,  # opaque label only, per evaluator.py's .get() usage
            "_image_dir": _image_dir_for(questions[0]),
            "image_bytes": None,
            "image_bytes_list": None,
            "phases": phases_dict,
        })

    if n_cases:
        cases = cases[:n_cases]

    phase_counts = {p: sum(1 for c in cases if p in c["phases"]) for p in config.PHASES}
    print(f"Built {len(cases)} LUMIERE cases | phase coverage: "
          + " | ".join(f"{p}:{phase_counts[p]}" for p in config.PHASES if phase_counts[p] > 0))
    return cases


def load_lumiere(n_cases: int | None = None, min_phases: int = 2, **kwargs) -> list[dict]:
    items = merge_reviewed()
    return build_lumiere_cases(items, n_cases=n_cases, min_phases=min_phases)
