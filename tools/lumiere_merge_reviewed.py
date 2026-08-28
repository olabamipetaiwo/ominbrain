"""
Assembles the final LUMIERE chain dataset from expert-reviewed items.

Reads data/lumiere/reviewed/<patient_id>.json (written by
tools/lumiere_review_app.py), keeps approved/edited items, and writes:
  - data/lumiere/lumiere_chains_final.json  (flat list, ready for src/lumiere_loader.py)
  - data/lumiere/rejected_log.json          (for methods-section transparency)
"""

from __future__ import annotations

import json
from pathlib import Path

import config.lumiere as lcfg
from src.lumiere_loader import merge_reviewed


def main() -> None:
    reviewed_dir = Path(lcfg.LUMIERE_DATA_DIR) / "reviewed"
    approved = merge_reviewed(reviewed_dir)

    rejected = []
    for fpath in sorted(reviewed_dir.glob("*.json")):
        for item in json.loads(fpath.read_text()):
            if item.get("review_status") == "rejected":
                rejected.append({
                    "id": item["id"], "patient_id": item["patient_id"],
                    "clinical_phase": item["clinical_phase"],
                    "reason": item.get("review_notes", ""),
                })

    out_dir = Path(lcfg.LUMIERE_DATA_DIR)
    (out_dir / "lumiere_chains_final.json").write_text(json.dumps(approved, indent=2, default=str))
    (out_dir / "rejected_log.json").write_text(json.dumps(rejected, indent=2, default=str))

    n_patients = len({item["patient_id"] for item in approved})
    print(f"Approved: {len(approved)} items across {n_patients} patients -> "
          f"{out_dir / 'lumiere_chains_final.json'}")
    print(f"Rejected: {len(rejected)} items -> {out_dir / 'rejected_log.json'}")


if __name__ == "__main__":
    main()
