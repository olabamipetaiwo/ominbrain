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
import random
from pathlib import Path

import config
import config.lumiere as lcfg
from src.phase_map import TASK_GROUNDING_TERMS

LETTERS = "ABCDE"


def _shuffle_options(options: dict, correct: str, seed_key: str) -> tuple[dict, str]:
    """Deterministically permute option texts across letters and re-map the answer.

    The LLM drafter puts the correct option first (A) on ~90% of items, so unshuffled
    accuracy would reward always answering "A". Seeded per item id -> reproducible.
    Done at load time so the drafts the expert reviews (whose rationales cite letters)
    are left untouched."""
    pairs = [(k, options[k]) for k in sorted(options)]
    random.Random(f"42:{seed_key}").shuffle(pairs)
    new = {LETTERS[i]: text for i, (_, text) in enumerate(pairs)}
    new_correct = LETTERS[next(i for i, (k, _) in enumerate(pairs) if k == correct)]
    return new, new_correct


def _grounding_terms_for(task_label: str) -> list[str]:
    return list(TASK_GROUNDING_TERMS.get(task_label, []))


def _image_path_for(question: dict) -> str | list[str]:
    # v4 items list their rendered files explicitly (may be empty for text-only PJRF/TCM items)
    if question.get("image_files") is not None:
        return list(question["image_files"])
    # v3 items name their images explicitly (DSCR gets baseline + follow-up, like LIL)
    if question.get("image_timepoints"):
        return [f"{tp}.png" for tp in question["image_timepoints"]]
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


def _image_labels_for(question: dict) -> list[str] | None:
    """Human-readable label per image in _image_path_for's list, so the model is told
    which numbered image is baseline vs follow-up instead of inferring it from order
    alone. Only meaningful for LIL (the only phase with >1 image); None elsewhere —
    prompts.py falls back to its existing generic <image_N> labeling in that case,
    so single-image phases and OmniBrainBench (data_loader.py's own cases, which never
    set this field) are unaffected.

    Investigated 2026-09-22 as a candidate cause of LIL's frequent growth/shrinkage
    direction errors (up to 68% of one model's wrong LIL answers): the two images were
    already sent in the correct baseline-then-follow-up order, but only ever labeled
    generically ("<image_1>:", "<image_2>:"), never tied to which timepoint is which."""
    if question.get("image_files") is not None:
        return question.get("image_labels")
    if question.get("image_timepoints"):
        tps = question["image_timepoints"]
        return [f"baseline ({tps[0]})", f"follow-up ({tps[1]})"] if len(tps) == 2 else None
    facts = question.get("facts_used", {})
    if question.get("clinical_phase") != config.PHASE_NAMES.get("LIL"):
        return None
    baseline_tp = facts.get("baseline", {}).get("timepoint_id")
    followup_tp = facts.get("followup", {}).get("timepoint_id")
    if not (baseline_tp and followup_tp):
        return None
    return [f"baseline ({baseline_tp})", f"follow-up ({followup_tp})"]


def _image_dir_for(question: dict) -> Path:
    if question.get("image_dir"):
        return Path(question["image_dir"])
    return Path(lcfg.LUMIERE_DATA_DIR) / "slices" / question["patient_id"]


def merge_reviewed(reviewed_dir: Path | None = None,
                   include_unreviewed: bool = False,
                   drafts_dir: Path | None = None) -> list[dict]:
    """Combine all data/lumiere/reviewed/<patient_id>_<phase>.json items,
    keeping only approved/edited (dropping rejected). With include_unreviewed,
    also keeps LLM-drafted items still pending expert review (preliminary runs)."""
    reviewed_dir = reviewed_dir or Path(lcfg.LUMIERE_DATA_DIR) / "reviewed"
    keep = ("approved", "edited") + (("pending",) if include_unreviewed else ())
    # reviewed/ rows are stripped copies (no timepoint/facts_used), but the image
    # lookup below needs both — backfill from the matching draft by id. Without this
    # every question resolves to "no image" and the models run text-only.
    drafts = {}
    for dpath in sorted((drafts_dir or Path(lcfg.LUMIERE_DATA_DIR) / "drafts").glob("*.json")):
        for d in json.loads(dpath.read_text()):
            drafts[d["id"]] = d
    items = []
    for fpath in sorted(reviewed_dir.glob("*.json")):
        data = json.loads(fpath.read_text())
        rows = data if isinstance(data, list) else [data]
        for row in rows:
            if row.get("review_status") in keep:
                draft = drafts.get(row["id"], {})
                for key in ("timepoint", "facts_used", "image_timepoints", "image_files", "image_labels", "image_dir",
                            "forecast", "scoring", "ordered_options", "tcm_rule"):
                    if key not in row and key in draft:
                        row[key] = draft[key]
                items.append(row)
    return items


