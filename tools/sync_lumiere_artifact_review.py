"""
Pulls reviewer decisions out of a LUMIERE review HTML file into
data/lumiere/reviewed/<patient_id>.json, in the same shape
tools/lumiere_review_app.py already produces — so
src/lumiere_loader.merge_reviewed() and tools/lumiere_merge_reviewed.py work
identically regardless of which review interface was used.

tools/build_lumiere_review_artifact.py now builds a fully standalone HTML
file (autosaves to the reviewer's browser via localStorage, no account or
server needed — see that module's docstring for why the earlier
claude.ai-Artifact-based version was replaced). The reviewer opens it
locally, works through the queue, and periodically/finally clicks
"Download review file" to produce an updated .html they send back (email,
shared drive, etc.). Run this script directly against whatever file they
send:
    python -m tools.sync_lumiere_artifact_review --html-file <path>

Safe to re-run any time (e.g. to check progress mid-review, against a
partial download) — idempotent overwrite per patient, not an append.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import config.lumiere as lcfg


def extract_state(html_path: Path) -> dict:
    html = html_path.read_text(encoding="utf-8")
    m = re.search(
        r'<script id="lumiere-data" type="application/json">(.*?)</script>',
        html, re.DOTALL,
    )
    if not m:
        raise ValueError(f"Could not find the lumiere-data script tag in {html_path}")
    return json.loads(m.group(1))


def to_reviewed_records(state: dict) -> dict[str, list[dict]]:
    """Groups items by patient_id, recomputing correct_answer_text from the
    FINAL (possibly reviewer-edited) options/answer — never trust a stale
    stored value, since the artifact's edit UI doesn't track it live."""
    by_patient: dict[str, list[dict]] = defaultdict(list)
    for it in state["items"]:
        options = it["options"]
        answer = it["correct_answer"]
        record = {
            "id": it["id"],
            "patient_id": it["patient_id"],
            "clinical_phase": it["clinical_phase"],
            "task_label": it["task_label"],
            "question": it["question"],
            "options": options,
            "correct_answer": answer,
            "correct_answer_text": options.get(answer, ""),
            "review_status": it["review_status"],
            "reviewer": it.get("reviewer", ""),
            "review_notes": it.get("review_notes", ""),
        }
        by_patient[it["patient_id"]].append(record)
    return by_patient


def sync(html_path: Path, out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(lcfg.LUMIERE_DATA_DIR) / "reviewed"
    out_dir.mkdir(parents=True, exist_ok=True)

    state = extract_state(html_path)
    by_patient = to_reviewed_records(state)

    counts = defaultdict(int)
    for patient_id, records in by_patient.items():
        (out_dir / f"{patient_id}.json").write_text(json.dumps(records, indent=2))
        for r in records:
            counts[r["review_status"]] += 1

    total = sum(counts.values())
    print(f"Synced {len(by_patient)} patients, {total} items -> {out_dir}")
    print(f"  approved: {counts['approved']}  edited: {counts['edited']}  "
          f"rejected: {counts['rejected']}  pending: {counts['pending']}")
    if counts["pending"]:
        print(f"  NOTE: {counts['pending']} items still pending — review may not be complete.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Sync LUMIERE artifact review state to data/lumiere/reviewed/")
    p.add_argument("--html-file", type=Path, required=True,
                    help="Path to the artifact HTML saved by Artifact(action='read')")
    args = p.parse_args()
    sync(args.html_file)
