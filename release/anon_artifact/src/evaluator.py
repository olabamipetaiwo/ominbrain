"""
Multimodal evaluation engine for OmniBrainBench.

Per case:
  - Iterates phases in causal order (AIA → LIL → DSCR → PJRF → TCM)
  - Enforces soft gating: phase blocked if upstream phases below threshold
  - Per question:
      1. Main call         — model sees image + question + chain context
      2. Faithfulness probe — model sees only the reasoning, predicts answer
      3. KB alignment      — scores against phase-appropriate knowledge base
      4. Adaptation        — if KB-unfaithful and missed_concepts non-empty,
                             inject missed concepts and re-run (measures Adaptation Rate)
  - Computes chain faithfulness (cross-phase reasoning continuity)

Images loaded lazily per case (not all at once) to keep memory bounded.
"""

from __future__ import annotations

import gc
import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI

import config
from src.causal_graph import check_gate
from src.kb_aligner import KBAligner
from src.prompts import (
    build_main_prompt,
    build_faithfulness_probe,
    build_adaptation_prompt,
    ANSWER_RESPONSE_SCHEMA,
    FAITHFULNESS_RESPONSE_SCHEMA,
)


USAGE = {"calls": 0, "prompt_tokens": 0, "total_tokens": 0}  # successful calls only


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def _call_model(
    client: OpenAI,
    messages: list[dict],
    label: str = "",
    guided_json_schema: dict | None = None,
) -> str:
    """API call with exponential backoff retry (3 attempts, 5/10/20s delays).

    guided_json_schema, when set, is passed as extra_body={"guided_json": ...} —
    vLLM's structured-output decoding, which forces the response to conform to the
    schema at the token level. Only meaningful against a vLLM-backed model; other
    backends silently ignore unknown extra_body fields or error, so only pass this
    for vllm-backed evaluator runs (--guided-json).
    """
    tag = f" ({label})" if label else ""
    kwargs: dict = {}
    if guided_json_schema is not None:
        kwargs["extra_body"] = {"guided_json": guided_json_schema}
    for attempt in range(config.API_RETRY_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                **kwargs,
            )
            u = getattr(response, "usage", None)
            if u is not None:  # token accounting for API-cost estimates (run_lumiere_v4.py prints it)
                USAGE["calls"] += 1
                USAGE["prompt_tokens"] += getattr(u, "prompt_tokens", 0) or 0
                USAGE["total_tokens"] += getattr(u, "total_tokens", 0) or 0
            return response.choices[0].message.content.strip()
        except Exception as e:
            is_last = attempt == config.API_RETRY_ATTEMPTS - 1
            print(f"  [API error{tag}] attempt {attempt+1}/{config.API_RETRY_ATTEMPTS}: {e}")
            if is_last:
                return ""
            delay = config.API_RETRY_DELAY * (2**attempt)
            print(f"  Retrying in {delay}s…")
            time.sleep(delay)
    return ""


def _salvage_answer_letter(text: str) -> str | None:
    """Best-effort recovery of the answer letter from JSON that failed to parse.

    The response schema puts "answer" first, "visual_grounding" and "reasoning"
    last (src/prompts.py's _ANSWER_JSON_SCHEMA) — a model that degenerates into a
    repetition loop inside those later fields and hits MAX_TOKENS truncates the
    JSON, but the answer field is written (and complete) before that happens.
    Confirmed against MedGemma-4B's parse failures (round 1/2 runs, 2026-09-21/22):
    all had "answer" present and well-formed, only later fields were cut off."""
    m = re.search(r'"answer"\s*:\s*"([A-E])"', text)
    return m.group(1) if m else None


def _loads_lenient(candidate: str) -> dict | None:
    """json.loads, then again with strict=False. MedGemma-4B sometimes emits a literal
    newline inside a string value (e.g. "...standard of care.\\n" un-escaped) — otherwise
    complete, valid JSON that strict mode rejects as a bare control character. Confirmed
    against real parse failures (2026-09-22): 3/27 were exactly this, recovered losslessly
    by strict=False; do not need the truncation-salvage path below."""
    for strict in (True, False):
        try:
            return json.loads(candidate, strict=strict)
        except json.JSONDecodeError:
            continue
    return None


def _parse_json(text: str, required_keys: list[str]) -> dict | None:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    data = _loads_lenient(text)
    if data and all(k in data for k in required_keys):
        return data
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        data = _loads_lenient(match.group())
        if data and all(k in data for k in required_keys):
            return data
    return None


