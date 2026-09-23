"""
Lightweight local Streamlit app for domain-expert review of LLM-drafted
LUMIERE MCQ items (data/lumiere/drafts/<patient_id>.json).

Usage (login node — this is a human-facing form, not compute):
    streamlit run tools/lumiere_review_app.py

Access remotely via SSH port-forward:
    ssh -L 8501:localhost:8501 <hipergator-host>
then open http://localhost:8501 in a local browser.

Writes decisions immediately to data/lumiere/reviewed/<patient_id>.json
(one file per patient, list of all its phase items with review_status set).
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import config.lumiere as lcfg

DRAFTS_DIR = Path(lcfg.LUMIERE_DATA_DIR) / "drafts"
REVIEWED_DIR = Path(lcfg.LUMIERE_DATA_DIR) / "reviewed"
SLICES_DIR = Path(lcfg.LUMIERE_DATA_DIR) / "slices"
REVIEWED_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="LUMIERE Chain Review", layout="wide")


def _load_patient_items(patient_id: str) -> list[dict]:
    reviewed_path = REVIEWED_DIR / f"{patient_id}.json"
    if reviewed_path.exists():
        return json.loads(reviewed_path.read_text())
    draft_path = DRAFTS_DIR / f"{patient_id}.json"
    return json.loads(draft_path.read_text())


def _save_patient_items(patient_id: str, items: list[dict]) -> None:
    (REVIEWED_DIR / f"{patient_id}.json").write_text(json.dumps(items, indent=2, default=str))


def _progress_counts(all_patients: list[str]) -> dict[str, int]:
    counts = {"approved": 0, "edited": 0, "rejected": 0, "pending": 0}
    for pid in all_patients:
        for item in _load_patient_items(pid):
            counts[item.get("review_status", "pending")] = counts.get(item.get("review_status", "pending"), 0) + 1
    return counts


patient_ids = sorted(p.stem for p in DRAFTS_DIR.glob("Patient-*.json"))
if not patient_ids:
    st.error(f"No drafted items found in {DRAFTS_DIR}. Run src/lumiere_drafter.py first.")
    st.stop()

st.sidebar.title("LUMIERE Chain Review")
counts = _progress_counts(patient_ids)
st.sidebar.metric("Approved", counts["approved"])
st.sidebar.metric("Edited", counts["edited"])
st.sidebar.metric("Rejected", counts["rejected"])
st.sidebar.metric("Pending", counts["pending"])

patient_id = st.sidebar.selectbox("Patient", patient_ids)
items = _load_patient_items(patient_id)

# surface flagged items first (needs_expert_judgment, or low distractor confidence)
flagged_first = sorted(items, key=lambda q: not (q.get("needs_expert_judgment") or
                                                   q.get("distractor_confidence") == "low"))

phase_labels = [f"{q['clinical_phase']} ({q.get('review_status', 'pending')})"
                + (" ⚠" if q.get("needs_expert_judgment") or q.get("distractor_confidence") == "low" else "")
                for q in flagged_first]
idx = st.sidebar.radio("Phase / item", range(len(flagged_first)), format_func=lambda i: phase_labels[i])
item = flagged_first[idx]
item_pos = items.index(item)

st.header(f"{patient_id} — {item['clinical_phase']}")

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Drafted item")
    question = st.text_area("Question", item["question"], height=100)
    options = dict(item["options"])
    new_options = {}
    for letter, text in options.items():
        new_options[letter] = st.text_input(f"Option {letter}", text)
    answer = st.selectbox("Correct answer", list(new_options.keys()),
                           index=list(new_options.keys()).index(item["correct_answer"])
                           if item["correct_answer"] in new_options else 0)
    st.text(f"Distractor rationale: {item.get('distractor_rationale', '')}")
    st.text(f"Distractor confidence: {item.get('distractor_confidence', '?')}")
    notes = st.text_area("Review notes", item.get("review_notes", ""))

def _lil_item_for(patient_id: str, items: list[dict]) -> dict | None:
    return next((q for q in items if q["clinical_phase"] == "Lesion Identification and Localization"), None)


def _slice_timepoints_for(item: dict, items: list[dict]) -> list[tuple[str, str]]:
    """Returns [(label, timepoint_id), ...] to display for this item. LIL and
    DSCR are comparisons between baseline and follow-up — show both slices so
    the reviewer can visually confirm the volume/location change, not just
    the endpoint. Everything else (AIA/PJRF/TCM) is a single timepoint."""
    phase = item["clinical_phase"]
    if phase == "Lesion Identification and Localization":
        facts = item.get("facts_used", {})
        return [("baseline", facts.get("baseline", {}).get("timepoint_id")),
                ("follow-up", facts.get("followup", {}).get("timepoint_id"))]
    if phase == "Diagnostic Synthesis and Causal Reasoning":
        lil = _lil_item_for(item["patient_id"], items)
        if lil:
            facts = lil.get("facts_used", {})
            return [("baseline", facts.get("baseline", {}).get("timepoint_id")),
                    ("follow-up", facts.get("followup", {}).get("timepoint_id"))]
    return [("timepoint", item.get("timepoint"))]


with col2:
    st.subheader("Underlying facts (provenance)")
    st.json(item.get("facts_used", {}))
    for label, tp in _slice_timepoints_for(item, items):
        if not tp:
            continue
        slice_path = SLICES_DIR / patient_id / f"{tp}.png"
        if slice_path.exists():
            st.image(str(slice_path), caption=f"{label}: {patient_id} / {tp}")
        else:
            st.info(f"No rendered slice available for {label} ({tp}).")

c1, c2, c3 = st.columns(3)
if c1.button("Approve"):
    item["review_status"] = "approved"
    item["review_notes"] = notes
    items[item_pos] = item
    _save_patient_items(patient_id, items)
    st.rerun()

if c2.button("Save edits & Approve"):
    item["question"] = question
    item["options"] = new_options
    item["correct_answer"] = answer
    item["correct_answer_text"] = new_options[answer]
    item["review_status"] = "edited"
    item["review_notes"] = notes
    items[item_pos] = item
    _save_patient_items(patient_id, items)
    st.rerun()

reject_reason = st.text_input("Reject reason (required to reject)")
if c3.button("Reject") and reject_reason:
    item["review_status"] = "rejected"
    item["review_notes"] = reject_reason
    items[item_pos] = item
    _save_patient_items(patient_id, items)
    st.rerun()
