"""
LLM options-only baseline (paper/review.md TODO, reviewer round 2 item 9).

Each of the 5 phase questions is asked with NO image, NO question stem, and NO chain context: the model sees
only the four answer options (plus the case's phase header and the standard answer-format instructions) and must
pick the most likely correct one. Accuracy above the majority-class / chance rate means the options themselves
leak the answer, i.e. a floor that image-present accuracy has to beat.

The no-chain-context baseline needs no new run: it is the 'absent' condition of the gating-causality experiment
(LIL-TCM) and the ordinary own-image v3 run for AIA (which has no upstream phase).

Reuses src/evaluator.py::_evaluate_question unmodified (text_only=True, adaptation off). Prompt caveat: the
standard main prompt still contains its instruction lines about "visual features in the image"; the same is true
of the existing text-only ablation, so the two are comparable. The stem is replaced by a fixed placeholder.

Usage
-----
python run_lumiere_options_only.py --model MedGemma-4B --include-unreviewed
python run_lumiere_options_only.py --all-models --include-unreviewed
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

import config
import config.lumiere as lcfg
from config.models import MODELS, MODEL_MAP
from openai import OpenAI
from src.analysis import _wilson_ci
from src.evaluator import _evaluate_question
from src.kb_aligner import KBAligner
from src.lumiere_loader import load_lumiere

STEM_PLACEHOLDER = "[The question text is withheld. Choose the option most likely to be the correct answer.]"


def run_model(model_cfg: dict, cases: list[dict], radlex_path: Path, ncit_path: Path,
              save_raw: bool = False, run_tag: str = "") -> None:
    print(f"\n{'#'*60}\n  Model: {model_cfg['name']}  [options-only baseline]   Cases: {len(cases)}\n{'#'*60}")
    aligner = KBAligner(radlex_path=radlex_path, ncit_path=ncit_path)
    config.MODEL = model_cfg["model"]
    kwargs = {"api_key": model_cfg.get("api_key") or "local"}
    if model_cfg.get("base_url"):
        kwargs["base_url"] = model_cfg["base_url"]
    client = OpenAI(**kwargs)

    results = []
    for i, case in enumerate(cases, 1):
        print(f"\nCase {i}/{len(cases)}: {case['id']}")
        blind_case = {**case, "title": "Case withheld", "modality": "mri"}
        out = {"case_id": case["id"], "phases": {}}
        for phase in config.PHASES:
            qs = case["phases"].get(phase)
            if not qs:
                continue
            q = {**qs[0], "question": STEM_PLACEHOLDER}
            r = _evaluate_question(q, blind_case, phase, [], aligner, client,
                                   adaptation_enabled=False, text_only=True)
            out["phases"][phase] = {"model_answer": r["model_answer"], "correct": r["correct"],
                                    "correct_answer": r["correct_answer"], "parse_error": r["parse_error"]}
            if save_raw:   # diagnostic only: the primary runs did not keep the model's raw output
                out["phases"][phase]["raw_response"] = r["raw_response"]
                out["phases"][phase]["answer_salvaged"] = r.get("answer_salvaged", False)
        results.append(out)

    summary = {}
    for phase in config.PHASES:
        oc = [r["phases"][phase]["correct"] for r in results if phase in r["phases"]]
        n, k = len(oc), sum(oc)
        summary[phase] = {"acc": round(k / n, 3) if n else None, "acc_ci": _wilson_ci(k, n), "n": n}

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # A tagged run goes to lumiere_optionsonly_<tag>_<model>_<ts>: the `lumiere_optionsonly_` prefix keeps it out of
    # compile_lumiere_results.py, and the tag keeps lumiere_gating_stats.py's `lumiere_optionsonly_<model>_*` glob
    # from picking it up in place of the primary run.
    tag = f"{run_tag}_" if run_tag else ""
    out_dir = Path("results") / f"lumiere_optionsonly_{tag}{model_cfg['name']}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw_results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nSummary — {model_cfg['name']}")
    for phase, d in summary.items():
        print(f"  {phase:5s} {d['acc']*100:.0f}%  (n={d['n']})" if d["acc"] is not None else f"  {phase}: n/a")
    print(f"Saved -> {out_dir}")


def main():
    p = argparse.ArgumentParser(description="LUMIERE LLM options-only baseline")
    p.add_argument("--model", type=str, default=None)
    p.add_argument("--all-models", action="store_true")
    p.add_argument("--n-cases", type=int, default=None)
    p.add_argument("--include-unreviewed", action="store_true",
                   help="Use LLM-drafted items pending expert review (required as of this writing)")
    p.add_argument("--item-set", choices=sorted(lcfg.ITEM_SETS), default="v3")
    p.add_argument("--save-raw", action="store_true",
                   help="Also store each raw model response in raw_results.json (diagnosing parse failures)")
    p.add_argument("--run-tag", default="",
                   help="Label for the results folder (e.g. diag) so the run is not mistaken for the primary one")
    p.add_argument("--radlex-path", type=Path, default=Path("data/kb/radlex.owl"))
    p.add_argument("--ncit-path", type=Path, default=Path("data/kb/ncit.owl"))
    args = p.parse_args()
    if not args.model and not args.all_models:
        print("Specify --model <name> or --all-models.")
        sys.exit(1)
    cases = load_lumiere(n_cases=args.n_cases, min_phases=2, item_set=args.item_set,
                         include_unreviewed=args.include_unreviewed)
    if not cases:
        print("No LUMIERE cases loaded (pass --include-unreviewed).")
        sys.exit(1)
    for m in (MODELS if args.all_models else [MODEL_MAP.get(args.model)]):
        if m is None:
            print(f"Unknown model '{args.model}'.")
            sys.exit(1)
        run_model(m, cases, args.radlex_path, args.ncit_path, save_raw=args.save_raw, run_tag=args.run_tag)


if __name__ == "__main__":
    main()
