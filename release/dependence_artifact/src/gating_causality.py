"""
Gating-causality experiment (reviewer finding #2, paper/review.md).

Soft gating (src/causal_graph.py, Section 3.3 of the paper) blocks a downstream phase
when an upstream phase scored below threshold. The reviewer's objection: this can look
like causal-degradation evidence even when phases are answered completely independently
-- five independent 80%-accuracy phases chained multiplicatively already yield ~33% with
zero real dependency. Gating alone can't tell these apart.

This experiment tests the dependency directly. For each patient and each downstream phase
(LIL, DSCR, PJRF, TCM -- AIA has no upstream dependency and is excluded), the SAME
downstream question (same image(s), same question text, same options) is evaluated three
times, varying only the injected upstream chain_context:

  correct   -- every upstream phase's true correct answer
  incorrect -- every upstream phase's answer forced to a fixed wrong option
  absent    -- no chain context at all (empty list)

If a model is genuinely reasoning from upstream context, accuracy should track condition
quality (correct >= absent >= incorrect, or at minimum correct > incorrect). If accuracy is
flat across all three, the model is answering each phase independently regardless of what
gating assumes, and gating's causal framing is not supported for that phase/model.

Reuses _evaluate_question from src/evaluator.py completely unmodified -- the only thing
that differs from a normal run is what chain_context gets passed in (there: the model's
own real answers accumulated so far; here: manufactured per condition). No new prompting
or scoring logic, so results are directly comparable to the rest of the paper's numbers.
"""

from __future__ import annotations

from openai import OpenAI

import config
from src.evaluator import _evaluate_question
from src.kb_aligner import KBAligner

CONDITIONS = ("correct", "incorrect", "absent")

# Every downstream phase in config.PHASES (["AIA","LIL","DSCR","PJRF","TCM"]) has all
# earlier phases as its upstream dependency, matching src/causal_graph.py's chain order.
DOWNSTREAM_PHASES = [p for p in config.PHASES if p != config.PHASES[0]]


def _upstream_phases(phase: str) -> list[str]:
    return config.PHASES[: config.PHASES.index(phase)]


def _pick_wrong_letter(question: dict) -> str:
    """Deterministic (not random): the alphabetically-first option letter that isn't
    correct, so the "incorrect" condition is reproducible across runs/models."""
    return next(l for l in sorted(question["options"]) if l != question["correct_answer"])


def _context_entry(phase: str, question: dict, letter: str) -> dict:
    """Same shape src/prompts.py's build_main_prompt() reads from a real chain_context
    entry (phase, question_id, question, model_answer, model_answer_text,
    visual_grounding) -- so a manufactured entry is indistinguishable in format from a
    real one, and only the correctness of its content varies by condition."""
    text = question["options"][letter]
    return {
        "phase": phase,
        "question_id": question["id"],
        "question": question["question"],
        "model_answer": letter,
        "model_answer_text": text,
        "visual_grounding": text,
    }


def build_chain_context(case: dict, downstream_phase: str, condition: str,
                        include: list[str] | None = None,
                        exclude: list[str] | None = None) -> list[dict]:
    """`include` / `exclude` (ablation, added 2026-09-23 for the TCM-leakage check) restrict WHICH
    upstream phases appear in the injected context; the default (both None) is the original
    experiment. Ablation runs write to a separate results prefix so they never mix with it."""
    if condition == "absent":
        return []
    if condition not in ("correct", "incorrect"):
        raise ValueError(f"unknown condition: {condition}")

    context = []
    for phase in _upstream_phases(downstream_phase):
        if include is not None and phase not in include:
            continue
        if exclude is not None and phase in exclude:
            continue
        upstream_qs = case["phases"].get(phase)
        if not upstream_qs:
            continue  # patient missing this upstream phase -- skip, don't fabricate one
        q = upstream_qs[0]
        letter = q["correct_answer"] if condition == "correct" else _pick_wrong_letter(q)
        context.append(_context_entry(phase, q, letter))
    return context


def run_case(case: dict, aligner: KBAligner, client: OpenAI,
             downstream_phases: list[str] = DOWNSTREAM_PHASES,
             conditions: tuple[str, ...] = CONDITIONS,
             include: list[str] | None = None, exclude: list[str] | None = None) -> dict:
    """Evaluates every (downstream_phase, condition) pair for one patient.

    Returns {"case_id": ..., "phases": {phase: {condition: {model_answer, correct,
    correct_answer, parse_error}}}}. Phases the patient lacks entirely (rare, LUMIERE
    is phase-complete by construction post-rebaseline) are skipped, not zero-filled.
    """
    out: dict = {"case_id": case["id"], "phases": {}}
    for phase in downstream_phases:
        questions = case["phases"].get(phase)
        if not questions:
            continue
        question = questions[0]
        phase_out = {}
        for condition in conditions:
            context = build_chain_context(case, phase, condition, include, exclude)
            result = _evaluate_question(
                question, case, phase, context, aligner, client,
                adaptation_enabled=False,  # isolate the context-manipulation effect;
                                            # adaptation is an orthogonal mechanism
            )
            phase_out[condition] = {
                "model_answer": result["model_answer"],
                "correct": result["correct"],
                "correct_answer": result["correct_answer"],
                "parse_error": result["parse_error"],
            }
            print(f"    [{case['id']}/{phase}/{condition}] "
                  f"-> {result['model_answer']} ({'OK' if result['correct'] else 'wrong'})")
        out["phases"][phase] = phase_out
    return out


def run_all(cases: list[dict], model: str, base_url: str | None, api_key: str | None,
            radlex_path, ncit_path,
            downstream_phases: list[str] = DOWNSTREAM_PHASES,
            conditions: tuple[str, ...] = CONDITIONS,
            include: list[str] | None = None, exclude: list[str] | None = None) -> list[dict]:
    aligner = KBAligner(radlex_path=radlex_path, ncit_path=ncit_path)
    config.MODEL = model
    kwargs: dict = {"api_key": api_key or "local"}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)

    results = []
    for i, case in enumerate(cases, 1):
        print(f"\n{'='*60}\nCase {i}/{len(cases)}: {case['title']}\n{'='*60}")
        results.append(run_case(case, aligner, client, downstream_phases, conditions, include, exclude))
    return results


def summarize(results: list[dict], downstream_phases: list[str] = DOWNSTREAM_PHASES,
              conditions: tuple[str, ...] = CONDITIONS) -> dict:
    """Per-phase accuracy under each condition, plus a Wilson CI (reusing
    src/analysis.py's implementation so it matches the rest of the paper's CIs)."""
    from src.analysis import _wilson_ci

    summary: dict = {}
    for phase in downstream_phases:
        summary[phase] = {}
        for condition in conditions:
            outcomes = [
                r["phases"][phase][condition]["correct"]
                for r in results if phase in r["phases"]
            ]
            n = len(outcomes)
            successes = sum(outcomes)
            summary[phase][condition] = {
                "acc": round(successes / n, 3) if n else None,
                "acc_ci": _wilson_ci(successes, n),
                "n": n,
            }
    return summary
