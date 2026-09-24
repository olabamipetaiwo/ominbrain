"""
Entry point for the v4 single-question intervention conditions (src/v4_conditions.py; paper/review.md
concerns 2-4). Sibling of run_lumiere_gating_causality.py: same model roster and results layout.

  python run_lumiere_v4.py --model Gemma-3-12B --conditions own,text,swap
  python run_lumiere_v4.py --model Gemma-3-12B --conditions ctx_gold,ctx_wrong,ctx_absent,flip_label,flip_window
  python run_lumiere_v4.py --mock --n-cases 3 --conditions own,text,swap,ctx_gold   # offline smoke test, no model

Results -> results/lumiere_v4_<model>_<tag>_<timestamp>/{raw_results,summary}.json. The ordinary chain run
(own answers as context) is `python run_lumiere.py --item-set v4 --include-unreviewed --no-gating --no-adaptation`.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

from config.models import ALL_MODELS, MODELS, MODEL_MAP
from src.lumiere_loader import load_lumiere
from src.v4_conditions import CONDITIONS, PHASES_BY_CONDITION, run_all, summarize


def parse_args():
    p = argparse.ArgumentParser(description="LUMIERE v4 intervention conditions")
    p.add_argument("--model", default=None)
    p.add_argument("--all-models", action="store_true")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--conditions", default=",".join(CONDITIONS), help=f"comma-separated subset of {CONDITIONS}")
    p.add_argument("--phases", default=None, help="restrict to these phases (comma-separated)")
    p.add_argument("--n-cases", type=int, default=None)
    p.add_argument("--tag", default="", help="label added to the results folder name")
    p.add_argument("--mock", action="store_true", help="offline smoke test with a deterministic fake model")
    return p.parse_args()


def run_model(model_cfg: dict, conditions: tuple, phases, n_cases, tag: str, mock: bool) -> None:
    cases = load_lumiere(n_cases=n_cases, min_phases=2, include_unreviewed=True, item_set="v4")
    swap_cases = (load_lumiere(n_cases=n_cases, min_phases=2, include_unreviewed=True, item_set="v4",
                               counterfactual_images=True) if "swap" in conditions else None)
    print(f"\n{'#' * 60}\n  Model: {model_cfg['name']}  [v4 conditions: {', '.join(conditions)}]  cases: {len(cases)}\n{'#' * 60}")
    lookup = load_lumiere(n_cases=None, min_phases=2, include_unreviewed=True, item_set="v4") if n_cases else None
    records = run_all(cases, swap_cases, model=model_cfg["model"], base_url=model_cfg.get("base_url"),
                      api_key=model_cfg.get("api_key"), conditions=conditions, phases=phases, mock=mock,
                      lookup_cases=lookup)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"lumiere_v4_{model_cfg['name']}{'_' + tag if tag else ''}_{ts}"
    out = Path("results") / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw_results.json").write_text(json.dumps(records, indent=1))
    summary = summarize(records)
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"\nSaved -> {out}")
    for phase, conds in summary.items():
        print(f"  {phase}: " + "; ".join(f"{c}: {d.get('acc', d.get('brier'))}" for c, d in conds.items()))


def main():
    args = parse_args()
    if args.list_models:
        for m in ALL_MODELS:
            print(f"{m['name']:<22} {m['category']:<14} {m.get('base_url') or 'OpenAI API'}")
        return
    conditions = tuple(args.conditions.split(","))
    if set(conditions) - set(CONDITIONS):
        sys.exit(f"unknown condition(s) {set(conditions) - set(CONDITIONS)}")
    phases = tuple(args.phases.split(",")) if args.phases else None
    if args.mock:
        run_model({"name": "MOCK", "model": "mock", "category": "mock"}, conditions, phases, args.n_cases, args.tag or "mock", True)
        return
    if not args.model and not args.all_models:
        sys.exit("Specify --model <name> or --all-models (or --mock).")
    for m in (MODELS if args.all_models else [MODEL_MAP[args.model]]):
        run_model(m, conditions, phases, args.n_cases, args.tag, False)


if __name__ == "__main__":
    main()
