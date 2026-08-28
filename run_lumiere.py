"""
Entry point for the LUMIERE causal chain evaluation — genuine same-patient
chains, replacing OmniBrainBench's stitched-multi-patient "chains" for the
paper's causal-degradation claim. Thin sibling of run_omnibrain.py: same CLI
shape, same CausalChainEvaluator/save_results, only the loader differs.
Kept as a separate script so the existing OmniBrainBench baseline pipeline
is never at risk of being destabilized by this change.

Usage
-----
# Single model
python run_lumiere.py --model GPT-5 --n-cases 30

# Quick smoke test (2 cases)
python run_lumiere.py --model GPT-5 --n-cases 2

Requires data/lumiere/lumiere_chains_final.json to exist — run
tools/lumiere_merge_reviewed.py after expert review completes.
"""

import argparse
import datetime
import sys
from pathlib import Path

from src.lumiere_loader import load_lumiere
from config.models import MODELS, MODEL_MAP
from src.evaluator import CausalChainEvaluator
from src.analysis import save_results


def _results_dir(model_name: str) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("results") / f"lumiere_{model_name}_{ts}"


def run_model(model_cfg: dict, cases: list[dict], gating: bool, adaptation: bool,
              radlex_path: Path, ncit_path: Path) -> None:
    print(f"\n{'#'*60}")
    print(f"  Model: {model_cfg['name']}  ({model_cfg['category']})  [LUMIERE]")
    print(f"  Cases: {len(cases)}   Gating: {gating}   Adaptation: {adaptation}")
    print(f"{'#'*60}")

    evaluator = CausalChainEvaluator(
        model=model_cfg["model"], gating_enabled=gating, adaptation_enabled=adaptation,
        base_url=model_cfg.get("base_url"), api_key=model_cfg.get("api_key"),
        radlex_path=radlex_path, ncit_path=ncit_path,
    )
    results = evaluator.evaluate_all(cases)
    save_results(results, model_cfg["name"], _results_dir(model_cfg["name"]))


def parse_args():
    p = argparse.ArgumentParser(description="LUMIERE causal chain evaluation")
    p.add_argument("--model", type=str, default=None)
    p.add_argument("--all-models", action="store_true")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--n-cases", type=int, default=30)
    p.add_argument("--min-phases", type=int, default=2)
    p.add_argument("--no-gating", action="store_true")
    p.add_argument("--no-adaptation", action="store_true")
    p.add_argument("--radlex-path", type=Path, default=Path("data/kb/radlex.owl"))
    p.add_argument("--ncit-path", type=Path, default=Path("data/kb/ncit.owl"))
    return p.parse_args()


def main():
    args = parse_args()

    if args.list_models:
        print(f"\n{'Name':<22} {'Category':<14} {'Backend':<10} Endpoint")
        print("-" * 70)
        for m in MODELS:
            print(f"{m['name']:<22} {m['category']:<14} {m.get('backend', 'openai'):<10} "
                  f"{m.get('base_url') or 'OpenAI API'}")
        return

    if not args.model and not args.all_models:
        print("Specify --model <name> or --all-models. Use --list-models to see options.")
        sys.exit(1)

    cases = load_lumiere(n_cases=args.n_cases, min_phases=args.min_phases)
    if not cases:
        print("No LUMIERE cases loaded. Run tools/lumiere_merge_reviewed.py first.")
        sys.exit(1)

    missing = [p for p in (args.radlex_path, args.ncit_path) if not p.exists()]
    if missing:
        print("Missing required knowledge base file(s):", *missing, sep="\n  ")
        sys.exit(1)

    gating, adaptation = not args.no_gating, not args.no_adaptation
    if args.all_models:
        for model_cfg in MODELS:
            run_model(model_cfg, cases, gating, adaptation, args.radlex_path, args.ncit_path)
    else:
        model_cfg = MODEL_MAP.get(args.model)
        if model_cfg is None:
            print(f"Unknown model '{args.model}'. Use --list-models.")
            sys.exit(1)
        run_model(model_cfg, cases, gating, adaptation, args.radlex_path, args.ncit_path)


if __name__ == "__main__":
    main()
