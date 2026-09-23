"""
Compile the counterfactual-image substitution runs (Section 7's 4th grounding check)
into the flip-rate / truth-tracking numbers §8 reports.

Reads each model's own-image v3 nogate run and its matching _cf_v3_nogate run, and for
every (patient, phase) pair with a valid answer in both:
  - flipped:        model_answer differs between own-image and counterfactual-image runs
  - tracks_truth:    for flipped LIL/DSCR items only, whether the counterfactual answer's
                     content (volume-change direction / RANO label) matches what the
                     SUBSTITUTED patient's own facts actually support, per
                     data/lumiere/v3/counterfactual_pairs.json -- distinguishes a flip
                     driven by genuine image content from one driven by decoding
                     variance alone (a truth-tracking flip is diagnostic; a
                     non-truth-tracking flip is consistent with noise).

Read-only on results/ and data/lumiere/v3/; safe on a login node.

Usage
-----
python -m tools.compile_lumiere_counterfactual
"""

import json
import re
from pathlib import Path

RANO_WORDS = {
    "PD": "progressive disease",
    "SD": "stable disease",
    "PR": "partial response",
    "CR": "complete response",
}
DIRECTION_WORDS = {"up": "increase", "down": "decrease"}

OWN_RUNS = {
    "MedGemma-4B": "results/lumiere_MedGemma-4B_v3_nogate_20260922_174448",
    "Gemma-3-12B": "results/lumiere_Gemma-3-12B_v3_nogate_20260922_184248",
    "Gemma-3-27B": "results/lumiere_Gemma-3-27B_v3_nogate_20260922_191649",
    "Llama-4-Scout": "results/lumiere_Llama-4-Scout_v3_nogate_20260922_192315",
}
CF_RUNS = {
    "MedGemma-4B": "results/lumiere_MedGemma-4B_cf_v3_nogate_20260923_024904",
    "Gemma-3-12B": "results/lumiere_Gemma-3-12B_cf_v3_nogate_20260923_034723",
    "Gemma-3-27B": "results/lumiere_Gemma-3-27B_cf_v3_nogate_20260923_051250",
    "Llama-4-Scout": "results/lumiere_Llama-4-Scout_cf_v3_nogate_20260923_055624",
}
PAIRS_PATH = "data/lumiere/v3/counterfactual_pairs.json"
PHASES = ["AIA", "LIL", "DSCR", "PJRF", "TCM"]


def _own_answers(run_dir: str) -> dict:
    cases = json.load(open(Path(run_dir) / "raw_results.json"))
    out = {}
    for case in cases:
        for phase, pdata in case["phases"].items():
            for q in pdata["questions"]:
                out[(case["case_id"], phase)] = q
    return out


# 2026-09-23 fix: the old check was `"increase" in t` / `"decrease" in t`, which (a) missed the drafter's
# most common phrasings ("volume increasing/decreasing", "stable", "reduction"), silently dropping those flipped
# answers from the truth-tracking denominator (only 73 of 95 flipped LIL/DSCR items were "checkable"), and
# (b) misread options that mention the opposite word about a sub-compartment. Now: read the clause about the
# TOTAL volume, else any volume/burden clause, else the first direction word. Validated against the correct
# option of every patient's LIL item (see tools/lumiere_reviewer_stats.py, which asserts it).
_DIR_TOKEN_RE = re.compile(r"\b(increas\w*|expan\w*|grow\w*|enlarg\w*|decreas\w*|reduc\w*|shrink\w*|shrank|"
                           r"declin\w*|stable|stabili\w*|unchang\w*)", re.I)
_CLAUSE_SPLIT_RE = re.compile(r"[;,]|\b(?:while|whereas|despite|driven|due|with|reflecting)\b")


def _direction_word(text: str) -> str | None:
    """Direction of the TOTAL lesion-volume change in an LIL option: 'increase' | 'decrease' | 'stable' | None."""
    clauses = _CLAUSE_SPLIT_RE.split(text)

    def first(cs):
        for c in cs:
            m = _DIR_TOKEN_RE.search(c)
            if m:
                return m.group(1).lower()
        return None

    cand = ([c for c in clauses if re.search(r"\b(total|overall)\b", c, re.I)]
            or [c for c in clauses if re.search(r"volum|burden", c, re.I)])
    w = first(cand) or first(clauses)
    if not w:
        return None
    if w.startswith(("increas", "expan", "grow", "enlarg")):
        return "increase"
    if w.startswith(("decreas", "reduc", "shrink", "shrank", "declin")):
        return "decrease"
    return "stable"


