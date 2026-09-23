"""
Fact-check models' stated evidence (visual_grounding + reasoning) against LUMIERE ground truth, to test
"right answer for wrong reasons" directly instead of via the self-consistency probe.

Each checkable claim in a model's evidence text is sorted into:
  - copied:      also present in text the model was shown (this stem, its options, or the prior-chain block:
                 earlier stems, earlier model answers, earlier visual_grounding) — not evidence of reading the image.
  - supported:   not in the shown text, and consistent with data/lumiere/facts/ — plausible image-derived evidence.
  - contradicts: hemisphere claim that disagrees with the segmentation's hemisphere. Reported as its own label
                 (laterality_flip), NOT as wrong reasons: slices are rendered in radiological orientation (FSL MNI
                 grid + np.rot90 in src/lumiere_facts.py puts patient-right on screen-left) and the prompt never states
                 the convention, so a model reading screen-left as "left" is locating the lesion, under the other convention.
  - fabricated:  a measurement (%, mm, mm³, ...) that is neither in the shown text nor within 2% of any fact number
                 (a precise volume cannot be read off a 2D slice).
Claims checked: hemisphere (left/right + anatomy word), measurements with units.

Measurements that are RANO criteria thresholds (20/25/40/50% near "RANO"/"criteria"/"defined") are skipped.

Per item: wrong_reasons = fabricated; laterality_flip = contradicts (and nothing fabricated); copied_only = has claims, all copied; supported = >=1
supported claim and no wrong-reason claim. Reported for correct AND incorrect answers — if wrong-reason rates
are similar in both, stated evidence is not what drives correctness.

Rule-based, reproducible; misses paraphrased claims (lower bound).
Read-only on results/; safe on a login node.

Usage
-----
python -m tools.audit_reasoning_facts                       # latest non-gated run per model
python -m tools.audit_reasoning_facts --include-textonly   # also the text-only ablation runs
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import config
from config import lumiere as lcfg
from src.lumiere_loader import load_lumiere
from tools.compile_lumiere_results import latest_runs

HEMI_RE = re.compile(r"\b(left|right)(?:-sided|\s+(?:cerebral|hemisphere|hemispheric|frontal|parietal|temporal|"
                     r"occipital|insula\w*|thalam\w*|basal|lateral|cerebell\w*|side|periventricular|corona|"
                     r"cingulate|precentral|postcentral|supramarginal|angular|lobe|white))", re.I)
MEAS_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|mm³|mm3|mm\^3|cm³|cm3|cc|ml|mm|cm)(?![a-z])", re.I)
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
RANO_THRESHOLDS = {20.0, 25.0, 40.0, 50.0}
RANO_CONTEXT_RE = re.compile(r"rano|criteri|defin|threshold|≥|>=", re.I)


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _fact_numbers(facts: dict) -> list[float]:
    """Every number anywhere in the patient's fact file (volumes, % change, survival, age, DSCR rationale mm...)."""
    return [_num(m) for m in NUM_RE.findall(json.dumps(facts)) if _num(m) > 0]


def _truth_hemis(facts: dict) -> set[str]:
    lil = facts["phase_facts"].get("LIL", {})
    regions = [r for tp in ("baseline", "followup") for r in lil.get(tp, {}).get("regions", {}).values()]
    return {h for r in regions for h in ("left", "right") if h in r.lower()}


def _shown_text(q: dict, prior: list[dict], options: dict) -> str:
    parts = [q["question"], *options.get(q["id"], {}).values()]
    for p in prior:
        parts += [p["question"], p.get("model_answer_text") or "", str(p.get("visual_grounding") or "")]
    return " ".join(parts).lower()


def _in_shown(value: float, shown_nums: list[float]) -> bool:
    return any(abs(value - s) <= max(0.05, 0.005 * s) for s in shown_nums)


def check_item(q: dict, prior: list[dict], facts: dict, options: dict) -> dict:
    evidence = f"{q.get('visual_grounding') or ''} {q.get('reasoning') or ''}"
    shown = _shown_text(q, prior, options)
    shown_nums = [_num(m) for m in NUM_RE.findall(shown)]
    fact_nums = _fact_numbers(facts)
    truth = _truth_hemis(facts)
    c = defaultdict(int)

    for m in HEMI_RE.finditer(evidence):
        h = m.group(1).lower()
        if re.search(rf"\b{h}\b", shown):
            c["copied"] += 1
        elif not truth:
            c["unverifiable"] += 1
        elif h in truth:
            c["supported"] += 1
        else:
            c["contradicts"] += 1

    for m in MEAS_RE.finditer(evidence):
        v = _num(m.group(1))
        if (m.group(2) == "%" and v in RANO_THRESHOLDS
                and RANO_CONTEXT_RE.search(evidence[max(0, m.start() - 120):m.start()])):
            continue
        if _in_shown(v, shown_nums):
            c["copied"] += 1
        elif any(abs(v - f) <= 0.02 * f for f in fact_nums):
            c["supported"] += 1
        else:
            c["fabricated"] += 1

    checkable = c["copied"] + c["supported"] + c["contradicts"] + c["fabricated"]
    if c["fabricated"]:
        label = "wrong_reasons"
    elif c["contradicts"]:
        label = "laterality_flip"
    elif c["supported"]:
        label = "supported"
    elif checkable:
        label = "copied_only"
    else:
        label = "no_claims"
    return {**c, "label": label}