def _load_question_image(question: dict) -> list[bytes]:
    image_path = question.get("_image_path")
    image_dir = question.get("_image_dir")
    if not image_path or not image_dir:
        return []
    from src.data_loader import load_image_bytes_list
    return load_image_bytes_list(image_path, Path(str(image_dir)))


def _compute_chain_faithfulness(phase_results: dict) -> dict[str, float | None]:
    cf = {}
    for i, phase in enumerate(config.PHASES[1:], start=1):
        upstream = config.PHASES[i - 1]
        if upstream not in phase_results or phase not in phase_results:
            continue
        phase_data = phase_results[phase]
        if phase_data.get("gated_out"):
            cf[phase] = None
            continue
        hits = total = 0
        for q in phase_data.get("questions", []):
            for key in q.get("chain_grounding_terms_used", []):
                total += 1
                if key.lower() in q.get("reasoning", "").lower():
                    hits += 1
        cf[phase] = round(hits / total, 3) if total else None
    return cf


_NO_ADAPTATION: dict = {
    "adaptation_run": False,
    "adaptation_answer": None,
    "adaptation_correct": None,
    "adaptation_changed": None,
}


def _run_adaptation(
    question: dict,
    case_for_prompt: dict,
    phase: str,
    chain_context: list[dict],
    missed_concepts: list[str],
    original_answer: str,
    original_reasoning: str,
    client: OpenAI,
    guided_json: bool = False,
) -> dict:
    """
    Feedback-adaptation step.

    Injects missed KB concepts as a clinical correction and re-runs the phase.
    Returns adaptation fields to merge into the question result dict.
    """
    print("| adapt…", end=" ", flush=True)
    messages = build_adaptation_prompt(
        question, case_for_prompt, phase, chain_context,
        missed_concepts, original_answer, original_reasoning,
    )
    schema = ANSWER_RESPONSE_SCHEMA if guided_json else None
    raw = _call_model(client, messages, label="adaptation", guided_json_schema=schema)
    parsed = _parse_json(raw, ["answer", "visual_grounding", "reasoning"])

    if parsed is None:
        print("adapt parse failed")
        return {
            "adaptation_run": True,
            "adaptation_answer": None,
            "adaptation_correct": None,
            "adaptation_changed": None,
        }

    adapted_answer = parsed["answer"].strip().upper()
    adaptation_correct = adapted_answer == question["correct_answer"]
    adaptation_changed = adapted_answer != original_answer

    change_sym = "→" if adaptation_changed else "="
    status_sym = "✓" if adaptation_correct else "✗"
    print(f"adapt {change_sym}{adapted_answer} ({status_sym})")

    return {
        "adaptation_run": True,
        "adaptation_answer": adapted_answer,
        "adaptation_correct": adaptation_correct,
        "adaptation_changed": adaptation_changed,
    }


