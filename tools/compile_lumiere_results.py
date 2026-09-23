"""
Compile per-model LUMIERE runs into one cross-model comparison table.

Reads results/lumiere_<model>_<timestamp>/raw_results.json (written by
src.analysis.save_results), keeps the latest run per model, and reuses
src.analysis's own aggregation (_phase_aggregate, _failure_counts) so the numbers
match each run's report.txt exactly. Read-only on the run folders; safe on a login node.

PJRF and TCM are always separate columns — never pooled (low n; pooling would
erase the degradation signal).

Usage
-----
python -m tools.compile_lumiere_results
python -m tools.compile_lumiere_results --results-dir results --out-prefix results/lumiere_summary
"""

import argparse
import csv
import json
import re
from pathlib import Path

import config
from src.analysis import _failure_counts, _phase_aggregate

RUN_RE = re.compile(r"^lumiere_(?P<model>.+)_(?P<ts>\d{8}_\d{6})$")


def latest_runs(results_dir: Path, before: str | None = None, after: str | None = None) -> dict[str, Path]:
    """model name -> latest run folder that has a raw_results.json.

    before/after (an RUN_RE timestamp string, e.g. "20260921_200000") restrict to runs
    strictly before / at-or-after that cutoff — used to pick out one "round" of runs
    when the same model was re-run later (e.g. after a data fix)."""
    runs: dict[str, tuple[str, Path]] = {}
    for d in sorted(results_dir.glob("lumiere_*")):
        m = RUN_RE.match(d.name)
        if not m or not (d / "raw_results.json").exists():
            continue
        model, ts = m["model"], m["ts"]
        if before is not None and ts >= before:
            continue
        if after is not None and ts < after:
            continue
        model = model.replace("_nogate", " (no gating)").replace("_noadapt", " (no adaptation)")
        if model not in runs or ts > runs[model][0]:
            runs[model] = (ts, d)
    return {model: path for model, (_, path) in runs.items()}


def summarize(results: list[dict]) -> dict:
    phase_agg = _phase_aggregate(results)
    fails = _failure_counts(results)
    n_cases = len(results)
    return {
        "n_cases": n_cases,
        "overall_acc": (sum(r["overall_score"] for r in results) / n_cases) if n_cases else None,
        "chain_completion": (sum(1 for r in results if r["chain_completed"]) / n_cases) if n_cases else None,
        "correct_unfaithful": fails["correct_unfaithful"],
        "phases": phase_agg,
    }


def _pct(v):
    return "—" if v is None else f"{100 * v:.0f}%"


def _cell(pdata: dict) -> str:
    n, ci = pdata["acc_n"], pdata["acc_ci"]
    if not n or ci is None or pdata["acc"] is None:
        return "—"
    cell = f"{_pct(pdata['acc'])} [{100 * ci[0]:.0f}–{100 * ci[1]:.0f}] n={n}"
    maj = pdata.get("majority_baseline")
    # Only flag when the trivial baseline is high enough to matter (i.e. an imbalanced
    # phase like DSCR) — free-text phases (PJRF/TCM) have near-unique correct answers per
    # item, so their majority_baseline is near 0 and not worth cluttering every cell with.
    if maj is not None and maj >= 0.4:
        cell += f" (maj {_pct(maj)})"
    return cell


def build_markdown(summaries: dict[str, dict], run_dirs: dict[str, Path]) -> str:
    lines = [
        "# LUMIERE preliminary results (LLM-drafted, unreviewed items)",
        "",
        "Per-phase accuracy with Wilson 95% CI and n = questions scored. "
        "PJRF and TCM are reported separately, not pooled.",
        "",
        "| Model | Cases | " + " | ".join(config.PHASES) + " | Overall | Chain completion | Correct-but-unfaithful |",
        "|---|---|" + "---|" * len(config.PHASES) + "---|---|---|",
    ]
    for model, s in summaries.items():
        cells = " | ".join(_cell(s["phases"][p]) for p in config.PHASES)
        lines.append(f"| {model} | {s['n_cases']} | {cells} | {_pct(s['overall_acc'])} | "
                     f"{_pct(s['chain_completion'])} | {s['correct_unfaithful']} |")
    lines += ["", "Source runs:"] + [f"- {m}: `{d}`" for m, d in run_dirs.items()]
    return "\n".join(lines) + "\n"


def write_csv(path: Path, summaries: dict[str, dict]) -> None:
    metrics = ["acc", "acc_n", "majority_baseline", "kb_alignment", "local_faithfulness", "gate_block_rate"]
    header = ["model", "n_cases", "overall_acc", "chain_completion", "correct_unfaithful"]
    header += [f"{p}_{m}" for p in config.PHASES for m in metrics] + [f"{p}_ci_low" for p in config.PHASES] \
              + [f"{p}_ci_high" for p in config.PHASES]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for model, s in summaries.items():
            row = [model, s["n_cases"], s["overall_acc"], s["chain_completion"], s["correct_unfaithful"]]
            row += [s["phases"][p][m] for p in config.PHASES for m in metrics]
            row += [s["phases"][p]["acc_ci"][0] if s["phases"][p]["acc_ci"] else None for p in config.PHASES]
            row += [s["phases"][p]["acc_ci"][1] if s["phases"][p]["acc_ci"] else None for p in config.PHASES]
            w.writerow(row)


