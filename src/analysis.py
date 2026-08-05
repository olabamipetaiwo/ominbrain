"""
Report generation for OmniBrainBench causal chain evaluation.

Produces two outputs:
  1. report.txt          — human-readable chain evaluation summary
  2. total_results.json  — OmniBrainBench-compatible format (extends base acc
                           with faithfulness dimensions)
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

import config


def _safe_avg(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 3) if vals else None


def _wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Wilson score interval for a binomial proportion — valid at small n, unlike the normal approximation."""
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5)) / denom
    return (round(max(0.0, center - margin), 3), round(min(1.0, center + margin), 3))


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
            if pdata.get("kb_alignment") is not None:
                agg[phase]["kb_alignment"].append(pdata["kb_alignment"])
            if pdata.get("concept_precision") is not None:
                agg[phase]["concept_precision"].append(pdata["concept_precision"])
            agg[phase]["adaptation_triggered"].append(pdata.get("adaptation_triggered", 0))
            if pdata.get("adaptation_rate") is not None:
                agg[phase]["adaptation_rate"].append(pdata["adaptation_rate"])
            cf = case["chain_faithfulness_by_phase"].get(phase)
            if cf is not None:
                agg[phase]["chain_faithfulness"].append(cf)
            for q in pdata["questions"]:
                agg[phase]["q_correct"].append(int(q["correct"]))

    out = {}
    for phase in config.PHASES:
        d = agg[phase]
        n_q = len(d["q_correct"])
        out[phase] = {
            "acc": _safe_avg(d["phase_score"]),
            "acc_ci": _wilson_ci(sum(d["q_correct"]), n_q),
            "acc_n": n_q,
            "gate_block_rate": _safe_avg(d["gated_out"]),
            "local_faithfulness": _safe_avg(d["local_faithfulness"]),
            "kb_alignment": _safe_avg(d["kb_alignment"]),
            "concept_precision": _safe_avg(d["concept_precision"]),
            "chain_faithfulness": _safe_avg(d["chain_faithfulness"]),
            "adaptation_triggered": sum(d["adaptation_triggered"]),
            "adaptation_rate": _safe_avg(d["adaptation_rate"]),
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
                task_data[task]["kb_alignment_score"].append(q.get("kb_alignment_score", 0.0))
                task_data[task]["concept_precision_score"].append(q.get("concept_precision_score", 0.0))

    return {
        task: {
            "acc": _safe_avg(d["correct"]),
            "local_faithfulness": _safe_avg(d["local_faithful"]),
            "kb_alignment_score": _safe_avg(d["kb_alignment_score"]),
            "concept_precision_score": _safe_avg(d["concept_precision_score"]),
            "n": len(d["correct"]),
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


def build_report(results: list[dict], model_name: str) -> str:
    phase_agg = _phase_aggregate(results)
    task_agg = _task_aggregate(results)
    failures = _failure_counts(results)
    n_cases = len(results)
    chain_comp = sum(1 for r in results if r["chain_completed"])
    overall = _safe_avg([r["overall_score"] for r in results])

    def fmt(v: float | None) -> str:
        return f"{v:.0%}" if v is not None else "  —  "

    def fmt_ci(ci: tuple[float, float] | None) -> str:
        return f"[{ci[0]:.0%}-{ci[1]:.0%}]" if ci is not None else "   —    "

    lines = []
    lines.append("=" * 70)
    lines.append(f"OmniBrainBench — Causal Chain Evaluation")
    lines.append(f"Model: {model_name}   |   Cases: {n_cases}")
    lines.append("=" * 70)
    lines.append(f"\nOverall accuracy:   {overall:.1%}" if overall else "")
    lines.append(f"Chain completion:   {chain_comp}/{n_cases} ({chain_comp/n_cases:.0%})")

    lines.append("\n── Phase Results ")
    header = (
        f"{'Phase':<6} {'Acc':>6} {'95% CI':>10} {'N':>4} {'LocalF':>8} "
        f"{'KBAlign':>8} {'ConceptP':>9} {'ChainF':>8} {'GateBlk':>8}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for phase in config.PHASES:
        d = phase_agg[phase]
        lines.append(
            f"{phase:<6} {fmt(d['acc']):>6} {fmt_ci(d['acc_ci']):>10} {d['acc_n']:>4} "
            f"{fmt(d['local_faithfulness']):>8} "
            f"{fmt(d['kb_alignment']):>8} {fmt(d['concept_precision']):>9} "
            f"{fmt(d['chain_faithfulness']):>8} {fmt(d['gate_block_rate']):>8}"
        )

    total_triggered = sum(d["adaptation_triggered"] for d in phase_agg.values())
    adapted_phases = [d for d in phase_agg.values() if d["adaptation_rate"] is not None]
    overall_adapt_rate = _safe_avg([d["adaptation_rate"] for d in adapted_phases])
    lines.append("\n── Adaptation Loop ")
    lines.append(f"  Questions triggered:    {total_triggered}")
    lines.append(f"  Adaptation rate:        {fmt(overall_adapt_rate)}")

    lines.append("\n── Failure Taxonomy ─")
    lines.append(f"  Perception failures:          {failures['perception']}")
    lines.append(f"  Reasoning failures:           {failures['reasoning']}")
    lines.append(f"  Decision-making failures:     {failures['decision']}")
    lines.append(f"  Correct-but-unfaithful:       {failures['correct_unfaithful']}  ← clinically dangerous")

    lines.append("\n── Per-Task Accuracy ")
    for task, d in sorted(task_agg.items(), key=lambda x: -(x[1]["acc"] or 0)):
        lines.append(f"  {task:<45} acc={d['acc']:.0%}  n={d['n']}")

    lines.append("")
    return "\n".join(lines)


def build_omnibrain_results(results: list[dict], model_name: str) -> dict:
    """
    Returns a dict in OmniBrainBench total_results.json format,
    extended with causal chain metrics.
    """
    phase_agg = _phase_aggregate(results)
    task_agg = _task_aggregate(results)
    overall = _safe_avg([r["overall_score"] for r in results])
    chain_comp_rate = sum(1 for r in results if r["chain_completed"]) / len(results)

    phase_metrics = {
        config.PHASE_NAMES[abbr]: {
            "acc": data["acc"],
            "acc_ci": data["acc_ci"],
            "acc_n": data["acc_n"],
            "local_faithfulness": data["local_faithfulness"],
            "kb_alignment": data["kb_alignment"],
            "concept_precision": data["concept_precision"],
            "chain_faithfulness": data["chain_faithfulness"],
            "gate_block_rate": data["gate_block_rate"],
            "adaptation_triggered": data["adaptation_triggered"],
            "adaptation_rate": data["adaptation_rate"],
        }
        for abbr, data in phase_agg.items()
    }

    task_metrics = {
        task: {
            "acc": d["acc"],
            "local_faithfulness": d["local_faithfulness"],
            "kb_alignment_score": d["kb_alignment_score"],
            "concept_precision_score": d["concept_precision_score"],
            "n": d["n"],
        }
        for task, d in task_agg.items()
    }

    return {
        "OmniBrainBench": {
            "total metrics": {
                "acc": overall,
                "chain_completion_rate": round(chain_comp_rate, 3),
            },
            "task type metrics": task_metrics,
            "clinical phase type metrics": phase_metrics,
        }
    }


def save_results(results: list[dict], model_name: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_path = output_dir / "raw_results.json"
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    report = build_report(results, model_name)
    report_path = output_dir / "report.txt"
    report_path.write_text(report)
    print(report)

    omnibrain_out = build_omnibrain_results(results, model_name)
    total_path = output_dir / "total_results.json"
    with open(total_path, "w") as f:
        json.dump(omnibrain_out, f, indent=2)

    print(f"\nSaved → {output_dir}")
    print(f"  {raw_path.name}")
    print(f"  {report_path.name}")
    print(f"  {total_path.name}")
