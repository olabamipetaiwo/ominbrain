"""
TCM label-lookup analysis (replaces the ad hoc regex check logged in paper/update.md, 2026-09-23 x14).

Read-only on results/ and the v3 item set; CPU-only, safe on a login node.

The TCM drafter prompt makes the correct treatment follow from the patient's disease course, so TCM may be
answerable by looking up the upstream DSCR label. This tool measures that with a fixed, inspectable rule set
(no model, no free-text judgement):

  1. key      Action class of every TCM option, from its OPENING words only (first 10; rationale clauses
              mention "recurrence", "second-line" etc. and would mislead a whole-text match). Classes:
              escalate / continue / stop (incl. hold, defer) / other (steroid, imaging-only, dose change).
              Reports how often the DSCR key predicts the TCM key's class (PD -> escalate; SD/PR/CR ->
              continue) and in how many items the key's class is UNIQUE among the four options (only
              then does the class alone fix the letter).
  2. own      Own-image (v3 nogate) run: TCM accuracy split by whether the model's OWN DSCR answer was
              correct. Exact two-sided Fisher p. Descriptive and confounded (patients answered correctly
              on DSCR may be easier throughout); the causal evidence is the gating-causality experiment.
  3. follow   Gating-causality run, PD-keyed patients only: share of TCM answers in the escalate class under
              correct / forced-wrong / absent DSCR context (how far the model follows the injected label).

Usage
-----
python -m tools.lumiere_tcm_lookup      # prints, writes results/lumiere_tcm_lookup.{json,md}
"""

import glob
import json
import re
from math import comb
from pathlib import Path

from src.lumiere_labels import canonical_answer_text
from src.lumiere_loader import load_lumiere

MODELS = ["MedGemma-4B", "Gemma-3-12B", "Gemma-3-27B", "Llama-4-Scout"]
N_LEAD_WORDS = 10

# First match wins, applied to the option's opening words. Order matters: "escalate" cues are checked first
# because escalation options can begin "Arrange ... re-resection" or "Refer for ... second-line".
RULES = [
    ("escalate", r"second-line|salvage|re-?resection|radiosurgery|stereotactic|re-?irradiation|hypofractionated|"
                 r"clinical trial|dose-intensified|bevacizumab|lomustine|tumor board|escalate"),
    ("stop",     r"discontinue|suspend|pause|\bhold\b|best supportive|palliative|defer systemic|transition to a? ?(?:best|palliative)"),
    ("continue", r"\bcontinue\b|\bmaintain\b|maintenance|proceed with adjuvant|extend the adjuvant"),
]
PD = "Progressive disease"


def action_class(option_text: str) -> str:
    lead = " ".join(option_text.replace(",", " ").split()[:N_LEAD_WORDS]).lower()
    for name, pat in RULES:
        if re.search(pat, lead):
            return name
    return "other"


def predicted_class(dscr_label: str) -> str:
    return "escalate" if dscr_label == PD else "continue"


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact two-sided Fisher p for [[a, b], [c, d]] (sum of tables no more likely than the observed one)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    denom = comb(n, c1)
    pobs = comb(r1, a) * comb(r2, c) / denom
    tot = 0.0
    for x in range(max(0, c1 - r2), min(r1, c1) + 1):
        p = comb(r1, x) * comb(r2, c1 - x) / denom
        if p <= pobs * (1 + 1e-9):
            tot += p
    return min(1.0, tot)


def latest(pattern: str, need: str = "raw_results.json") -> Path | None:
    runs = [Path(p) for p in sorted(glob.glob(pattern)) if (Path(p) / need).exists()]
    return runs[-1] if runs else None


def key_analysis(cases: list[dict]) -> tuple[list[str], dict, dict]:
    rows, ids = [], []
    for c in cases:
        d, t = c["phases"]["DSCR"][0], c["phases"]["TCM"][0]
        classes = {l: action_class(x) for l, x in t["options"].items()}
        key_cls = classes[t["correct_answer"]]
        rows.append({"id": c["id"], "dscr": canonical_answer_text(d["correct_answer_text"]), "key_class": key_cls,
                     "pred_class": predicted_class(canonical_answer_text(d["correct_answer_text"])),
                     "unique": sum(v == key_cls for v in classes.values()) == 1,
                     "classes": classes})
        ids.append(c["id"])
    n = len(rows)
    hit = sum(r["key_class"] == r["pred_class"] for r in rows)
    pd_rows = [r for r in rows if r["dscr"] == PD]
    non_rows = [r for r in rows if r["dscr"] != PD]
    stats = {
        "n": n,
        "agree": hit,
        "pd_n": len(pd_rows), "pd_escalate": sum(r["key_class"] == "escalate" for r in pd_rows),
        "nonpd_n": len(non_rows), "nonpd_continue": sum(r["key_class"] == "continue" for r in non_rows),
        "class_unique": sum(r["unique"] for r in rows),
        "key_class_counts": {k: sum(r["key_class"] == k for r in rows) for k in ("escalate", "continue", "stop", "other")},
        "disagree_ids": [r["id"] for r in rows if r["key_class"] != r["pred_class"]],
    }
    return ids, stats, {r["id"]: r for r in rows}