def _delta_cell(a: dict, b: dict) -> str:
    """One phase's before -> after accuracy, with the point-change and each n."""
    pa, pb = a["acc"], b["acc"]
    if pa is None or pb is None:
        return "—"
    sign = "+" if pb >= pa else ""
    return f"{_pct(pa)} (n={a['acc_n']}) → {_pct(pb)} (n={b['acc_n']}) [{sign}{100 * (pb - pa):.0f}pp]"


def build_compare_markdown(before: dict[str, dict], after: dict[str, dict],
                            before_dirs: dict[str, Path], after_dirs: dict[str, Path],
                            before_label: str, after_label: str) -> str:
    models = [m for m in before if m in after]
    lines = [
        f"# LUMIERE two-round comparison: {before_label} vs {after_label}",
        "",
        "Per-phase accuracy, before -> after, with n and the point change. PJRF and TCM are reported",
        "separately, not pooled. A phase/model missing from one round is shown as `—`.",
        "",
        "| Model | " + " | ".join(config.PHASES) + " | Overall |",
        "|---|" + "---|" * len(config.PHASES) + "---|",
    ]
    for m in models:
        a, b = before[m], after[m]
        cells = " | ".join(_delta_cell(a["phases"][p], b["phases"][p]) for p in config.PHASES)
        overall = (f"{_pct(a['overall_acc'])} → {_pct(b['overall_acc'])}"
                   if a["overall_acc"] is not None and b["overall_acc"] is not None else "—")
        lines.append(f"| {m} | {cells} | {overall} |")
    skipped = [m for m in before if m not in after] + [m for m in after if m not in before]
    lines += ["", "Source runs:"]
    lines += [f"- {m} ({before_label}): `{before_dirs[m]}`" for m in models]
    lines += [f"- {m} ({after_label}): `{after_dirs[m]}`" for m in models]
    if skipped:
        lines += ["", f"Only in one round (not compared): {', '.join(sorted(set(skipped)))}"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Compile LUMIERE per-model results into one table")
    ap.add_argument("--results-dir", type=Path, default=Path("results"))
    ap.add_argument("--out-prefix", type=Path, default=None,
                    help="default: <results-dir>/lumiere_summary (.md and .csv)")
    ap.add_argument("--split-at", type=str, default=None,
                    help="timestamp cutoff (YYYYMMDD_HHMMSS) splitting runs into two rounds for a "
                         "before/after comparison table, e.g. --split-at 20260921_200000. Each "
                         "model's latest run before the cutoff is 'before', latest at/after is 'after'.")
    ap.add_argument("--before-label", type=str, default="before")
    ap.add_argument("--after-label", type=str, default="after")
    args = ap.parse_args()

    if args.split_at:
        before_dirs = latest_runs(args.results_dir, before=args.split_at)
        after_dirs = latest_runs(args.results_dir, after=args.split_at)
        if not before_dirs or not after_dirs:
            raise SystemExit(f"--split-at {args.split_at} left one side empty "
                              f"({len(before_dirs)} before, {len(after_dirs)} after)")
        before_sum = {m: summarize(json.loads((d / "raw_results.json").read_text()))
                      for m, d in before_dirs.items()}
        after_sum = {m: summarize(json.loads((d / "raw_results.json").read_text()))
                     for m, d in after_dirs.items()}
        prefix = args.out_prefix or args.results_dir / "lumiere_compare"
        md = build_compare_markdown(before_sum, after_sum, before_dirs, after_dirs,
                                     args.before_label, args.after_label)
        prefix.with_suffix(".md").write_text(md)
        print(md)
        print(f"Saved → {prefix.with_suffix('.md')}")
        return

    run_dirs = latest_runs(args.results_dir)
    if not run_dirs:
        raise SystemExit(f"No lumiere_*/raw_results.json found under {args.results_dir}")

    summaries = {m: summarize(json.loads((d / "raw_results.json").read_text()))
                 for m, d in run_dirs.items()}
    prefix = args.out_prefix or args.results_dir / "lumiere_summary"
    md = build_markdown(summaries, run_dirs)
    prefix.with_suffix(".md").write_text(md)
    write_csv(prefix.with_suffix(".csv"), summaries)
    print(md)
    print(f"Saved → {prefix.with_suffix('.md')}, {prefix.with_suffix('.csv')}")


if __name__ == "__main__":
    main()
