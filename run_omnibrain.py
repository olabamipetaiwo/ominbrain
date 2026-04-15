"""
Entry point for the OmniBrainBench causal chain evaluation.

Usage
-----
# Single model
python run_omnibrain.py --model GPT-5 --n-cases 100

# All 12 models (sequential)
python run_omnibrain.py --all-models --n-cases 100

# Quick smoke test (5 cases)
python run_omnibrain.py --model GPT-5 --n-cases 5

# List available models
python run_omnibrain.py --list-models

# Force re-download the dataset
python run_omnibrain.py --model GPT-5 --force-download

# Skip gating (flat accuracy only — for comparison with OmniBrainBench baseline)
python run_omnibrain.py --model GPT-5 --no-gating
"""

import argparse
import datetime
import os
import sys
from pathlib import Path

import config
from data_loader import load_omnibrain
from models_config import MODELS, MODEL_MAP
from src.evaluator import CausalChainEvaluator
from src.analysis import save_results


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _results_dir(model_name: str) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("results") / f"{model_name}_{ts}"


def run_model(model_cfg: dict, cases: list[dict], gating: bool) -> None:
    print(f"\n{'#'*60}")
    print(f"  Model: {model_cfg['name']}  ({model_cfg['category']})")
    print(f"  Cases: {len(cases)}   Gating: {gating}")
    print(f"{'#'*60}")

    evaluator = CausalChainEvaluator(
        model=model_cfg["model"],
        gating_enabled=gating,
        base_url=model_cfg.get("base_url"),
        api_key=model_cfg.get("api_key"),
    )

    results = evaluator.evaluate_all(cases)
    out_dir = _results_dir(model_cfg["name"])
    save_results(results, model_cfg["name"], out_dir)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="OmniBrainBench causal chain evaluation")
    p.add_argument("--model",          type=str,  default=None,
                   help="Model name (from models_config.py)")
    p.add_argument("--all-models",     action="store_true",
                   help="Run all 12 models sequentially")
    p.add_argument("--list-models",    action="store_true",
                   help="Print available models and exit")
    p.add_argument("--n-cases",        type=int,  default=100,
                   help="Number of cases to evaluate (default: 100)")
    p.add_argument("--min-phases",     type=int,  default=2,
                   help="Min phases per case to be included (default: 2)")
    p.add_argument("--no-gating",      action="store_true",
                   help="Disable phase gating (flat eval for baseline comparison)")
    p.add_argument("--force-download", action="store_true",
                   help="Re-download dataset even if cached")
    p.add_argument("--seed",           type=int,  default=42)
    # Chunked / distributed eval — split cases across parallel workers
    # e.g. run 4 processes: --num-chunks 4 --chunk-idx 0/1/2/3
    p.add_argument("--num-chunks",     type=int,  default=1,
                   help="Total number of parallel chunks (default: 1 = no chunking)")
    p.add_argument("--chunk-idx",      type=int,  default=0,
                   help="Which chunk this process handles (0-indexed)")
    return p.parse_args()


def main():
    args = parse_args()

    if args.list_models:
        print(f"\n{'Name':<22} {'Category':<14} {'Backend':<10} Endpoint")
        print("-" * 70)
        for m in MODELS:
            backend  = m.get("backend", "openai")
            endpoint = m.get("base_url") or "OpenAI API"
            print(f"{m['name']:<22} {m['category']:<14} {backend:<10} {endpoint}")
        return

    if not args.model and not args.all_models:
        print("Specify --model <name> or --all-models. Use --list-models to see options.")
        sys.exit(1)

    # Load dataset once (shared across models)
    cases = load_omnibrain(
        n_cases=args.n_cases,
        min_phases=args.min_phases,
        force_download=args.force_download,
        seed=args.seed,
    )

    # Chunked eval — distribute cases across parallel workers
    if args.num_chunks > 1:
        cases = [c for i, c in enumerate(cases) if i % args.num_chunks == args.chunk_idx]
        print(f"Chunk {args.chunk_idx}/{args.num_chunks}: {len(cases)} cases")

    if not cases:
        print("No cases loaded. Check dataset download.")
        sys.exit(1)

    gating = not args.no_gating

    if args.all_models:
        for model_cfg in MODELS:
            run_model(model_cfg, cases, gating)
    else:
        model_cfg = MODEL_MAP.get(args.model)
        if model_cfg is None:
            print(f"Unknown model '{args.model}'. Use --list-models.")
            sys.exit(1)
        run_model(model_cfg, cases, gating)


if __name__ == "__main__":
    main()
