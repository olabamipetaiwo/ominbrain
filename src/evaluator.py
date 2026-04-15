"""
Multimodal evaluation engine for OmniBrainBench.

Per case:
  - Iterates phases in causal order (AIA → LIL → DSCR → PJRF → TCM)
  - Enforces soft gating: phase blocked if upstream phases below threshold
  - Per question:
      1. Main call   — model sees image + question + chain context
      2. Faithfulness probe — model sees only the reasoning, predicts answer
      3. Scores correctness, local faithfulness, grounding faithfulness
  - Computes chain faithfulness (cross-phase reasoning continuity)

Images loaded lazily per case (not all at once) to keep memory bounded.
"""

import gc
import json
import re
import os
import time
from pathlib import Path

from openai import OpenAI

import config
from src.causal_graph import check_gate
from src.prompts import build_main_prompt, build_faithfulness_probe

client: OpenAI = None  # initialised in CausalChainEvaluator.__init__


# ──────────────────────────────────────────────
# API helpers
# ──────────────────────────────────────────────

def _call_model(messages: list[dict], label: str = "") -> str:
    """API call with exponential backoff retry (3 attempts, 5/10/20s delays)."""
    tag = f" ({label})" if label else ""
    for attempt in range(config.API_RETRY_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            is_last = attempt == config.API_RETRY_ATTEMPTS - 1
            print(f"  [API error{tag}] attempt {attempt+1}/{config.API_RETRY_ATTEMPTS}: {e}")
            if is_last:
                return ""
            delay = config.API_RETRY_DELAY * (2 ** attempt)
            print(f"  Retrying in {delay}s…")
            time.sleep(delay)
    return ""


def _parse_json(text: str, required_keys: list[str]) -> dict | None:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        data = json.loads(text)
        if all(k in data for k in required_keys):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if all(k in data for k in required_keys):
                return data
        except json.JSONDecodeError:
            pass
    return None


# ──────────────────────────────────────────────
# Image loader (lazy, cached in case dict)
# ──────────────────────────────────────────────

def _ensure_image(case: dict) -> None:
    """
    Load image bytes into case dict if not already loaded.
    Handles both single-image (str) and multi-image (list) image_path.
    Sets:
      case["image_bytes"]      — primary image (first), for backward compat
      case["image_bytes_list"] — all images as list[bytes]
    """
    if case.get("image_bytes_list") is not None:
        return
    image_dir  = case.get("_image_dir")
    image_path = case.get("_image_path")
    if not image_dir or not image_path:
        return
    from data_loader import load_image_bytes_list
    img_list = load_image_bytes_list(image_path, Path(str(image_dir)))
    case["image_bytes_list"] = img_list
    case["image_bytes"]      = img_list[0] if img_list else None


# ──────────────────────────────────────────────
# Faithfulness helpers
# ──────────────────────────────────────────────

def _grounding_score(visual_grounding: str, grounding_terms: list[str]) -> float:
    if not grounding_terms:
        return 1.0
    vg = visual_grounding.lower()
    hits = sum(1 for t in grounding_terms if t.lower() in vg)
    return hits / len(grounding_terms)


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
        upstream_texts = [
            q["correct_answer_text"].lower()
            for q in phase_results[upstream].get("questions", [])
            if q.get("correct")
        ]
        upstream_ref = " ".join(upstream_texts)
        hits = total = 0
        for q in phase_data.get("questions", []):
            for key in q.get("chain_grounding_terms_used", []):
                total += 1
                if key.lower() in q.get("reasoning", "").lower():
                    hits += 1
        cf[phase] = round(hits / total, 3) if total else None
    return cf


# ──────────────────────────────────────────────
# Per-question evaluation
# ──────────────────────────────────────────────

def _evaluate_question(
    question: dict,
    case: dict,
    phase: str,
    chain_context: list[dict],
) -> dict:
    qid = question["id"]
    print(f"    [{qid}] main call…", end=" ", flush=True)

    messages = build_main_prompt(question, case, phase, chain_context)
    raw      = _call_model(messages, label="main")
    parsed   = _parse_json(raw, ["answer", "visual_grounding", "reasoning"])

    if parsed is None:
        print("parse failed.")
        return {
            "id": qid, "question": question["question"],
            "correct_answer": question["correct_answer"],
            "model_answer": None, "model_answer_text": None,
            "correct": False, "visual_grounding": "", "reasoning": "",
            "raw_response": raw, "local_faithful": None,
            "faithfulness_predicted": None, "grounding_score": 0.0,
            "grounding_faithful": False, "parse_error": True,
            "task_label": question.get("task_label", ""),
        }

    model_answer      = parsed["answer"].strip().upper()
    model_answer_text = question["options"].get(model_answer, "")
    correct           = model_answer == question["correct_answer"]
    print(f"→ {model_answer} ({'✓' if correct else '✗'})", end=" ", flush=True)

    # Faithfulness probe
    print("| probe…", end=" ", flush=True)
    faith_msgs   = build_faithfulness_probe(parsed["reasoning"], question["options"])
    faith_raw    = _call_model(faith_msgs, label="faithfulness")
    faith_parsed = _parse_json(faith_raw, ["predicted_answer"])

    if faith_parsed:
        faith_pred    = faith_parsed["predicted_answer"].strip().upper()
        local_faithful = faith_pred == model_answer
        print(f"pred {faith_pred} → {'faithful' if local_faithful else 'UNFAITHFUL'}")
    else:
        faith_pred    = None
        local_faithful = None
        print("probe parse failed")

    grounding_sc      = _grounding_score(parsed["visual_grounding"], question["grounding_terms"])
    grounding_faithful = grounding_sc >= config.GROUNDING_THRESHOLD

    return {
        "id":                    qid,
        "question":              question["question"],
        "correct_answer":        question["correct_answer"],
        "correct_answer_text":   question["correct_answer_text"],
        "model_answer":          model_answer,
        "model_answer_text":     model_answer_text,
        "correct":               correct,
        "visual_grounding":      parsed["visual_grounding"],
        "reasoning":             parsed["reasoning"],
        "raw_response":          raw,
        "local_faithful":        local_faithful,
        "faithfulness_predicted":faith_pred,
        "grounding_score":       round(grounding_sc, 3),
        "grounding_faithful":    grounding_faithful,
        "parse_error":           False,
        "task_label":            question.get("task_label", ""),
    }


# ──────────────────────────────────────────────
# Main evaluator class
# ──────────────────────────────────────────────

class CausalChainEvaluator:

    def __init__(
        self,
        model: str = config.MODEL,
        gating_enabled: bool = True,
        gating_threshold: float = config.GATING_THRESHOLD,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model             = model
        self.gating_enabled    = gating_enabled
        self.gating_threshold  = gating_threshold
        config.MODEL           = model

        global client
        kwargs: dict = {}
        if base_url:
            kwargs["base_url"] = base_url
        kwargs["api_key"] = api_key or os.environ.get("OPENAI_API_KEY") or "local"
        client = OpenAI(**kwargs)

    def evaluate_all(self, cases: list[dict]) -> list[dict]:
        results = []
        for i, case in enumerate(cases, 1):
            print(f"\n{'='*60}")
            print(f"Case {i}/{len(cases)}: {case['title']}  [{case.get('source_file','')}]")
            print(f"{'='*60}")
            results.append(self.evaluate_case(case))
            gc.collect()   # release image memory between cases
        return results

    def evaluate_case(self, case: dict) -> dict:
        # Load images once at the start of the case
        _ensure_image(case)
        img_list = case.get("image_bytes_list") or []
        if img_list:
            total_kb = sum(len(b) for b in img_list) // 1024
            print(f"  {len(img_list)} image(s) loaded ({total_kb} KB total)")
        else:
            print("  [warn] No images found — text-only fallback")

        phase_results: dict  = {}
        phase_scores:  dict  = {}
        chain_context: list  = []

        for phase in config.PHASES:
            phase_name = config.PHASE_NAMES[phase]
            print(f"\n  Phase: {phase} — {phase_name}")

            if self.gating_enabled and not check_gate(
                phase_scores, phase, self.gating_threshold
            ):
                print("  *** GATE BLOCKED ***")
                phase_results[phase] = {
                    "phase": phase, "gated_out": True, "questions": [],
                    "phase_score": 0.0, "passed_gate": False,
                    "local_faithfulness": None, "grounding_faithfulness": None,
                }
                phase_scores[phase] = 0.0
                continue

            questions = case["phases"].get(phase, [])
            if not questions:
                # Phase not present in this case — treat as not evaluated
                continue

            question_results = []
            for q in questions:
                result = _evaluate_question(q, case, phase, chain_context)
                result["chain_grounding_terms_used"] = q.get("chain_grounding_terms", [])
                question_results.append(result)
                chain_context.append({
                    "phase":            phase,
                    "question_id":      q["id"],
                    "question":         q["question"],
                    "model_answer":     result["model_answer"] or "?",
                    "model_answer_text":result["model_answer_text"] or "",
                    "visual_grounding": result["visual_grounding"],
                })
                time.sleep(0.3)

            answered   = [r for r in question_results if not r.get("parse_error")]
            phase_score = (
                sum(r["correct"] for r in answered) / len(answered) if answered else 0.0
            )
            passed_gate = phase_score >= self.gating_threshold

            lf_vals = [r["local_faithful"] for r in answered if r["local_faithful"] is not None]
            local_f = round(sum(lf_vals) / len(lf_vals), 3) if lf_vals else None

            gf_vals = [r["grounding_score"] for r in answered]
            ground_f = round(sum(gf_vals) / len(gf_vals), 3) if gf_vals else None

            phase_scores[phase] = phase_score
            gate_str = "PASS" if passed_gate else "FAIL"
            lf_str   = f"{local_f:.0%}" if local_f is not None else "—"
            print(f"  → score: {phase_score:.0%} [{gate_str}]  local faithful: {lf_str}")

            phase_results[phase] = {
                "phase": phase, "gated_out": False,
                "questions": question_results,
                "phase_score": round(phase_score, 3),
                "passed_gate": passed_gate,
                "local_faithfulness": local_f,
                "grounding_faithfulness": ground_f,
            }

        chain_faithfulness = _compute_chain_faithfulness(phase_results)

        active = [v for v in phase_results.values() if not v["gated_out"]]
        overall = (
            sum(p["phase_score"] for p in active) / len(active) if active else 0.0
        )
        chain_completed = all(
            not v["gated_out"] and v["passed_gate"] for v in phase_results.values()
            if v["phase"] in case["phases"]
        )

        # Release image bytes to free RAM
        case["image_bytes"]      = None
        case["image_bytes_list"] = None

        return {
            "case_id":                    case["id"],
            "title":                      case["title"],
            "modality":                   case["modality"],
            "source_file":                case.get("source_file", ""),
            "phases":                     phase_results,
            "chain_faithfulness_by_phase":chain_faithfulness,
            "overall_score":              round(overall, 3),
            "chain_completed":            chain_completed,
        }