def _evaluate_question(
    question: dict,
    case: dict,
    phase: str,
    chain_context: list[dict],
    aligner: KBAligner,
    client: OpenAI,
    adaptation_enabled: bool = True,
    guided_json: bool = False,
    text_only: bool = False,
) -> dict:
    qid = question["id"]
    print(f"    [{qid}] main call…", end=" ", flush=True)

    img_list = [] if text_only else _load_question_image(question)
    if not img_list:
        print("[no image]", end=" ", flush=True)
    case_for_prompt = {
        **case,
        "image_bytes_list": img_list,
        "image_bytes": img_list[0] if img_list else None,
        # Per-image labels (e.g. "baseline (week-000)"/"follow-up (week-047)"), set by
        # lumiere_loader.py for LIL only; None for every other case, in which case
        # prompts.py falls back to its existing generic <image_N> labeling.
        "image_labels": None if text_only else question.get("_image_labels"),
        "image_note": None if text_only else question.get("_image_note"),
    }

    messages = build_main_prompt(question, case_for_prompt, phase, chain_context)
    answer_schema = ANSWER_RESPONSE_SCHEMA if guided_json else None
    raw = _call_model(client, messages, label="main", guided_json_schema=answer_schema)
    parsed = _parse_json(raw, ["answer", "visual_grounding", "reasoning"])

    if parsed is None:
        salvaged = _salvage_answer_letter(raw)
        if salvaged:
            print(f"parse failed — salvaged answer {salvaged} from truncated JSON.")
        else:
            print("parse failed.")
        model_answer = salvaged
        model_answer_text = question["options"].get(salvaged, "") if salvaged else None
        correct = salvaged == question["correct_answer"] if salvaged else False
        return {
            "id": qid,
            "question": question["question"],
            "correct_answer": question["correct_answer"],
            "correct_answer_text": question.get("correct_answer_text", ""),
            "model_answer": model_answer,
            "model_answer_text": model_answer_text,
            "correct": correct,
            "visual_grounding": "",
            "reasoning": "",
            "raw_response": raw,
            # Salvaged runs have no reasoning/visual_grounding text (truncated before those
            # fields completed), so faithfulness and KB-grounding can't be scored — left as
            # "not computed", not folded into the accuracy number either way.
            "local_faithful": None,
            "faithfulness_predicted": None,
            "kb_alignment_score": 0.0,
            "kb_alignment_faithful": False,
            "concept_precision_score": 0.0,
            "matched_concepts": [],
            "missed_concepts": [],
            "kb_used": "",
            "parse_error": True,
            "answer_salvaged": bool(salvaged),
            "task_label": question.get("task_label", ""),
            "counterfactual_partner": question.get("_counterfactual_partner"),
            **_NO_ADAPTATION,
        }

    model_answer = parsed["answer"].strip().upper()
    model_answer_text = question["options"].get(model_answer, "")
    correct = model_answer == question["correct_answer"]
    print(f"→ {model_answer} ({'✓' if correct else '✗'})", end=" ", flush=True)

    print("| probe…", end=" ", flush=True)
    faith_msgs = build_faithfulness_probe(parsed["reasoning"], question["options"])
    faith_schema = FAITHFULNESS_RESPONSE_SCHEMA if guided_json else None
    faith_raw = _call_model(client, faith_msgs, label="faithfulness", guided_json_schema=faith_schema)
    faith_parsed = _parse_json(faith_raw, ["predicted_answer"])

    if faith_parsed:
        faith_pred = faith_parsed["predicted_answer"].strip().upper()
        local_faithful = faith_pred == model_answer
        print(f"pred {faith_pred} → {'faithful' if local_faithful else 'UNFAITHFUL'}", end=" ", flush=True)
    else:
        faith_pred = None
        local_faithful = None
        print("probe parse failed", end=" ", flush=True)

    kb_result = aligner.align(
        phase,
        parsed["visual_grounding"],
        parsed["reasoning"],
        question.get("correct_answer_text", ""),
    )
    kb_faithful = kb_result.kb_alignment_score >= config.GROUNDING_THRESHOLD

    # Feedback-adaptation: trigger when KB-unfaithful and there are missed concepts to inject
    if adaptation_enabled and not kb_faithful and kb_result.missed_concepts:
        adaptation = _run_adaptation(
            question, case_for_prompt, phase, chain_context,
            kb_result.missed_concepts, model_answer, parsed["reasoning"],
            client, guided_json=guided_json,
        )
    else:
        print()  # newline after probe result
        adaptation = _NO_ADAPTATION

    return {
        "id": qid,
        "question": question["question"],
        "correct_answer": question["correct_answer"],
        "correct_answer_text": question["correct_answer_text"],
        "model_answer": model_answer,
        "model_answer_text": model_answer_text,
        "correct": correct,
        "visual_grounding": parsed["visual_grounding"],
        "reasoning": parsed["reasoning"],
        "raw_response": raw,
        "local_faithful": local_faithful,
        "faithfulness_predicted": faith_pred,
        "kb_alignment_score": kb_result.kb_alignment_score,
        "kb_alignment_faithful": kb_faithful,
        "concept_precision_score": kb_result.concept_precision_score,
        "matched_concepts": kb_result.matched_concepts,
        "missed_concepts": kb_result.missed_concepts,
        "kb_used": kb_result.kb_used,
        "parse_error": False,
        "task_label": question.get("task_label", ""),
        "counterfactual_partner": question.get("_counterfactual_partner"),
        **adaptation,
    }