def own_split(model: str) -> dict | None:
    d = latest(f"results/lumiere_{model}_v3_nogate_2*")
    if d is None:
        return None
    a = b = c_ = d_ = 0   # a: DSCR ok & TCM ok, b: DSCR ok & TCM wrong, c: DSCR wrong & TCM ok, d: both wrong
    for case in json.loads((d / "raw_results.json").read_text()):
        ph = case["phases"]
        if "DSCR" not in ph or "TCM" not in ph or not ph["DSCR"]["questions"] or not ph["TCM"]["questions"]:
            continue
        dc, tc = bool(ph["DSCR"]["questions"][0]["correct"]), bool(ph["TCM"]["questions"][0]["correct"])
        if dc:
            a, b = a + tc, b + (not tc)
        else:
            c_, d_ = c_ + tc, d_ + (not tc)
    return {"run": str(d), "dscr_ok_tcm_ok": a, "dscr_ok": a + b, "dscr_wrong_tcm_ok": c_, "dscr_wrong": c_ + d_,
            "fisher_p": fisher_two_sided(a, b, c_, d_)}


def follow_label(model: str, rows: dict) -> dict | None:
    d = latest(f"results/lumiere_gatingcausality_{model}_*", need="summary.json")
    if d is None:
        return None
    out = {"run": str(d)}
    for cond in ("correct", "incorrect", "absent"):
        k = n = 0
        for case in json.loads((d / "raw_results.json").read_text()):
            r = rows.get(case["case_id"])
            if r is None or r["dscr"] != PD or "TCM" not in case["phases"]:
                continue
            ans = case["phases"]["TCM"][cond]["model_answer"]
            if not ans or ans not in r["classes"]:
                continue   # parse failure: excluded from this share, counted in the note
            n += 1
            k += r["classes"][ans] == "escalate"
        out[cond] = {"escalate": k, "n": n}
    return out


def main() -> None:
    cases = load_lumiere(n_cases=None, min_phases=2, item_set="v3", include_unreviewed=True)
    cases = [c for c in cases if "DSCR" in c["phases"] and "TCM" in c["phases"]]
    _, ks, rows = key_analysis(cases)

    L = ["# TCM label-lookup analysis (v3, 52 patients)", "",
         "Read-only, CPU-only; rule set in `tools/lumiere_tcm_lookup.py` (`RULES`, opening "
         f"{N_LEAD_WORDS} words of each option). Fisher p exact two-sided, uncorrected.", "",
         "## 1. Does the DSCR key predict the TCM key's action class?", "",
         f"- DSCR key -> TCM key class (PD -> escalate; SD/PR/CR -> continue): **{ks['agree']}/{ks['n']}** "
         f"(PD {ks['pd_escalate']}/{ks['pd_n']} escalate; non-PD {ks['nonpd_continue']}/{ks['nonpd_n']} continue).",
         f"- Key class counts: {ks['key_class_counts']}.",
         f"- Key's class is unique among the four options in **{ks['class_unique']}/{ks['n']}** items "
         "(only there does the class alone fix the letter).",
         f"- Disagreements: {', '.join(ks['disagree_ids']) or 'none'}.", "",
         "## 2. TCM accuracy by whether the model's own DSCR answer was correct (own-image v3 run)", "",
         "Descriptive and confounded: patients answered correctly on DSCR may be easier throughout.", "",
         "| Model | TCM correct, own DSCR correct | TCM correct, own DSCR wrong | Fisher p |", "|---|---|---|---|"]
    res = {"key": ks, "own": {}, "follow": {}}
    for m in MODELS:
        o = own_split(m)
        res["own"][m] = o
        if o:
            L.append(f"| {m} | {o['dscr_ok_tcm_ok']}/{o['dscr_ok']} | {o['dscr_wrong_tcm_ok']}/{o['dscr_wrong']} | {o['fisher_p']:.3g} |")
        else:
            L.append(f"| {m} | run missing | | |")
    L += ["", "## 3. Following the injected DSCR label (PD-keyed patients; gating-causality TCM answers)", "",
          "Share of TCM answers in the escalate class. Parse failures excluded from the denominator.", "",
          "| Model | correct context (PD) | forced-wrong context | absent context |", "|---|---|---|---|"]
    for m in MODELS:
        f = follow_label(m, rows)
        res["follow"][m] = f
        if f:
            L.append(f"| {m} | {f['correct']['escalate']}/{f['correct']['n']} | {f['incorrect']['escalate']}/{f['incorrect']['n']} "
                     f"| {f['absent']['escalate']}/{f['absent']['n']} |")
        else:
            L.append(f"| {m} | run missing | | |")
    md = "\n".join(L) + "\n"
    print(md)
    Path("results/lumiere_tcm_lookup.md").write_text(md)
    Path("results/lumiere_tcm_lookup.json").write_text(json.dumps(res, indent=2))
    print("Saved -> results/lumiere_tcm_lookup.{md,json}")


if __name__ == "__main__":
    main()
