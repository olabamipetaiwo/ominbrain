"""
Audit how much of each LUMIERE item's answer is already given away by its question stem.

Two kinds of leak, checked per item against the patient's ground-truth facts (data/lumiere/facts/):
  - self leak:     the stem states this item's own answer (e.g. PJRF stem says "survived 93 weeks").
  - upstream leak: the stem states an EARLIER phase's answer (e.g. TCM stem says "progressive disease",
                   DSCR stem restates LIL's volume change). Upstream leaks cut the causal chain: a model
                   that got the earlier phase wrong is handed the right answer anyway.
Plus a fact-free check: a "stem-overlap guesser" that picks the option sharing the most content words
with the stem, never looking at the image. Accuracy well above 25% means the text alone points to the answer.

Rule-based (regex/string match) so it is reproducible; it undercounts paraphrased leaks (lower bound).
Read-only; safe on a login node.

Usage
-----
python -m tools.audit_stem_leakage
python -m tools.audit_stem_leakage --out-prefix results/lumiere_stem_leakage
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import config
from config import lumiere as lcfg
from src.lumiere_leakage import find_leaks
from src.lumiere_loader import load_lumiere

RANO_LABELS = ["complete response", "partial response", "stable disease", "progressive disease"]
DIRECTION_RE = re.compile(r"\b(increas\w*|decreas\w*|grow\w*|growth|shrink\w*|shrank|reduc\w*|resolution|resolved|"
                          r"enlarg\w*|expan\w*|regress\w*|progress\w*)\b", re.I)
PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
WEEKS_RE = re.compile(r"(?<![-\w])(\d{1,3})\s*weeks?\b", re.I)   # "93 weeks", not timepoint ids like "week-066"
STOP = set("""a an the and or of in to at with for on by from as is was were be been this that these which what
most best its their his her she he patient glioblastoma week weeks""".split())


def _facts(patient_id: str, item_set: str = lcfg.DEFAULT_ITEM_SET) -> dict:
    return json.loads((Path(lcfg.ITEM_SETS[item_set]["facts_dir"]) / f"{patient_id}.json").read_text())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP}


def _has_pct(stem: str, pct: float | None) -> bool:
    return pct is not None and any(abs(float(m) - abs(pct)) <= 1.0 for m in PCT_RE.findall(stem))


def _new_followup_regions(lil: dict) -> list[str]:
    """Follow-up lesion regions that were NOT already a baseline region (a stem may legitimately give baseline location)."""
    base = {r.lower() for r in lil["baseline"].get("regions", {}).values()}
    return sorted({r.lower() for r in lil["followup"].get("regions", {}).values()} - base)


def _overlap_guess(stem: str, options: dict) -> str:
    sw = _words(stem)
    return max(sorted(options), key=lambda k: len(_words(options[k]) & sw) / max(1, len(_words(options[k]))))


def audit_item(phase: str, q: dict, facts: dict) -> dict:
    stem = q["question"]
    low = stem.lower()
    pf = facts["phase_facts"]
    pct = pf.get("LIL", {}).get("volume_change_pct")
    rano = (pf.get("DSCR") or {}).get("rating_label", "").lower()
    survival = (pf.get("PJRF") or {}).get("survival_weeks")

    row = {"patient": facts["patient_id"], "phase": phase,
           "self_leak": False, "upstream_leak": False, "reasons": []}

    def flag(kind: str, reason: str):
        row[kind] = True
        row["reasons"].append(reason)

    if phase == "LIL":
        if _has_pct(stem, pct):
            flag("self_leak", "volume % change")
        for r in _new_followup_regions(pf["LIL"]):
            if r in low:
                flag("self_leak", f"follow-up region '{r}'")
        if DIRECTION_RE.search(stem):
            flag("self_leak", "direction of change")
    else:
        if phase in ("DSCR", "PJRF", "TCM"):
            if _has_pct(stem, pct):
                flag("upstream_leak", "LIL volume % change")
            elif DIRECTION_RE.search(stem):
                flag("upstream_leak", "LIL direction of change")
        if phase == "DSCR" and rano and rano in low:
            flag("self_leak", f"RANO label '{rano}'")
        if phase in ("PJRF", "TCM") and rano and rano in low:
            flag("upstream_leak", f"DSCR label '{rano}'")
        if phase == "PJRF" and survival is not None and any(int(w) == int(survival) for w in WEEKS_RE.findall(stem)):
            flag("self_leak", f"survival {survival} weeks")

    row["overlap_guess_correct"] = _overlap_guess(stem, q["options"]) == q["correct_answer"]
    # stricter v3 rules (src/lumiere_leakage.py): also checks options and any imaging finding in later stems
    row["v3_rule_violation"] = bool(find_leaks(phase, stem, q["options"], facts))
    row["reasons"] = "; ".join(row["reasons"])
    return row


def main():
    ap = argparse.ArgumentParser(description="Audit LUMIERE question stems for answer leakage")
    ap.add_argument("--item-set", choices=sorted(lcfg.ITEM_SETS), default=lcfg.DEFAULT_ITEM_SET)
    ap.add_argument("--out-prefix", type=Path, default=None,
                    help="default: results/lumiere_stem_leakage (v2) or results/lumiere_stem_leakage_<set>")
    args = ap.parse_args()
    if args.out_prefix is None:
        suffix = "" if args.item_set == lcfg.DEFAULT_ITEM_SET else f"_{args.item_set}"
        args.out_prefix = Path(f"results/lumiere_stem_leakage{suffix}")

    cases = load_lumiere(include_unreviewed=True, item_set=args.item_set)
    rows = []
    for case in cases:
        facts = _facts(case["id"], args.item_set)
        for phase in config.PHASES:
            for q in case["phases"].get(phase, []):
                rows.append(audit_item(phase, q, facts))

    agg = defaultdict(lambda: defaultdict(int))
    for r in rows:
        a = agg[r["phase"]]
        a["n"] += 1
        a["self"] += r["self_leak"]
        a["up"] += r["upstream_leak"]
        a["any"] += r["self_leak"] or r["upstream_leak"]
        a["guess"] += r["overlap_guess_correct"]
        a["v3"] += r["v3_rule_violation"]

    def pct(k, n):
        return f"{k}/{n} ({k / n:.0%})" if n else "—"

    lines = [f"# LUMIERE stem-leakage audit, item set {args.item_set} (rule-based lower bound)", "",
             "Self leak = stem states this item's answer. Upstream leak = stem states an earlier phase's answer.",
             "Overlap guesser = pick the option with most content words shared with the stem (no image; chance = 25%).",
             "v3-rule violation = src/lumiere_leakage.find_leaks (stricter: also options, any imaging finding).", "",
             "| Phase | n | Self leak | Upstream leak | Any leak | Overlap-guesser acc | v3-rule violation |",
             "|---|---|---|---|---|---|---|"]
    for ph in config.PHASES:
        a = agg[ph]
        lines.append(f"| {ph} | {a['n']} | {pct(a['self'], a['n'])} | {pct(a['up'], a['n'])} | "
                     f"{pct(a['any'], a['n'])} | {pct(a['guess'], a['n'])} | {pct(a['v3'], a['n'])} |")
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
