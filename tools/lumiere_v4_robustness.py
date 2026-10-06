"""Real-model donor-swap robustness across alternative valid assignments (T-R16).

For each alternative donor assignment produced by ``tools.lumiere_v4_altpairs`` and run under
``run_lumiere_v4.py --results-dir results/robustness`` (folders
``results/robustness/lumiere_v4_<model>_alt<k>_*``), recompute the paper's own E2 donor gain and the donor-key
permutation p on the ACTUAL model answers. This tests whether the real empirical finding is stable across genuinely
distinct valid assignments, which synthetic predictors cannot establish.

  python -m tools.lumiere_v4_robustness --model Llama-4-Scout --phases DSCR
  python -m tools.lumiere_v4_robustness --model Gemini-3.6-Flash --phases AIA LIL
Writes results/lumiere_v4_robustness_<model>.json. No model is called; this is pure re-analysis.
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

import tools.lumiere_v4_stats as st
import tools.lumiere_v4_supplement as sup


def recs_from_folder(folder: str) -> dict:
    recs = {}
    for r in json.loads((Path(folder) / "raw_results.json").read_text()):
        recs[(r["case_id"], r["phase"], r["condition"])] = r
    return recs


def _eval(recs: dict, phases) -> dict:
    e2 = st.e2(recs, np.random.default_rng(st.SEED))
    dd = sup.donor_dependence(recs, np.random.default_rng(st.SEED), n_perm=5000)
    return {ph: {"gain": e2.get(ph, {}).get("gain"), "gain_p": e2.get(ph, {}).get("gain_p"),
                 "perm_p": dd.get(ph, {}).get("perm_p"), "n": e2.get(ph, {}).get("n")} for ph in phases}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--phases", nargs="+", default=["DSCR"])
    ap.add_argument("--dir", default="results/robustness")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    folders = sorted(glob.glob(str(Path(args.dir) / f"lumiere_v4_{args.model}_alt*")))
    if not folders:
        raise SystemExit(f"no robustness folders in {args.dir} for {args.model} "
                         "(run run_lumiere_v4.py --results-dir results/robustness under each alt assignment first)")

    per = [{"folder": Path(f).name, **_eval(recs_from_folder(f), args.phases)} for f in folders]
    original = _eval(st.load_records(args.model), args.phases)   # original fixed assignment, for reference

    across = {}
    for ph in args.phases:
        gains = [r[ph]["gain"] for r in per if r[ph]["gain"] is not None]
        perms = [r[ph]["perm_p"] for r in per if r[ph]["perm_p"] is not None]
        across[ph] = {
            "orig_gain": original[ph]["gain"], "orig_perm_p": original[ph]["perm_p"],
            "gain_min": (min(gains) if gains else None), "gain_median": (float(np.median(gains)) if gains else None),
            "gain_max": (max(gains) if gains else None),
            "perm_p_min": (min(perms) if perms else None), "perm_p_max": (max(perms) if perms else None),
            "n_significant_05": int(sum(p < 0.05 for p in perms)), "n_assignments": len(perms)}

    summary = {"model": args.model, "n_assignments": len(folders), "across": across,
               "original": original, "per_assignment": per}
    out = args.out or f"results/lumiere_v4_robustness_{args.model}.json"
    Path(out).write_text(json.dumps(summary, indent=1))
    print(json.dumps(across, indent=1))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
