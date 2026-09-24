"""
LUMIERE v4 item set: answerable from the model-visible inputs by construction (paper/review.md, concern 1).

v3 asked questions the supplied evidence cannot answer (whole-lesion volume change from one slice, expert RANO
ratings that rest on T2/FLAIR progression, an AIA question with one fixed answer, PJRF scored against realised
survival, TCM without a defined rule). v4 replaces every key with one that is a stated function of the inputs:

  AIA   Which MRI sequence is shown?                   key = the sequence rendered (balanced 4-way, image only).
  LIL   Which hemisphere / anterior-posterior half     key = position of the largest tumour-core component on the
        holds the main tumour mass on this slice?      displayed slice (src/lumiere_measure.py).
  DSCR  RANO enhancement category from the displayed   key = category computed from the bidimensional products of the
        post-op baseline, nadir and follow-up slices.  enhancing lesion on those slices (RANO thresholds). The
                                                       expert rating is recorded per item but is NOT the key: only
                                                       ~47% of expert ratings are reproducible from enhancement.
  PJRF  Probability of death within 52 weeks of this   forecast: prediction time, information and horizon are
        scan, given stated clinical facts.             stated; scored with the Brier score against the recorded
                                                       outcome, not by picking a "correct" bin.
  TCM   Next management step under a stated rule.      key = rule(RANO category, weeks since chemoradiotherapy):
                                                       non-PD -> continue; PD within the 12-week post-radiotherapy
                                                       window -> repeat MRI before changing therapy; PD beyond it ->
                                                       change therapy. A documented treatment is NOT available in
                                                       LUMIERE, so this is a guideline-rule recommendation.

Selection and every random choice use fixed seeds and never look at model output. Nothing here is clinician
validated; that review remains outstanding (README of the paper, Limitations).
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import config.lumiere as lcfg
from src import lumiere_facts as lf
from src.lumiere_measure import cache_path, imaging_rano_label, lil_eligible

V4_DIR = Path(lcfg.LUMIERE_DATA_DIR) / "v4"
SEED = 20260925
CRT_END_WEEK = 10      # assumed: chemoradiotherapy ends ~10 weeks after surgery (Stupp: RT starts ~4 wk post-op, 6-wk course)
WINDOW_WEEKS = 12      # RANO 2010: progression within 12 weeks of completing radiotherapy needs confirmation
MIN_X = 2              # weeks since chemoradiotherapy ended: earlier scans are still on treatment
EARLY_MAX_X = 10       # PD in the post-radiotherapy window: X in [MIN_X, EARLY_MAX_X]; the 11-13 band is left out
LATE_MIN_X = 14        # PD beyond the window: X >= LATE_MIN_X (a margin of 2 weeks either side of 12)
HORIZON_WEEKS = 52
QUOTA = {"F": 20, "E": 20, "C": 28}          # target patients per TCM class
NON_PD_QUOTA = {"partial response": 7, "stable disease": 12, "complete response": 9}   # C = 28
SEQUENCES = ["t1", "ct1", "t2", "flair"]
SEQUENCE_TEXT = {"t1": "T1-weighted, before contrast", "ct1": "T1-weighted, after gadolinium contrast",
                 "t2": "T2-weighted", "flair": "FLAIR (fluid-attenuated inversion recovery)"}
RANO_TEXT = {"PD": "progressive disease", "SD": "stable disease", "PR": "partial response", "CR": "complete response"}
RESECTION = {"CRET": "complete", "PRET": "partial"}
PJRF_BINS = [("Below 20%", 0.10), ("20% to 40%", 0.30), ("40% to 60%", 0.50), ("Above 60%", 0.80)]
TCM_OPTIONS = {
    "continue": "Continue adjuvant temozolomide unchanged and plan the next surveillance MRI in 8 to 12 weeks.",
    "confirm": "Continue adjuvant temozolomide for now and repeat the MRI in 4 to 8 weeks before changing therapy.",
    "escalate": "Change therapy now: bring re-resection, second-line treatment or a clinical trial to tumor board.",
    "stop": "Stop tumor-directed treatment and move to best supportive care with no further imaging plan.",
}


def _w(tp: str) -> int:
    return int(tp.split("-")[1])


# ------------------------------------------------------------------ candidates

def load_measure(pid: str, tp: str) -> dict | None:
    p = cache_path(pid, tp)
    return json.loads(p.read_text()) if p.exists() else None


def tcm_class(is_pd: bool, x: int) -> str | None:
    """Rule class for a follow-up, or None when the timepoint falls in the excluded margin."""
    if x < MIN_X:
        return None
    if not is_pd:
        return "C"
    if x <= EARLY_MAX_X:
        return "F"
    if x >= LATE_MIN_X:
        return "E"
    return None


def enumerate_candidates() -> dict[str, dict]:
    """patient -> {ref, surgery_week, extent, candidates: [...]} for first-line follow-ups only."""
    rano, demo, comp = lf.load_rano(), lf.load_demographics(), lf.load_completeness()
    survival = demo.set_index("Patient")["Survival time (weeks)"]
    out = {}
    for pid in sorted(rano.Patient.unique()):
        imaged = set(lf._patient_timepoints(pid, comp))
        rows = lf.extract_dscr_facts(pid, rano)
        posts = sorted([r["timepoint_id"] for r in rows if r["rating_code"] == "Post-Op"], key=lambda t: (_w(t), t))
        if not posts or posts[0] not in imaged:
            continue                      # the first post-operative scan must be imaged: it is the RANO reference
        ref = posts[0]
        later_surgery = [p for p in posts[1:] if _w(p) > _w(ref)]
        limit = _w(later_surgery[0]) if later_surgery else 10 ** 6
        rationale = next((r["rationale"] for r in rows if r["timepoint_id"] == ref), None)
        s = survival.get(pid)
        s = None if pd.isna(s) or str(s).strip() == "na" else int(float(s))
        cands, undetermined = [], []
        rated = sorted([r["timepoint_id"] for r in rows if r["is_response_rating"] and r["timepoint_id"] in imaged
                        and _w(ref) < _w(r["timepoint_id"]) < limit], key=lambda t: (_w(t), t))
        bp = lambda m: (m["enh"]["bp_mm2"] if m.get("enh") else 0.0)
        for r in rows:
            tp = r["timepoint_id"]
            if tp not in rated or not r["is_response_rating"]:
                continue
            x = (_w(tp) - _w(ref)) - CRT_END_WEEK
            m_ref, m_fu = load_measure(pid, ref), load_measure(pid, tp)
            earlier = [t for t in rated if _w(t) < _w(tp)]
            ms = {t: load_measure(pid, t) for t in earlier}
            if m_ref is None or m_fu is None or any(m is None for m in ms.values()):
                continue
            # nadir: the earlier scan (post-operative reference included) with the smallest enhancing product
            nadir_tp = min([ref] + earlier, key=lambda t: (bp(m_ref if t == ref else ms[t]), _w(t)))
            m_nad = m_ref if nadir_tp == ref else ms[nadir_tp]
            rule = imaging_rano_label(bp(m_ref), bp(m_fu), bp(m_nad))
            expert = RANO_TEXT[r["rating_code"]]
            if rule is None:                # enhancement cannot decide: no DSCR item, so no candidate
                undetermined.append({"expert": expert, "x": x})
                continue
            cands.append({"tp": tp, "code": r["rating_code"], "expert": expert, "rule": rule,
                          "nadir_tp": nadir_tp, "bp_nadir": bp(m_nad),
                          "concordant": rule == expert, "x": x, "weeks_since_surgery": _w(tp) - _w(ref),
                          "cls": tcm_class(rule == "progressive disease", x), "bp_ref": bp(m_ref), "bp_fu": bp(m_fu),
                          "lil_ok": lil_eligible(m_fu)[0], "rationale": r["rationale"]})
        if cands:
            out[pid] = {"patient_id": pid, "ref": ref, "extent": RESECTION.get(rationale),
                        "survival_weeks": s, "candidates": cands, "undetermined": undetermined,
                        "demo": demo[demo.Patient == pid].iloc[0].to_dict()}
    return out


def needed_timepoints() -> list[tuple[str, str]]:
    """(patient, timepoint) pairs whose slice measurements the candidate enumeration needs: the first post-operative
    reference and every rated, imaged follow-up before any second surgery."""
    rano, comp = lf.load_rano(), lf.load_completeness()
    todo = []
    for pid in sorted(rano.Patient.unique()):
        imaged = set(lf._patient_timepoints(pid, comp))
        rows = lf.extract_dscr_facts(pid, rano)
        posts = sorted([r["timepoint_id"] for r in rows if r["rating_code"] == "Post-Op"], key=lambda t: (_w(t), t))
        if not posts or posts[0] not in imaged:
            continue
        ref = posts[0]
        later = [p for p in posts[1:] if _w(p) > _w(ref)]
        limit = _w(later[0]) if later else 10 ** 6
        todo.append((pid, ref))
        todo += [(pid, r["timepoint_id"]) for r in rows
                 if r["is_response_rating"] and r["timepoint_id"] in imaged and _w(ref) < _w(r["timepoint_id"]) < limit]
    return todo


def measure_all(force: bool = False) -> None:
    """Fill data/lumiere/v4/measurements/ from the remote archive (range reads; cached, so re-runs only fetch the delta)."""
    import zipfile
    import fsspec
    from src.lumiere_measure import load_or_measure
    todo = needed_timepoints()
    print(f"{len(todo)} timepoints", flush=True)
    with fsspec.open(lf._zip_url(), mode="rb") as f, zipfile.ZipFile(f) as zf:
        for i, (pid, tp) in enumerate(todo):
            try:
                load_or_measure(zf, pid, tp, force=force)
            except Exception as e:      # a missing member should not stop the sweep
                print(f"ERR {pid} {tp}: {e}", flush=True)
            if i % 25 == 0:
                print(i, flush=True)


# ------------------------------------------------------------------ selection

def select_cohort(records: dict[str, dict], seed: int = SEED) -> tuple[list[dict], dict]:
    rng = random.Random(seed)
    usable = {pid: [c for c in r["candidates"] if c["cls"]] for pid, r in records.items()}
    usable = {pid: cs for pid, cs in usable.items() if cs}
    pids = sorted(usable)
    rng.shuffle(pids)
    chosen: dict[str, dict] = {}

    def pick(pid: str, cls: str, label: str | None = None) -> dict | None:
        cs = [c for c in usable[pid] if c["cls"] == cls and (label is None or c["rule"] == label)]
        if not cs:
            return None
        cs.sort(key=lambda c: (not c["concordant"], not c["lil_ok"], rng.random()))   # prefer expert-agreeing, LIL-eligible
        return cs[0]

    # scarcest strata first (each patient contributes one follow-up): non-PD labels, then early PD, then late PD
    for label, quota in NON_PD_QUOTA.items():
        for pid in pids:
            if pid in chosen or sum(v["cls"] == "C" and v["rule"] == label for v in chosen.values()) >= quota:
                continue
            if (c := pick(pid, "C", label)):
                chosen[pid] = c
    for cls in ("F", "E"):
        for pid in pids:
            if pid in chosen or sum(v["cls"] == cls for v in chosen.values()) >= QUOTA[cls]:
                continue
            if (c := pick(pid, cls)):
                chosen[pid] = c
    cohort = [{**c, "patient_id": pid} for pid, c in sorted(chosen.items())]

    all_c = [c for r in records.values() for c in r["candidates"]]
    report = {
        "n_patients_with_first_line_candidates": len(records),
        "n_candidate_followups": len(all_c),
        "rule_vs_expert_concordance": {
            "n": len(all_c), "concordant": sum(c["concordant"] for c in all_c),
            "by_expert_label": {lab: {"n": sum(c["expert"] == lab for c in all_c),
                                       "concordant": sum(c["expert"] == lab and c["concordant"] for c in all_c),
                                       "rule_undetermined": sum(c["expert"] == lab and c["rule"] is None for c in all_c)}
                                for lab in RANO_TEXT.values()},
            "confusion_expert_by_rule": {f"{e}|{r}": n for (e, r), n in
                                         sorted(Counter((c["expert"], str(c["rule"])) for c in all_c).items())},
        },
        "n_selected": len(cohort),
        "selected_by_tcm_class": dict(Counter(c["cls"] for c in cohort)),
        "selected_by_rule_label": dict(Counter(c["rule"] for c in cohort)),
        "selected_by_expert_label": dict(Counter(c["expert"] for c in cohort)),
        "selected_expert_agrees": sum(c["concordant"] for c in cohort),
        "n_undetermined_followups": sum(len(r["undetermined"]) for r in records.values()),
        "undetermined_by_expert": dict(Counter(u["expert"] for r in records.values() for u in r["undetermined"])),
        "selected_lil_eligible": sum(c["lil_ok"] for c in cohort),
        "quota": QUOTA, "seed": seed,
    }
    return cohort, report


# ------------------------------------------------------------------ items

def _extent_phrase(extent: str | None) -> str:
    return (f"a {extent} resection of the enhancing tumor" if extent else "surgical resection")


def _clinical_sentence(rec: dict) -> str:
    d = rec["demo"]
    sex = str(d.get("Sex", "")).strip().lower() or "patient"
    age = d.get("Age at surgery (years)")
    mg = str(d.get("MGMT qualitative", "na")).strip().lower()
    idh = str(d.get("IDH (WT: wild type)", "na")).strip()
    mg_t = {"methylated": "MGMT promoter methylated", "not methylated": "MGMT promoter not methylated"}.get(
        mg, "MGMT status not available")
    idh_t = {"WT": "IDH wild type"}.get(idh, "IDH status not available")
    try:
        who = f"{int(float(age))}-year-old {sex}"
    except (TypeError, ValueError):
        who = f"adult {sex}"
    return who, mg_t, idh_t


def make_items(rec: dict, ch: dict, aia_seq: str) -> list[dict]:
    pid, ref, fu = rec["patient_id"], rec["ref"], ch["tp"]
    m_ref, m_fu = load_measure(pid, ref), load_measure(pid, fu)
    slices = f"data/lumiere/v4/slices/{pid}"
    base = {"patient_id": pid, "leak_check": [], "needs_expert_judgment": True, "review_status": "pending",
            "image_dir": slices}
    items = []

    # AIA ------------------------------------------------------------------
    items.append({**base, "id": f"{pid}_AIA", "clinical_phase": "Anatomical and Imaging Assessment",
                  "task_label": "Imaging Modality Identification", "timepoint": fu,
                  "question": ("The image is a single axial slice from a brain MRI examination of a patient with glioblastoma "
                              "(skull-stripped and registered to a standard template). Which MRI sequence does this image show?"),
                  "options": {l: SEQUENCE_TEXT[s] for l, s in zip("ABCD", SEQUENCES)},
                  "correct_answer": "ABCD"[SEQUENCES.index(aia_seq)], "correct_answer_text": SEQUENCE_TEXT[aia_seq],
                  "image_files": [f"{fu}_{aia_seq}.png"], "image_labels": None,
                  "facts_used": {"sequence": aia_seq, "timepoint": fu, "key_rule": "sequence rendered"}})

    # LIL ------------------------------------------------------------------
    ok, why = lil_eligible(m_fu)
    if ok:
        core = m_fu["core"]
        key = f"{core['hemisphere'].capitalize()} hemisphere, {core['ap_half']} half"
        opts = {l: f"{h} hemisphere, {a} half" for l, (h, a) in zip("ABCD", [("Right", "anterior"), ("Right", "posterior"),
                                                                             ("Left", "anterior"), ("Left", "posterior")])}
        items.append({**base, "id": f"{pid}_LIL", "clinical_phase": "Lesion Identification and Localization",
                      "task_label": "Lesion Localization", "timepoint": fu,
                      "question": ("The image is an axial slice of a post-contrast T1-weighted brain MRI in radiological "
                                   "convention (the patient's right side is on the left of the image; anterior is at the top). "
                                   "Where is the main tumor region (enhancing tumor, necrosis or resection cavity, not the surrounding "
                                   "edema) on this slice? Divide the brain on this slice into right and left hemispheres at the midline and "
                                   "into anterior and posterior halves at the midpoint of its front-to-back extent."),
                      "options": opts, "correct_answer": next(l for l, t in opts.items() if t == key),
                      "correct_answer_text": key, "image_files": [f"{fu}_core.png"], "image_labels": None,
                      "facts_used": {"core": core, "key_rule": "largest tumour-core component on the displayed slice"}})

    # DSCR -----------------------------------------------------------------
    labels = ["Progressive disease", "Stable disease", "Partial response", "Complete response"]
    key = ch["rule"].capitalize()
    nadir = ch["nadir_tp"]
    dscr_files = [f"{ref}_enh.png"] + ([f"{nadir}_enh.png"] if nadir != ref else []) + [f"{fu}_enh.png"]
    dscr_labels = (["post-operative baseline scan"] + (["scan with the smallest enhancing lesion so far (nadir)"] if nadir != ref else [])
                   + ["follow-up scan"])
    n_img = len(dscr_files)
    items.append({**base, "id": f"{pid}_DSCR", "clinical_phase": "Diagnostic Synthesis and Causal Reasoning",
                  "task_label": "Disease Diagnosis Reasoning", "timepoint": fu,
                  "question": (f"{'Three' if n_img == 3 else 'Two'} post-contrast T1-weighted axial slices of the same patient are shown, each at "
                               "the level of the largest contrast-enhancing lesion on that scan, in time order: "
                               + ("the post-operative baseline scan (image 1), the earlier scan with the smallest enhancing lesion "
                                  "(the nadir, image 2) and the follow-up scan (image 3)" if n_img == 3 else
                                  "the post-operative baseline scan, which is also the nadir (image 1), and the follow-up scan (image 2)")
                               + ". Pixels are 1 mm in the original scan, and a 20 mm scale bar is drawn on each image. Apply the RANO "
                               "enhancement criteria to the enhancing lesion. Measurable means at least 10 mm by 10 mm. Progression is a "
                               "25% or greater increase in the product of the two largest perpendicular diameters relative to the nadir, or a "
                               "new measurable enhancing lesion. Response is judged against the post-operative baseline: partial response is a "
                               "50% or greater decrease, complete response is no remaining measurable enhancing disease, otherwise stable "
                               "disease. T2/FLAIR changes, steroid dose and clinical status are not provided. What is the response "
                               "category at follow-up?"),
                  "options": dict(zip("ABCD", labels)), "correct_answer": "ABCD"[labels.index(key)], "correct_answer_text": key,
                  "image_files": dscr_files, "image_labels": dscr_labels,
                  "facts_used": {"expert_rating": ch["code"], "rule_label": ch["rule"], "concordant": ch["concordant"],
                                 "bp_ref_mm2": ch["bp_ref"], "bp_nadir_mm2": ch["bp_nadir"], "bp_followup_mm2": ch["bp_fu"],
                                 "reference_tp": ref, "nadir_tp": nadir, "followup_tp": fu,
                                 "expert_rationale": ch["rationale"],
                                 "key_rule": "image-derived RANO-style enhancement category (bidimensional products on the "
                                             "displayed slices); the expert rating is recorded, not the key"}})

    # shared clinical context ----------------------------------------------------
    who, mg_t, idh_t = _clinical_sentence(rec)
    wss, x = ch["weeks_since_surgery"], ch["x"]
    history = (f"A {who} with glioblastoma ({mg_t}; {idh_t}) had {_extent_phrase(rec['extent'])} and then standard "
               f"chemoradiotherapy (radiotherapy with concurrent temozolomide), followed by adjuvant temozolomide. No second "
               f"surgery or second-line treatment has been given.")

    # PJRF -----------------------------------------------------------------------
    s = rec["survival_weeks"]
    if s is not None and s > _w(fu):
        y = int(s <= _w(fu) + HORIZON_WEEKS)
        items.append({**base, "id": f"{pid}_PJRF", "clinical_phase": "Prognostic Judgment and Risk Forecasting",
                      "task_label": "Prognostic Factor Analysis", "timepoint": fu,
                      "question": (f"{history} The follow-up MRI is {wss} weeks after surgery and the patient is alive at this time. "
                                   f"Using only the information above and your earlier assessment of this patient, estimate the "
                                   f"probability that the patient will die within {HORIZON_WEEKS} weeks after this scan."),
                      "options": {l: t for l, (t, _) in zip("ABCD", PJRF_BINS)}, "correct_answer": None, "correct_answer_text": "",
                      "scoring": "forecast", "ordered_options": True,
                      "forecast": {"horizon_weeks": HORIZON_WEEKS, "outcome": y,
                                   "bin_midpoints": {l: p for l, (_, p) in zip("ABCD", PJRF_BINS)}},
                      "image_files": [], "image_labels": None,
                      "facts_used": {"survival_weeks": s, "prediction_week": _w(fu), "horizon_weeks": HORIZON_WEEKS,
                                     "time_origin_assumption": "survival time and scan weeks share the surgery-week origin"}})

    # TCM ------------------------------------------------------------------------
    klass = {"C": "continue", "F": "confirm", "E": "escalate"}[ch["cls"]]
    opts = {l: TCM_OPTIONS[k] for l, k in zip("ABCD", ["continue", "confirm", "escalate", "stop"])}
    items.append({**base, "id": f"{pid}_TCM", "clinical_phase": "Therapeutic Cycle Management",
                  "task_label": "Treatment Plan Selection", "timepoint": fu,
                  "question": (f"{history} This MRI is {wss} weeks after surgery; chemoradiotherapy ended about {x} weeks before "
                               f"this scan. Using your earlier assessment of this patient, what is the most appropriate next step?"),
                  "options": opts, "correct_answer": "ABCD"[["continue", "confirm", "escalate", "stop"].index(klass)],
                  "correct_answer_text": TCM_OPTIONS[klass], "image_files": [], "image_labels": None,
                  "tcm_rule": {"rano": ch["rule"], "weeks_since_chemoradiotherapy": x, "class": klass,
                               "rule": "non-PD -> continue; PD and <= 12 weeks after radiotherapy -> repeat MRI first; "
                                       "PD and later -> change therapy (RANO 2010; Stupp schedule assumed)"},
                  "facts_used": {"rano": ch["rule"], "x_weeks": x, "weeks_since_surgery": wss, "assumed_chemoradiotherapy_end_week": CRT_END_WEEK}})
    return items


# ------------------------------------------------------------------ rendering

def render_patient(zf, rec: dict, ch: dict, aia_seq: str, force: bool = False) -> None:
    from src.lumiere_v4_render import render_from_zip
    pid, ref, fu = rec["patient_id"], rec["ref"], ch["tp"]
    m_ref, m_fu = load_measure(pid, ref), load_measure(pid, fu)
    out = V4_DIR / "slices" / pid

    def z_enh(m, other):
        if m.get("enh"):
            return m["enh"]["z"]
        if other.get("enh"):
            return other["enh"]["z"]
        return (m.get("core") or other.get("core") or {"z": 90})["z"]

    jobs = [(ref, "ct1", z_enh(m_ref, m_fu), f"{ref}_enh.png"), (fu, "ct1", z_enh(m_fu, m_ref), f"{fu}_enh.png")]
    if ch["nadir_tp"] != ref:
        m_nad = load_measure(pid, ch["nadir_tp"])
        jobs.append((ch["nadir_tp"], "ct1", z_enh(m_nad, m_fu), f"{ch['nadir_tp']}_enh.png"))
    if m_fu.get("core"):
        jobs.append((fu, "ct1", m_fu["core"]["z"], f"{fu}_core.png"))
    z_aia = (m_fu.get("core") or m_ref.get("core") or {"z": 90})["z"]
    jobs.append((fu, aia_seq, z_aia, f"{fu}_{aia_seq}.png"))
    for tp, seq, z, name in jobs:
        path = out / name
        if path.exists() and not force:
            continue
        if render_from_zip(zf, pid, tp, seq, z, path) is None:
            print(f"  [warn] missing {seq} for {pid}/{tp}")


# ------------------------------------------------------------------ counterfactual pairs

def build_pairs(items_by_patient: dict[str, dict[str, dict]], seed: int = SEED) -> dict:
    """Per phase (AIA, LIL, DSCR) a one-to-one donor assignment where the donor's key differs from the patient's.

    Because the AIA, LIL and DSCR stems contain no patient-specific fact and their option sets always contain every
    possible answer, a donor image never conflicts with the text and the donor's correct answer is always available."""
    from scipy.optimize import linear_sum_assignment
    rng = np.random.default_rng(seed)
    pairs: dict[str, dict] = defaultdict(dict)
    for phase in ("AIA", "LIL", "DSCR"):
        pids = sorted(p for p, it in items_by_patient.items() if phase in it)
        key = {p: items_by_patient[p][phase]["correct_answer_text"] for p in pids}
        # each patient may donate to at most two others (columns are duplicated), which keeps the class-imbalanced
        # DSCR keys matchable while spreading donor use
        # the DSCR stem names how many scans are shown (two or three), so a donor must show the same number
        n_img = {p: len(items_by_patient[p][phase]["image_files"]) for p in pids}
        cost = np.array([[0.0 if key[a] != key[b] and a != b and n_img[a] == n_img[b] else 1e6 for b in pids] * 2
                         for a in pids])
        cost = cost + rng.random(cost.shape) * 1e-3
        rows, cols = linear_sum_assignment(cost)
        for r, c in zip(rows, cols):
            c = c % len(pids)
            if cost[r, c] >= 1e5:
                continue           # no compatible donor left for this patient
            pairs[pids[r]][phase] = {"partner": pids[c], "own_key": key[pids[r]], "donor_key": key[pids[c]]}
    return {p: {"partner_by_phase": {ph: v["partner"] for ph, v in d.items()}, "detail": d} for p, d in pairs.items()}