def build_lumiere_cases(items: list[dict], n_cases: int | None = None,
                          min_phases: int = 2, shuffle_options: bool = True,
                          image_note: str | None = None,
                          counterfactual_pairs: dict[str, dict] | None = None) -> list[dict]:
    """Groups reviewed items by patient_id (the genuine chain key) into cases
    in the exact shape CausalChainEvaluator/data_loader.build_cases() uses.

    counterfactual_pairs (2026-09-23, step-4 non-grounding test): patient_id ->
    {"partner": partner_patient_id, ...} (see tools/build_lumiere_counterfactual_pairs.py).
    When set, every question's IMAGE (only) is resolved from the partner's own rendered
    slices instead of the patient's own — the stem, options, chain context, and image
    labels are untouched, so only the pixels the model actually sees change. Applied to
    all phases (no per-phase restriction) per the 2026-09-23 scoping decision."""
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(item["patient_id"], []).append(item)

    by_patient_phase: dict[tuple[str, str], dict] = {}
    if counterfactual_pairs:
        for item in items:
            by_patient_phase[(item["patient_id"], item["clinical_phase"])] = item

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
                forecast = q.get("scoring") == "forecast"   # PJRF v4: no "correct" option, scored by Brier score
                if not (3 <= len(options) <= 5) or (not forecast and q["correct_answer"] not in options):
                    continue  # ingest-time validation per plan
                correct = q["correct_answer"]
                if shuffle_options and not q.get("ordered_options"):
                    options, correct = _shuffle_options(options, correct, q["id"])

                image_path, image_dir = _image_path_for(q), _image_dir_for(q)
                cf_partner = None
                if counterfactual_pairs:
                    entry = counterfactual_pairs.get(patient_id, {})
                    # v3 pairs: one donor per patient; v4 pairs: one donor per (patient, phase)
                    partner_id = (entry.get("partner_by_phase", {}).get(phase_abbr) if "partner_by_phase" in entry
                                  else entry.get("partner"))
                    partner_q = by_patient_phase.get((partner_id, q["clinical_phase"])) if partner_id else None
                    if partner_q is not None:
                        image_path, image_dir = _image_path_for(partner_q), _image_dir_for(partner_q)
                        cf_partner = partner_id
                    elif q.get("image_files") != []:   # text-only v4 items (PJRF, TCM) have no image to swap
                        print(f"WARNING: no counterfactual partner image for "
                              f"{patient_id}/{q['clinical_phase']} — using own image.")

                phase_qs.append({
                    "id": q["id"],
                    "question": q["question"],
                    "options": options,
                    "correct_answer": correct,
                    "correct_answer_text": q["correct_answer_text"],
                    "task_label": q["task_label"],
                    "grounding_terms": _grounding_terms_for(q["task_label"]),
                    "chain_grounding_terms": [],
                    "_image_path": image_path,
                    "_image_dir": image_dir,
                    "_image_labels": _image_labels_for(q),  # original patient's own labels — see docstring
                    "_image_note": image_note,
                    "_counterfactual_partner": cf_partner,
                    **{k: q[k] for k in ("scoring", "forecast", "tcm_rule", "ordered_options") if k in q},
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


def load_lumiere(n_cases: int | None = None, min_phases: int = 2,
                 include_unreviewed: bool = False, item_set: str = lcfg.DEFAULT_ITEM_SET,
                 counterfactual_images: bool = False,
                 **kwargs) -> list[dict]:
    spec = lcfg.ITEM_SETS[item_set]
    items = merge_reviewed(Path(spec["dir"]) / "reviewed", include_unreviewed=include_unreviewed,
                           drafts_dir=Path(spec["dir"]) / "drafts")
    note = lcfg.IMAGE_ORIENTATION_NOTE if spec["orientation_note"] else None

    cf_pairs = None
    if counterfactual_images:
        pairs_path = Path(spec["dir"]) / "counterfactual_pairs.json"
        if not pairs_path.exists():
            raise FileNotFoundError(
                f"--counterfactual-images requires {pairs_path} — run "
                "`python -m tools.build_lumiere_counterfactual_pairs` first.")
        cf_pairs = json.loads(pairs_path.read_text())

    return build_lumiere_cases(items, n_cases=n_cases, min_phases=min_phases, image_note=note,
                               counterfactual_pairs=cf_pairs)
