"""Generate alternative, constraint-valid donor-assignment files for the real-model robustness run (T-R16).

Re-runs the dataset's own ``build_pairs`` (distinct key, no self, matching scan count, <=2 recipients per donor)
under fresh seeds and writes each DISTINCT full assignment to ``data/lumiere/v4/alt_pairs/assignment_<k>.json``
(identical schema to ``counterfactual_pairs.json``). A swap-condition run reads one via the ``LUMIERE_V4_PAIRS``
environment variable, e.g.

  LUMIERE_V4_PAIRS=data/lumiere/v4/alt_pairs/assignment_0.json \
    python run_lumiere_v4.py --model Llama-4-Scout --conditions own,text,swap --phases DSCR

Usage:
  python -m tools.lumiere_v4_altpairs --n 5                       # 5 alternative assignments, all imaging phases
No model is called; this only draws assignments.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.lumiere_v4 import build_pairs
from tools.lumiere_v4_donor_validation import _items_by_patient, PAIRS


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5, help="how many distinct alternative assignments to write")
    ap.add_argument("--phases", nargs="+", default=["AIA", "LIL", "DSCR"])
    ap.add_argument("--outdir", default="data/lumiere/v4/alt_pairs")
    ap.add_argument("--max-seeds", type=int, default=5000)
    args = ap.parse_args()

    ibp = _items_by_patient()
    orig = {ph: frozenset((c, v["detail"][ph]["partner"]) for c, v in PAIRS.items() if ph in v.get("detail", {}))
            for ph in args.phases}
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    seen: set = set()
    manifest = []
    s = 0
    while len(manifest) < args.n and s < args.max_seeds:
        seed = 10_000 + s
        s += 1
        pr = build_pairs(ibp, seed=seed)
        keys = {ph: frozenset((c, pr[c]["detail"][ph]["partner"]) for c in pr if ph in pr[c].get("detail", {}))
                for ph in args.phases}
        full = tuple(keys[ph] for ph in args.phases)
        if full in seen or all(keys[ph] == orig[ph] for ph in args.phases):
            continue                                   # skip duplicates and the exact original
        seen.add(full)
        idx = len(manifest)
        (outdir / f"assignment_{idx}.json").write_text(json.dumps(pr, indent=1))
        manifest.append({"index": idx, "seed": seed,
                         "coverage": {ph: len(keys[ph]) for ph in args.phases},
                         "differs_from_original": {ph: keys[ph] != orig[ph] for ph in args.phases}})
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {len(manifest)} alternative assignment files to {outdir} (from {s} seeds)")
    for m in manifest:
        print(" ", m)


if __name__ == "__main__":
    main()
