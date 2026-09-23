"""
Entry point for the gating-causality experiment (reviewer finding #2, see
paper/review.md and src/gating_causality.py's module docstring for the full
rationale). Thin sibling of run_lumiere.py: same CLI shape, same model roster,
different evaluation loop (downstream-phase-under-manufactured-context instead
of a full 5-phase chain).

Usage
-----
# Single model, all four dependent phases (LIL, DSCR, PJRF, TCM)
python run_lumiere_gating_causality.py --model Gemma-3-27B --include-unreviewed

# All four models
python run_lumiere_gating_causality.py --all-models --include-unreviewed

# Smoke test on a handful of patients first
python run_lumiere_gating_causality.py --model Gemma-3-27B --n-cases 3 --include-unreviewed

--include-unreviewed is required as of this writing: expert review of the v3 item set
has not completed (see paper/update.md), so data/lumiere/v3/reviewed is empty and every
other reported result in the paper (text-only ablation, evidence fact-check,
counterfactual-image substitution) was likewise run with LLM-drafted, not-yet-reviewed
items. Matches run_lumiere.py's own flag exactly, kept explicit rather than defaulted on
so this never silently reads unreviewed items once review does land.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

import config
import config.lumiere as lcfg
from src.lumiere_loader import load_lumiere
from config.models import ALL_MODELS, MODELS, MODEL_MAP
from src.gating_causality import run_all, summarize, DOWNSTREAM_PHASES


def _results_dir(model_name: str) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("results") / f"lumiere_gatingcausality_{model_name}_{ts}"


def run_model(model_cfg: dict, cases: list[dict], phases: list[str],
              radlex_path: Path, ncit_path: Path) -> None:
    print(f"\n{'#'*60}")
    print(f"  Model: {model_cfg['name']}  ({model_cfg['category']})  [gating-causality]")
    print(f"  Cases: {len(cases)}   Phases: {', '.join(phases)}")
    print(f"{'#'*60}")

    results = run_all(
        cases, model=model_cfg["model"], base_url=model_cfg.get("base_url"),
        api_key=model_cfg.get("api_key"), radlex_path=radlex_path, ncit_path=ncit_path,
        downstream_phases=phases,
    )
    summary = summarize(results, downstream_phases=phases)

    out_dir = _results_dir(model_cfg["name"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw_results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\n{'='*60}\nSummary — {model_cfg['name']}\n{'='*60}")
    for phase, conditions in summary.items():
        print(f"  {phase}:")
        for condition, d in conditions.items():
            acc = f"{d['acc']*100:.0f}%" if d["acc"] is not None else "n/a"
            ci = f" [{d['acc_ci'][0]*100:.0f}-{d['acc_ci'][1]*100:.0f}]" if d["acc_ci"] else ""
            print(f"    {condition:10s} {acc:>5s}{ci}  (n={d['n']})")
    print(f"\nSaved -> {out_dir}")


def parse_args():
    p = argparse.ArgumentParser(description="LUMIERE gating-causality experiment")
    p.add_argument("--model", type=str, default=None)
    p.add_argument("--all-models", action="store_true")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--n-cases", type=int, default=None)
    p.add_argument("--include-unreviewed", action="store_true",
                   help="Use LLM-drafted items still pending expert review (required "
                        "as of this writing -- see module docstring)")
    p.add_argument("--phases", type=str, default=None,
                   help="Comma-separated subset of LIL,DSCR,PJRF,TCM (default: all four)")
    p.add_argument("--item-set", choices=sorted(lcfg.ITEM_SETS), default="v3",
                   help="LUMIERE item set; default v3 (leak-controlled), matching every "
                        "other reported result in the paper")
    p.add_argument("--radlex-path", type=Path, default=Path("data/kb/radlex.owl"))
    p.add_argument("--ncit-path", type=Path, default=Path("data/kb/ncit.owl"))
    return p.parse_args()


def main():
    args = parse_args()

    if args.list_models:
        print(f"\n{'Name':<22} {'Category':<14} {'Backend':<10} Endpoint")
        print("-" * 70)
        for m in ALL_MODELS:
            print(f"{m['name']:<22} {m['category']:<14} {m.get('backend', 'openai'):<10} "
                  f"{m.get('base_url') or 'OpenAI API'}")
        return

    if not args.model and not args.all_models:
        print("Specify --model <name> or --all-models. Use --list-models to see options.")
        sys.exit(1)

    phases = args.phases.split(",") if args.phases else DOWNSTREAM_PHASES
    unknown = set(phases) - set(DOWNSTREAM_PHASES)
    if unknown:
        print(f"Unknown phase(s) {unknown}; choose from {DOWNSTREAM_PHASES}.")
        sys.exit(1)

    cases = load_lumiere(n_cases=args.n_cases, min_phases=2, item_set=args.item_set,
                         include_unreviewed=args.include_unreviewed)
    if not cases:
        print("No LUMIERE cases loaded. Either run tools/lumiere_merge_reviewed.py first, "
              "or pass --include-unreviewed (expert review has not completed yet).")
        sys.exit(1)

    missing = [p for p in (args.radlex_path, args.ncit_path) if not p.exists()]
    if missing:
        print("Missing required knowledge base file(s):", *missing, sep="\n  ")
        sys.exit(1)

    if args.all_models:
        for model_cfg in MODELS:
            run_model(model_cfg, cases, phases, args.radlex_path, args.ncit_path)
    else:
        model_cfg = MODEL_MAP.get(args.model)
        if model_cfg is None:
            print(f"Unknown model '{args.model}'. Use --list-models.")
            sys.exit(1)
        run_model(model_cfg, cases, phases, args.radlex_path, args.ncit_path)


if __name__ == "__main__":
    main()