def _item_set_of(model: str) -> str:
    """run_lumiere.py appends _<set> to non-default item sets' run names (e.g. Gemma-3-12B_v3)."""
    return next((s for s in lcfg.ITEM_SETS if s != lcfg.DEFAULT_ITEM_SET and f"_{s}" in model), lcfg.DEFAULT_ITEM_SET)


def audit_run(run_dir: Path, model: str, options: dict) -> list[dict]:
    rows = []
    facts_dir = Path(lcfg.ITEM_SETS[_item_set_of(model)]["facts_dir"])
    for case in json.loads((run_dir / "raw_results.json").read_text()):
        facts = json.loads((facts_dir / f"{case['case_id']}.json").read_text())
        prior: list[dict] = []
        for phase in config.PHASES:
            pdata = case["phases"].get(phase)
            if not pdata or pdata.get("gated_out"):
                continue
            for q in pdata["questions"]:
                if q.get("parse_error"):
                    continue
                r = check_item(q, prior, facts, options)
                rows.append({"model": model, "patient": case["case_id"], "phase": phase,
                             "correct": bool(q["correct"]), **{k: r.get(k, 0) for k in
                             ("copied", "supported", "contradicts", "fabricated", "unverifiable")}, "label": r["label"]})
            prior += [{"question": q["question"], "model_answer_text": q.get("model_answer_text"),
                       "visual_grounding": q.get("visual_grounding")} for q in pdata["questions"]]
    return rows


def main():
    ap = argparse.ArgumentParser(description="Fact-check LUMIERE model evidence against ground truth")
    ap.add_argument("--results-dir", type=Path, default=Path("results"))
    ap.add_argument("--include-textonly", action="store_true")
    ap.add_argument("--out-prefix", type=Path, default=Path("results/lumiere_reasoning_facts"))
    args = ap.parse_args()

    runs = {m: p for m, p in latest_runs(args.results_dir).items()
            if "(no gating)" in m and (args.include_textonly or "_textonly" not in m)}
    # raw_results.json doesn't store options; the model saw them, so they count as shown text
    options = {s: {q["id"]: q["options"] for c in load_lumiere(include_unreviewed=True, item_set=s)
                   for qs in c["phases"].values() for q in qs}
               for s in {_item_set_of(m) for m in runs}}
    rows = [r for m, p in sorted(runs.items())
            for r in audit_run(p, m.replace(" (no gating)", ""), options[_item_set_of(m)])]

    labels = ["supported", "copied_only", "laterality_flip", "wrong_reasons", "no_claims"]
    agg = defaultdict(lambda: defaultdict(int))
    for r in rows:
        k = (r["model"], r["phase"], r["correct"])
        agg[k]["n"] += 1
        agg[k][r["label"]] += 1

    def cell(a):
        n = a["n"]
        return " / ".join(f"{a[l] / n:.0%}" if n else "—" for l in labels) + f" (n={n})"

    lines = ["# LUMIERE evidence fact-check (rule-based lower bound; non-gated runs)", "",
             "Each cell: supported / copied-only / laterality-flip / wrong-reasons / no-claims, as % of answers. "
             "wrong-reasons = a measurement in neither the prompt nor the facts; laterality-flip = hemisphere opposite "
             "to segmentation (radiological display convention, see module docstring).", "",
             "| Model | Phase | Correct answers | Incorrect answers |", "|---|---|---|---|"]
    for model in sorted({r["model"] for r in rows}):
        for ph in config.PHASES:
            lines.append(f"| {model} | {ph} | {cell(agg[(model, ph, True)])} | {cell(agg[(model, ph, False)])} |")
    md = "\n".join(lines) + "\n"
    print(md)

    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    args.out_prefix.with_suffix(".md").write_text(md)
    with open(args.out_prefix.with_suffix(".csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved → {args.out_prefix.with_suffix('.md')}, {args.out_prefix.with_suffix('.csv')}")


if __name__ == "__main__":
    main()
