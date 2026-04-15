"""
Report generation for OmniBrainBench causal chain evaluation.

Produces two outputs:
  1. report.txt          — human-readable chain evaluation summary
  2. total_results.json  — OmniBrainBench-compatible format (extends base acc
                           with faithfulness dimensions)
"""

import json
from pathlib import Path
from collections import defaultdict

import config


# ──────────────────────────────────────────────
# Aggregate helpers
# ──────────────────────────────────────────────

def _safe_avg(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 3) if vals else None


def _phase_aggregate(results: list[dict]) -> dict:
    """Per-phase accuracy, faithfulness, and gating stats across all cases."""
    agg = {p: defaultdict(list) for p in config.PHASES}

    for case in results:
        for phase, pdata in case["phases"].items():
            if pdata["gated_out"]:
                agg[phase]["gated_out"].append(1)
                continue
            agg[phase]["gated_out"].append(0)
            agg[phase]["phase_score"].append(pdata["phase_score"])
            agg[phase]["passed_gate"].append(int(pdata["passed_gate"]))
            if pdata["local_faithfulness"] is not None:
                agg[phase]["local_faithfulness"].append(pdata["local_faithfulness"])
            if pdata["grounding_faithfulness"] is not None:
                agg[phase]["grounding_faithfulness"].append(pdata["grounding_faithfulness"])
            cf = case["chain_faithfulness_by_phase"].get(phase)
            if cf is not None:
                agg[phase]["chain_faithfulness"].append(cf)

    out = {}
    for phase in config.PHASES:
        d = agg[phase]
        out[phase] = {
            "acc":                   _safe_avg(d["phase_score"]),
            "gate_block_rate":       _safe_avg(d["gated_out"]),
            "local_faithfulness":    _safe_avg(d["local_faithfulness"]),
            "grounding_faithfulness":_safe_avg(d["grounding_faithfulness"]),
            "chain_faithfulness":    _safe_avg(d["chain_faithfulness"]),
        }
    return out


def _task_aggregate(results: list[dict]) -> dict:
    """Per-task accuracy and faithfulness across all questions in all cases."""
    task_data = defaultdict(lambda: defaultdict(list))

    for case in results:
        for phase, pdata in case["phases"].items():
            if pdata["gated_out"]:
                continue
            for q in pdata["questions"]:
                task = q.get("task_label", "Unknown")
                task_data[task]["correct"].append(int(q["correct"]))
                if q["local_faithful"] is not None:
                    task_data[task]["local_faithful"].append(int(q["local_faithful"]))
                task_data[task]["grounding_score"].append(q["grounding_score"])

    return {
        task: {
            "acc":                _safe_avg(d["correct"]),
            "local_faithfulness": _safe_avg(d["local_faithful"]),
            "grounding_score":    _safe_avg(d["grounding_score"]),
            "n":                  len(d["correct"]),
        }
        for task, d in task_data.items()
    }


def _failure_counts(results: list[dict]) -> dict:
    counts = {"perception": 0, "reasoning": 0, "decision": 0, "correct_unfaithful": 0}
    for case in results:
        for phase, pdata in case["phases"].items():
            if pdata["gated_out"]:
                continue
            ftype = config.FAILURE_TYPE.get(phase, "")
            for q in pdata["questions"]:
                if not q["correct"]:
                    counts[ftype] = counts.get(ftype, 0) + 1
                if q["correct"] and q["local_faithful"] is False:
                    counts["correct_unfaithful"] += 1
    return counts


# ──────────────────────────────────────────────
# Human-readable report
# ──────────────────────────────────────────────

