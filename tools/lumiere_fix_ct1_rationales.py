"""
One-off data fix, follow-up to lumiere_fix_ct1_misread.py: the drafter also worded
the `ct1` (contrast-enhanced T1) -> "CT" misread in ~20 AIA distractor rationales
in item-specific ways. Rewrites just those phrases (reviewer-facing text only; no
question, option or answer changes). PET-CT / CT-angiography mentions are correct
and left alone. Applies to drafts/ and reviewed/. Idempotent; asserts every rewrite
finds its text in drafts/ on the first run.

Usage: python -m tools.lumiere_fix_ct1_rationales [--dry-run]
"""
import argparse
import json
from pathlib import Path

import config.lumiere as lcfg

CE = "contrast-enhanced T1"
# (item id, old phrase, new phrase)
REWRITES = [
    ("Patient-004_AIA", "T1-weighted and CT sequences were available", f"T1-weighted and {CE} sequences were available"),
    ("Patient-008_AIA", "CT was not mentioned", f"{CE} was not mentioned"),
    ("Patient-018_AIA", "it omits CT and FLAIR", f"it omits {CE} and FLAIR"),
    ("Patient-019_AIA", "'ct1' (CT)", f"'ct1' ({CE})"),
    ("Patient-022_AIA", "(MRS), CT, and FLAIR", f"(MRS), {CE}, and FLAIR"),
    ("Patient-022_AIA", "CT and FLAIR are omitted", f"{CE} and FLAIR are omitted"),
    ("Patient-023_AIA", " in addition to CTnot CT alone", ", not CT alone"),
    ("Patient-030_AIA", "CT was available but not listed", f"{CE} was available but not listed"),
    ("Patient-033_AIA", " in addition to CTnot CT alone", ", not CT alone"),
    ("Patient-035_AIA", "the facts document CT (not CT angiography)", f"the facts document {CE} (ct1), not CT angiography,"),
    ("Patient-041_AIA", "CT and FLAIR sequences that were actually available", f"{CE} and FLAIR sequences that were actually available"),
    ("Patient-048_AIA", "the available modality was CT (ct1)", f"the available modality was {CE} (ct1)"),
    ("Patient-049_AIA", "the patient had CT rather than SWI", f"the patient had {CE} rather than SWI"),
    ("Patient-049_AIA", "CT was present instead of PWI", f"{CE} was present instead of PWI"),
    ("Patient-065_AIA", "'ct1' (CT)", f"'ct1' ({CE})"),
    ("Patient-067_AIA", "CT1 (not standard CT alone) was the computed tomography modality present", f"ct1 ({CE}, not CT) was the modality present"),
    ("Patient-071_AIA", "CT1 (not just CT) was the specific modality used", f"ct1 ({CE}, not CT) was the specific modality used"),
    ("Patient-072_AIA", "the patient had CT instead", f"the patient had {CE} instead"),
    ("Patient-085_AIA", "CT was available but not listed", f"{CE} was available but not listed"),
    ("Patient-091_AIA", " in addition to CTnot CT alone", ", not CT alone"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    base = Path(lcfg.LUMIERE_DATA_DIR)
    changed = 0
    for sub in ("drafts", "reviewed"):
        for f in sorted((base / sub).glob("Patient-*.json")):
            items = json.loads(f.read_text())
            dirty = False
            for it in items:
                for iid, old, new in REWRITES:
                    if it["id"] == iid and old in it.get("distractor_rationale", ""):
                        it["distractor_rationale"] = it["distractor_rationale"].replace(old, new)
                        dirty = True
            if dirty:
                changed += 1
                if not args.dry_run:
                    f.write_text(json.dumps(items, indent=2))
    # sanity: after a real run every rewrite's old phrase must be gone from drafts/
    if not args.dry_run:
        left = []
        for f in sorted((base / "drafts").glob("Patient-*.json")):
            for it in json.loads(f.read_text()):
                for iid, old, _ in REWRITES:
                    if it["id"] == iid and old in it.get("distractor_rationale", ""):
                        left.append((iid, old))
        assert not left, f"rewrites left unapplied: {left}"
    print(f"{'Would change' if args.dry_run else 'Changed'} {changed} file(s)")


if __name__ == "__main__":
    main()
