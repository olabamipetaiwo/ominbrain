"""
Leak rules for LUMIERE items: what a question stem / option may NOT state, per phase.

The chain design only works if each phase's answer has to come from the images or from the
model's OWN earlier answers. v2 drafts broke this: later stems were self-contained vignettes that
restated earlier phases' answers (DSCR stems gave LIL's exact % volume change, TCM stems named the
RANO rating, some PJRF stems gave the survival outright) — see tools/audit_stem_leakage.py.

Allowed in any stem: patient id, timepoint ids, non-imaging clinical facts (age, sex, IDH/MGMT,
extent of resection, treatment protocol, time since radiotherapy).
Banned, per phase:
  LIL  stem:          the % volume change, follow-up-only regions, direction of change (its own answer).
  DSCR stem:          LIL's answer (the % volume change, lesion regions) and any RANO label. The expert
                      rater's own report findings ARE allowed (T2/FLAIR progression, new lesions, lesion
                      measurements): they are DSCR's evidence, not an earlier phase's answer, and the rating
                      is often not derivable from the rendered CT1 slice without them.
  PJRF stem:          the above + the survival duration (its own answer).
  TCM  stem:          the above.
  PJRF/TCM options:   imaging findings and RANO labels (options must differ by prognosis / action,
                      not restate the disease state). PJRF options may give survival durations.
Rule-based -> a lower bound on paraphrased leaks; used both as the drafter's retry check and by the audit.
"""

from __future__ import annotations

import re

RANO_LABELS = ("complete response", "partial response", "stable disease", "progressive disease")
DIRECTION_RE = re.compile(r"\b(increas\w*|decreas\w*|grow\w*|growth|shrink\w*|shrank|reduc\w*|resolution|resolved|"
                          r"enlarg\w*|expan\w*|regress\w*|progress\w*)\b", re.I)
PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
MEASURE_RE = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:mm³|mm3|mm\^3|cm³|cm3|cc|ml|mm|cm)(?![a-z])", re.I)
DURATION_RE = re.compile(r"(?<![-\w])(\d{1,3})\s*(weeks?|months?)\b", re.I)   # "93 weeks", not "week-066"

STEM_BANNED_IMAGING = ("PJRF", "TCM")
OPTION_CHECKED = ("PJRF", "TCM")


def _regions(facts: dict) -> tuple[set[str], set[str]]:
    lil = facts["phase_facts"].get("LIL", {})
    base = {r.lower() for r in lil.get("baseline", {}).get("regions", {}).values()}
    follow = {r.lower() for r in lil.get("followup", {}).get("regions", {}).values()}
    return base, follow


def _has_pct(text: str, pct: float | None) -> bool:
    return pct is not None and any(abs(float(m) - abs(pct)) <= 1.0 for m in PCT_RE.findall(text))


def imaging_findings(text: str, facts: dict) -> list[str]:
    """Imaging findings / disease state stated in `text` (what LIL/DSCR are supposed to produce)."""
    low = text.lower()
    base, follow = _regions(facts)
    out = []
    if PCT_RE.search(text):
        out.append("percentage")
    if MEASURE_RE.search(text):
        out.append("measurement")
    if m := DIRECTION_RE.search(text):
        out.append(f"direction '{m.group(0)}'")
    out += [f"region '{r}'" for r in sorted(base | follow) if r in low]
    out += [f"RANO label '{lab}'" for lab in RANO_LABELS if lab in low]
    return out


def survival_stated(text: str, facts: dict) -> bool:
    weeks = (facts["phase_facts"].get("PJRF") or {}).get("survival_weeks")
    if weeks is None:
        return False
    for n, unit in DURATION_RE.findall(text):
        n = int(n)
        if unit.lower().startswith("week") and n == int(weeks):
            return True
        if unit.lower().startswith("month") and abs(n - weeks / 4.345) <= 1:
            return True
    return False


def find_leaks(phase: str, stem: str, options: dict, facts: dict) -> list[str]:
    """Reasons this item violates the v3 leak rules (empty list = clean)."""
    reasons = []
    if phase == "LIL":
        base, follow = _regions(facts)
        if _has_pct(stem, facts["phase_facts"]["LIL"].get("volume_change_pct")):
            reasons.append("stem: % volume change")
        reasons += [f"stem: follow-up region '{r}'" for r in sorted(follow - base) if r in stem.lower()]
        if m := DIRECTION_RE.search(stem):
            reasons.append(f"stem: direction '{m.group(0)}'")
    if phase in STEM_BANNED_IMAGING:
        reasons += [f"stem: {r}" for r in imaging_findings(stem, facts)]
    if phase == "DSCR":
        reasons += [f"stem: {r}" for r in imaging_findings(stem, facts)
                    if r.startswith(("region", "RANO label"))]
        if _has_pct(stem, facts["phase_facts"]["LIL"].get("volume_change_pct")):
            reasons.append("stem: LIL % volume change")
    if phase == "PJRF" and survival_stated(stem, facts):
        reasons.append("stem: survival duration")
    if phase in OPTION_CHECKED:
        for k, v in sorted(options.items()):
            reasons += [f"option {k}: {r}" for r in imaging_findings(v, facts)]
    return reasons