def build_report(results: list[dict], model_name: str) -> str:
    phase_agg  = _phase_aggregate(results)
    task_agg   = _task_aggregate(results)
    failures   = _failure_counts(results)
    n_cases    = len(results)
    chain_comp = sum(1 for r in results if r["chain_completed"])
    overall    = _safe_avg([r["overall_score"] for r in results])

    lines = []
    lines.append("=" * 70)
    lines.append(f"OmniBrainBench — Causal Chain Evaluation")
    lines.append(f"Model: {model_name}   |   Cases: {n_cases}")
    lines.append("=" * 70)
    lines.append(f"\nOverall accuracy:   {overall:.1%}" if overall else "")
    lines.append(f"Chain completion:   {chain_comp}/{n_cases} ({chain_comp/n_cases:.0%})")

    lines.append("\n── Phase Results ──────────────────────────────────────────────")
    header = f"{'Phase':<6} {'Acc':>6} {'LocalF':>8} {'GroundF':>8} {'ChainF':>8} {'GateBlk':>8}"
    lines.append(header)
    lines.append("-" * len(header))
    for phase in config.PHASES:
        d = phase_agg[phase]
        def fmt(v): return f"{v:.0%}" if v is not None else "  —  "
        lines.append(
            f"{phase:<6} {fmt(d['acc']):>6} {fmt(d['local_faithfulness']):>8} "
            f"{fmt(d['grounding_faithfulness']):>8} {fmt(d['chain_faithfulness']):>8} "
            f"{fmt(d['gate_block_rate']):>8}"
        )

    lines.append("\n── Failure Taxonomy ───────────────────────────────────────────")
    lines.append(f"  Perception failures:          {failures['perception']}")
    lines.append(f"  Reasoning failures:           {failures['reasoning']}")
    lines.append(f"  Decision-making failures:     {failures['decision']}")
    lines.append(f"  Correct-but-unfaithful:       {failures['correct_unfaithful']}  ← clinically dangerous")

    lines.append("\n── Per-Task Accuracy ──────────────────────────────────────────")
    for task, d in sorted(task_agg.items(), key=lambda x: -(x[1]["acc"] or 0)):
        lines.append(f"  {task:<45} acc={d['acc']:.0%}  n={d['n']}")

    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# OmniBrainBench-compatible total_results.json
# ──────────────────────────────────────────────

def build_omnibrain_results(results: list[dict], model_name: str) -> dict:
    """
    Returns a dict in OmniBrainBench total_results.json format,
    extended with causal chain metrics.
    """
    phase_agg = _phase_aggregate(results)
    task_agg  = _task_aggregate(results)
    overall   = _safe_avg([r["overall_score"] for r in results])
    chain_comp_rate = sum(1 for r in results if r["chain_completed"]) / len(results)

    # clinical phase type metrics — full phase names as keys
    phase_metrics = {}
    for abbr, data in phase_agg.items():
        full_name = config.PHASE_NAMES[abbr]
        phase_metrics[full_name] = {
            "acc":                    data["acc"],
            "local_faithfulness":     data["local_faithfulness"],
            "grounding_faithfulness": data["grounding_faithfulness"],
            "chain_faithfulness":     data["chain_faithfulness"],
            "gate_block_rate":        data["gate_block_rate"],
        }

    # task type metrics — task label as keys
    task_metrics = {
        task: {
            "acc":                d["acc"],
            "local_faithfulness": d["local_faithfulness"],
            "grounding_score":    d["grounding_score"],
            "n":                  d["n"],
        }
        for task, d in task_agg.items()
    }

    return {
        "OmniBrainBench": {
            "total metrics": {
                "acc":                   overall,
                "chain_completion_rate": round(chain_comp_rate, 3),
            },
            "task type metrics":          task_metrics,
            "clinical phase type metrics":phase_metrics,
        }
    }


# ──────────────────────────────────────────────
# Save outputs
# ──────────────────────────────────────────────

def save_results(
    results: list[dict],
    model_name: str,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # raw results
    raw_path = output_dir / "raw_results.json"
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # human report
    report = build_report(results, model_name)
    report_path = output_dir / "report.txt"
    report_path.write_text(report)
    print(report)

    # OmniBrainBench-compatible
    omnibrain_out = build_omnibrain_results(results, model_name)
    total_path = output_dir / "total_results.json"
    with open(total_path, "w") as f:
        json.dump(omnibrain_out, f, indent=2)

    print(f"\nSaved → {output_dir}")
    print(f"  {raw_path.name}")
    print(f"  {report_path.name}")
    print(f"  {total_path.name}")
