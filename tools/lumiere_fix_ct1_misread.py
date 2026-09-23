"""
One-off data fix: the LLM drafter read LUMIERE's `ct1` (contrast-enhanced T1) as
"CT", so every AIA item's correct option/rationale lists a CT sequence for an
MRI-only dataset. Rewrites the phrase in data/lumiere/drafts/ and
data/lumiere/reviewed/ (all string fields). Idempotent. Back up first.

Usage: python -m tools.lumiere_fix_ct1_misread [--dry-run]
"""
import argparse
import json
from pathlib import Path

import config.lumiere as lcfg

REPLACEMENTS = [
    ("T1-weighted, CT, T2-weighted, and FLAIR",
     "T1-weighted, contrast-enhanced T1-weighted, T2-weighted, and FLAIR"),
    ("T1, CT, T2, and FLAIR", "T1, contrast-enhanced T1, T2, and FLAIR"),
]


def _fix(obj):
    if isinstance(obj, str):
        for old, new in REPLACEMENTS:
            obj = obj.replace(old, new)
        return obj
    if isinstance(obj, list):
        return [_fix(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _fix(v) for k, v in obj.items()}
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    changed = 0
    for sub in ("drafts", "reviewed"):
        for f in sorted((Path(lcfg.LUMIERE_DATA_DIR) / sub).glob("*.json")):
            old = json.loads(f.read_text())
            new = _fix(old)
            if new != old:
                changed += 1
                if not args.dry_run:
                    f.write_text(json.dumps(new, indent=2))
    print(f"{'Would change' if args.dry_run else 'Changed'} {changed} file(s)")


if __name__ == "__main__":
    main()