# ------------------------------------------------------------------ CLI

def build(render: bool = True) -> None:
    records = enumerate_candidates()
    cohort, report = select_cohort(records)
    V4_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED + 1)
    order = [c["patient_id"] for c in cohort]
    rng.shuffle(order)
    aia_seq = {pid: SEQUENCES[i % 4] for i, pid in enumerate(order)}
    for sub in ("drafts", "reviewed", "facts"):
        (V4_DIR / sub).mkdir(exist_ok=True)
    zf_ctx = None
    if render:
        import fsspec, zipfile
        zf_ctx = fsspec.open(lf._zip_url(), mode="rb").open()
        zf = zipfile.ZipFile(zf_ctx)
    by_patient: dict[str, dict[str, dict]] = {}
    for ch in cohort:
        pid = ch["patient_id"]
        items = make_items(records[pid], ch, aia_seq[pid])
        by_patient[pid] = {it["id"].split("_")[-1]: it for it in items}
        (V4_DIR / "drafts" / f"{pid}.json").write_text(json.dumps(items, indent=2, default=str))
        (V4_DIR / "reviewed" / f"{pid}.json").write_text(json.dumps(items, indent=2, default=str))
        (V4_DIR / "facts" / f"{pid}.json").write_text(json.dumps({"patient_id": pid, "selected": ch, "aia_sequence": aia_seq[pid],
                                                                   "record": {k: v for k, v in records[pid].items() if k != "candidates"}},
                                                                  indent=2, default=str))
        if render:
            print(f"rendering {pid}", flush=True)
            render_patient(zf, records[pid], ch, aia_seq[pid])
    pairs = build_pairs(by_patient)
    (V4_DIR / "counterfactual_pairs.json").write_text(json.dumps(pairs, indent=2))
    report["phase_counts"] = {ph: sum(ph in it for it in by_patient.values()) for ph in ("AIA", "LIL", "DSCR", "PJRF", "TCM")}
    report["aia_sequence_counts"] = dict(Counter(aia_seq.values()))
    report["pjrf_outcome_counts"] = dict(Counter(it["PJRF"]["forecast"]["outcome"] for it in by_patient.values() if "PJRF" in it))
    report["lil_key_counts"] = dict(Counter(it["LIL"]["correct_answer_text"] for it in by_patient.values() if "LIL" in it))
    report["dscr_key_counts"] = dict(Counter(it["DSCR"]["correct_answer_text"] for it in by_patient.values()))
    report["tcm_key_counts"] = dict(Counter(it["TCM"]["tcm_rule"]["class"] for it in by_patient.values()))
    report["pairs_built"] = {ph: sum(ph in v["partner_by_phase"] for v in pairs.values()) for ph in ("AIA", "LIL", "DSCR")}
    (V4_DIR / "selection_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the LUMIERE v4 (answerable-by-construction) item set")
    ap.add_argument("--measure", action="store_true", help="measure every needed timepoint from the remote archive, then exit")
    ap.add_argument("--explore", action="store_true", help="print candidate/concordance counts and exit")
    ap.add_argument("--no-render", action="store_true", help="build items and pairs without rendering slices")
    a = ap.parse_args()
    if a.measure:
        measure_all()
    elif a.explore:
        recs = enumerate_candidates()
        cohort, rep = select_cohort(recs)
        print(json.dumps(rep, indent=2))
    else:
        build(render=not a.no_render)