def truth_label(patient_id: str, phase: str, item_set: str = "v3") -> str | None:
    """The patient's own truth label as WORDED in their correct option (direction for LIL, RANO for DSCR).
    Read from the reviewed item, not from pairs.json's sign of the % change: a +0.3% patient is worded 'stable'."""
    items = json.load(open(Path(f"data/lumiere/{item_set}/reviewed/{patient_id}.json")))
    text = next(q["correct_answer_text"] for q in items if q["id"] == f"{patient_id}_{phase}")
    return _direction_word(text) if phase == "LIL" else _rano_word(text)


def _rano_word(text: str) -> str | None:
    t = text.lower()
    for label in RANO_WORDS.values():
        if label in t:
            return label
    return None


def compile_model(model: str, pairs: dict) -> dict:
    own = _own_answers(OWN_RUNS[model])
    cf = _own_answers(CF_RUNS[model])

    per_phase = {p: {"n": 0, "flipped": 0} for p in PHASES}
    truth_track = {"LIL": {"flipped_checkable": 0, "tracks_truth": 0},
                    "DSCR": {"flipped_checkable": 0, "tracks_truth": 0}}

    for (case_id, phase), cf_q in cf.items():
        own_q = own.get((case_id, phase))
        if own_q is None or own_q.get("model_answer") is None or cf_q.get("model_answer") is None:
            continue
        per_phase[phase]["n"] += 1
        flipped = own_q["model_answer_text"] != cf_q["model_answer_text"]
        if not flipped:
            continue
        per_phase[phase]["flipped"] += 1

        if phase == "LIL":
            partner_dir = truth_label(pairs[case_id]["partner"], "LIL")
            cf_dir = _direction_word(cf_q["model_answer_text"])
            if partner_dir and cf_dir:
                truth_track["LIL"]["flipped_checkable"] += 1
                if cf_dir == partner_dir:
                    truth_track["LIL"]["tracks_truth"] += 1
        elif phase == "DSCR":
            partner_rano = truth_label(pairs[case_id]["partner"], "DSCR")
            cf_rano = _rano_word(cf_q["model_answer_text"])
            if partner_rano and cf_rano:
                truth_track["DSCR"]["flipped_checkable"] += 1
                if cf_rano == partner_rano:
                    truth_track["DSCR"]["tracks_truth"] += 1

    return {"per_phase": per_phase, "truth_track": truth_track}


def main():
    pairs = json.load(open(PAIRS_PATH))
    results = {model: compile_model(model, pairs) for model in OWN_RUNS}

    print(f"{'Model':<15} " + " ".join(f"{p:>12s}" for p in PHASES))
    for model, r in results.items():
        cells = []
        for p in PHASES:
            d = r["per_phase"][p]
            rate = f"{100*d['flipped']/d['n']:.0f}%" if d["n"] else "n/a"
            cells.append(f"{rate:>5s}(n={d['n']:<3d})")
        print(f"{model:<15} " + " ".join(f"{c:>12s}" for c in cells))

    print()
    print(f"{'Model':<15} {'LIL flip truth-track':>25s} {'DSCR flip truth-track':>25s}")
    for model, r in results.items():
        lil = r["truth_track"]["LIL"]
        dscr = r["truth_track"]["DSCR"]
        lil_s = (f"{lil['tracks_truth']}/{lil['flipped_checkable']}"
                 f" ({100*lil['tracks_truth']/lil['flipped_checkable']:.0f}%)"
                 if lil["flipped_checkable"] else "n/a")
        dscr_s = (f"{dscr['tracks_truth']}/{dscr['flipped_checkable']}"
                  f" ({100*dscr['tracks_truth']/dscr['flipped_checkable']:.0f}%)"
                  if dscr["flipped_checkable"] else "n/a")
        print(f"{model:<15} {lil_s:>25s} {dscr_s:>25s}")

    json.dump(results, open("results/lumiere_counterfactual_summary.json", "w"), indent=2)
    print("\nSaved -> results/lumiere_counterfactual_summary.json")


if __name__ == "__main__":
    main()