class CausalChainEvaluator:

    def __init__(
        self,
        model: str = config.MODEL,
        gating_enabled: bool = True,
        gating_threshold: float = config.GATING_THRESHOLD,
        adaptation_enabled: bool = True,
        base_url: str | None = None,
        api_key: str | None = None,
        radlex_path: Path = Path("data/kb/radlex.owl"),
        ncit_path: Path = Path("data/kb/ncit.owl"),
        guided_json: bool = False,
        text_only: bool = False,
    ):
        self.model = model
        self.gating_enabled = gating_enabled
        self.gating_threshold = gating_threshold
        self.adaptation_enabled = adaptation_enabled
        self.guided_json = guided_json
        self.text_only = text_only  # ablation: strip images, see whether accuracy survives on text alone
        self.aligner = KBAligner(radlex_path=radlex_path, ncit_path=ncit_path)
        config.MODEL = model

        kwargs: dict = {}
        if base_url:
            kwargs["base_url"] = base_url
        kwargs["api_key"] = api_key or os.environ.get("OPENAI_API_KEY") or "local"
        self._client = OpenAI(**kwargs)

    def evaluate_all(self, cases: list[dict]) -> list[dict]:
        results = []
        for i, case in enumerate(cases, 1):
            print(f"\n{'='*60}")
            print(f"Case {i}/{len(cases)}: {case['title']}  [{case.get('source_file','')}]")
            print(f"{'='*60}")
            results.append(self.evaluate_case(case))
            gc.collect()
        return results

    def evaluate_case(self, case: dict) -> dict:
        total_qs = sum(len(qs) for qs in case["phases"].values())
        print(f"  {len(case['phases'])} phase(s) | {total_qs} question(s)")

        phase_results: dict = {}
        phase_scores: dict = {}
        chain_context: list = []

        for phase in config.PHASES:
            phase_name = config.PHASE_NAMES[phase]
            print(f"\n  Phase: {phase} — {phase_name}")

            if self.gating_enabled and not check_gate(phase_scores, phase, self.gating_threshold):
                print("  *** GATE BLOCKED ***")
                phase_results[phase] = {
                    "gated_out": True,
                    "questions": [],
                    "phase_score": 0.0,
                    "passed_gate": False,
                    "local_faithfulness": None,
                    "kb_alignment": None,
                    "concept_precision": None,
                    "adaptation_triggered": 0,
                    "adaptation_rate": None,
                }
                phase_scores[phase] = 0.0
                continue

            questions = case["phases"].get(phase, [])
            if not questions:
                continue

            question_results = []
            for q in questions:
                result = _evaluate_question(
                    q, case, phase, chain_context,
                    self.aligner, self._client, self.adaptation_enabled,
                    guided_json=self.guided_json, text_only=self.text_only,
                )
                result["chain_grounding_terms_used"] = q.get("chain_grounding_terms", [])
                question_results.append(result)
                chain_context.append({
                    "phase": phase,
                    "question_id": q["id"],
                    "question": q["question"],
                    "model_answer": result["model_answer"] or "?",
                    "model_answer_text": result["model_answer_text"] or "",
                    "visual_grounding": result["visual_grounding"],
                })
                time.sleep(0.3)

            answered = [r for r in question_results if not r.get("parse_error")]
            phase_score = sum(r["correct"] for r in answered) / len(answered) if answered else 0.0
            passed_gate = phase_score >= self.gating_threshold

            lf_vals = [r["local_faithful"] for r in answered if r["local_faithful"] is not None]
            kb_vals = [r["kb_alignment_score"] for r in answered]
            cp_vals = [r["concept_precision_score"] for r in answered]

            adapted = [r for r in answered if r.get("adaptation_run")]
            adapt_correct = [r for r in adapted if r.get("adaptation_correct")]
            adaptation_rate = len(adapt_correct) / len(adapted) if adapted else None

            phase_scores[phase] = phase_score
            lf_str = f"{_avg(lf_vals):.0%}" if lf_vals else "—"
            adapt_str = f"  adapt: {len(adapt_correct)}/{len(adapted)} ({adaptation_rate:.0%})" if adapted else ""
            gate_str = "PASS" if passed_gate else "FAIL"
            print(f"  → score: {phase_score:.0%} [{gate_str}]  local faithful: {lf_str}{adapt_str}")

            phase_results[phase] = {
                "gated_out": False,
                "questions": question_results,
                "phase_score": round(phase_score, 3),
                "passed_gate": passed_gate,
                "local_faithfulness": _avg(lf_vals),
                "kb_alignment": _avg(kb_vals),
                "concept_precision": _avg(cp_vals),
                "adaptation_triggered": len(adapted),
                "adaptation_rate": round(adaptation_rate, 3) if adaptation_rate is not None else None,
            }

        chain_faithfulness = _compute_chain_faithfulness(phase_results)

        active = [v for v in phase_results.values() if not v["gated_out"]]
        overall = sum(p["phase_score"] for p in active) / len(active) if active else 0.0
        chain_completed = all(
            not v["gated_out"] and v["passed_gate"]
            for phase, v in phase_results.items()
            if phase in case["phases"]
        )

        case["image_bytes"] = None
        case["image_bytes_list"] = None

        return {
            "case_id": case["id"],
            "title": case["title"],
            "modality": case["modality"],
            "source_file": case.get("source_file", ""),
            "phases": phase_results,
            "chain_faithfulness_by_phase": chain_faithfulness,
            "overall_score": round(overall, 3),
            "chain_completed": chain_completed,
        }
