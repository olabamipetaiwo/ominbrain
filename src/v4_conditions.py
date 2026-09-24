"""
Single-question intervention conditions for the v4 item set (paper/review.md concerns 2, 3, 4).

Every condition asks ONE question at a time with an explicitly manufactured upstream context, so a phase's
effect is not confounded with answers the model itself produced earlier in the chain (the "fixed-context
comparison" of concern 4). The prompt, parsing and salvage code are the evaluator's own (src/evaluator.py,
src/prompts.py), so results are comparable with the ordinary chain runs; the recoverability probe and the KB
scoring are skipped because these conditions only need the answer.

  own          image(s) of the patient, no upstream context          AIA LIL DSCR
  text         no image, no upstream context                         AIA LIL DSCR
  swap         image(s) of a donor patient whose key differs (one     AIA LIL DSCR
               donor per patient and phase; stems contain no patient-
               specific fact and every option set holds every possible
               answer, so the donor's answer is always available)
  ctx_gold     true upstream answers (AIA, LIL, DSCR)                LIL DSCR PJRF TCM
  ctx_wrong    each upstream answer replaced by a seeded random       LIL DSCR PJRF TCM
               incorrect option (not one fixed option)
  ctx_absent   no upstream context                                   PJRF TCM  (== own for image phases)
  flip_label   TCM with the DSCR entry replaced by the label that     TCM
               the rule maps to a different management class
  flip_window  TCM with the stated weeks since chemoradiotherapy      TCM
               moved to the other side of the 12-week window
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import time
from pathlib import Path

from openai import OpenAI

import config
from src.evaluator import _call_model, _load_question_image, _parse_json, _salvage_answer_letter
from src.gating_causality import _context_entry
from src.prompts import build_main_prompt

CONDITIONS = ("own", "text", "swap", "ctx_gold", "ctx_wrong", "ctx_absent", "flip_label", "flip_window")
IMAGE_PHASES = ("AIA", "LIL", "DSCR")
PHASES_BY_CONDITION = {
    "own": IMAGE_PHASES, "text": IMAGE_PHASES, "swap": IMAGE_PHASES,
    "ctx_gold": ("LIL", "DSCR", "PJRF", "TCM"), "ctx_wrong": ("LIL", "DSCR", "PJRF", "TCM"),
    "ctx_absent": ("PJRF", "TCM"), "flip_label": ("TCM",), "flip_window": ("TCM",),
}
WINDOW_FLIP_X = {"to_late": 20, "to_early": 4}          # stated weeks since chemoradiotherapy after the flip
FLIP_LABEL = {"PD": "Stable disease", "nonPD": "Progressive disease"}
TCM_CLASS_OPTIONS = ("continue", "confirm", "escalate", "stop")


def tcm_rule_class(rano: str, x: int) -> str:
    """The management class the TCM rule assigns (must match src/lumiere_v4.py::tcm_class thresholds)."""
    if rano.lower() != "progressive disease":
        return "continue"
    return "confirm" if x <= 12 else "escalate"


def _wrong_letter(question: dict) -> str:
    rng = random.Random(f"v4wrong:{question['id']}")
    return rng.choice([l for l in sorted(question["options"]) if l != question["correct_answer"]])


def build_context(case: dict, phase: str, mode: str, dscr_letter: str | None = None) -> list[dict]:
    """Manufactured upstream context. mode: gold | wrong | absent. PJRF has no gold answer and is never injected."""
    if mode == "absent":
        return []
    out = []
    for up in config.PHASES[: config.PHASES.index(phase)]:
        qs = case["phases"].get(up)
        if not qs or qs[0].get("scoring") == "forecast":
            continue
        q = qs[0]
        letter = q["correct_answer"] if mode == "gold" else _wrong_letter(q)
        if up == "DSCR" and dscr_letter is not None:
            letter = dscr_letter
        out.append(_context_entry(up, q, letter))
    return out


def _letter_for(question: dict, text: str) -> str | None:
    return next((l for l, t in question["options"].items() if t.lower() == text.lower()), None)


def _retext_window(question: dict, x_old: int, wss_old: int, x_new: int) -> dict:
    """Copy of a TCM question with the stated timing moved (weeks since surgery keeps the same +10 offset)."""
    wss_new = x_new + (wss_old - x_old)
    text = question["question"]
    t2 = text.replace(f"{wss_old} weeks after surgery", f"{wss_new} weeks after surgery", 1)
    t2 = t2.replace(f"about {x_old} weeks before", f"about {x_new} weeks before", 1)
    if t2 == text or f"about {x_new} weeks before" not in t2:
        raise ValueError(f"could not rewrite the timing in {question['id']}")
    return {**question, "question": t2}


def ask(question: dict, case: dict, phase: str, chain_context: list[dict], client, text_only: bool = False,
        image_override: dict | None = None) -> dict:
    src = {**question, **(image_override or {})}
    imgs = [] if text_only else _load_question_image(src)
    if not text_only and src.get("_image_path") and not imgs:
        raise FileNotFoundError(f"image(s) missing for {question['id']}: {src.get('_image_path')}")
    case_for_prompt = {**case, "image_bytes_list": imgs, "image_bytes": imgs[0] if imgs else None,
                       "image_labels": None if text_only else src.get("_image_labels"),
                       "image_note": None if text_only or not imgs else src.get("_image_note")}
    raw = _call_model(client, build_main_prompt(question, case_for_prompt, phase, chain_context), label="v4")
    parsed = _parse_json(raw, ["answer", "visual_grounding", "reasoning"])
    if parsed is None:
        ans, parse_error, reasoning, grounding = _salvage_answer_letter(raw), True, "", ""
    else:
        ans, parse_error = parsed["answer"].strip().upper(), False
        reasoning, grounding = parsed["reasoning"], parsed["visual_grounding"]
    return {"model_answer": ans, "parse_error": parse_error, "reasoning": reasoning, "visual_grounding": grounding,
            "raw": raw if parse_error else None}


def _record(case, phase, condition, question, res, extra: dict | None = None) -> dict:
    forecast = question.get("scoring") == "forecast"
    ans = res["model_answer"]
    rec = {"case_id": case["id"], "phase": phase, "condition": condition, "model_answer": ans,
           "parse_error": res["parse_error"], "correct_answer": question["correct_answer"],
           "correct": (None if forecast else bool(ans and ans == question["correct_answer"])),
           "reasoning": res["reasoning"], "visual_grounding": res["visual_grounding"]}
    if forecast:
        mid = question["forecast"]["bin_midpoints"].get(ans)
        rec.update({"forecast_outcome": question["forecast"]["outcome"], "forecast_prob": mid})
    if res.get("raw"):
        rec["raw"] = res["raw"]
    rec.update(extra or {})
    return rec


def run_case(case: dict, swap_case: dict | None, own_by_id: dict[str, dict], client, conditions: tuple[str, ...],
             phases: tuple[str, ...] | None = None) -> list[dict]:
    out = []
    for cond in conditions:
        for phase in PHASES_BY_CONDITION[cond]:
            if phases and phase not in phases:
                continue
            qs = case["phases"].get(phase)
            if not qs:
                continue
            q = qs[0]
            extra: dict = {}
            question, ctx, text_only, img_override = q, [], False, None
            if cond == "own":
                pass
            elif cond == "text":
                text_only = True
            elif cond == "swap":
                sq = (swap_case or {}).get("phases", {}).get(phase)
                if not sq or not sq[0].get("_counterfactual_partner"):
                    continue
                donor_id = sq[0]["_counterfactual_partner"]
                donor_q = own_by_id[f"{donor_id}_{phase}"]
                donor_letter = _letter_for(q, donor_q["correct_answer_text"])
                img_override = {k: sq[0][k] for k in ("_image_path", "_image_dir") if k in sq[0]}
                extra = {"donor": donor_id, "donor_key_letter": donor_letter, "donor_key_text": donor_q["correct_answer_text"],
                         "own_key_text": q["correct_answer_text"]}
            elif cond == "ctx_gold":
                ctx = build_context(case, phase, "gold")
            elif cond == "ctx_wrong":
                ctx = build_context(case, phase, "wrong")
            elif cond == "ctx_absent":
                ctx = []
            elif cond in ("flip_label", "flip_window"):
                rule = q["tcm_rule"]
                x, rano_gold = rule["weeks_since_chemoradiotherapy"], rule["rano"]
                dscr_q = case["phases"]["DSCR"][0]
                wss = x + 10
                if cond == "flip_label":
                    new_label = FLIP_LABEL["PD" if rano_gold.lower() == "progressive disease" else "nonPD"]
                    ctx = build_context(case, phase, "gold", dscr_letter=_letter_for(dscr_q, new_label))
                    expected = tcm_rule_class(new_label, x)
                else:
                    x_new = WINDOW_FLIP_X["to_late" if x <= 12 else "to_early"]
                    question = _retext_window(q, x, wss, x_new)
                    ctx = build_context(case, phase, "gold")
                    expected = tcm_rule_class(rano_gold, x_new)
                from src.lumiere_v4 import TCM_OPTIONS
                exp_letter = _letter_for(q, TCM_OPTIONS[expected])
                extra = {"original_class": rule["class"], "expected_class": expected, "expected_letter": exp_letter}
            injected = next((e["model_answer_text"] for e in ctx if e["phase"] == "DSCR"), None)
            if injected is not None:
                extra["injected_dscr_text"] = injected
                if phase == "TCM":   # what the rule prescribes for the STATED category (correct or not) and the true timing
                    from src.lumiere_v4 import TCM_OPTIONS
                    stated = tcm_rule_class(injected, q["tcm_rule"]["weeks_since_chemoradiotherapy"]) \
                        if cond != "flip_window" else None
                    if stated:
                        extra["stated_rule_class"] = stated
                        extra["stated_rule_letter"] = _letter_for(q, TCM_OPTIONS[stated])
            res = ask(question, case, phase, ctx, client, text_only=text_only, image_override=img_override)
            rec = _record(case, phase, cond, question, res, extra)
            if cond in ("flip_label", "flip_window"):
                rec["follows_flip"] = bool(rec["model_answer"] and rec["model_answer"] == extra["expected_letter"])
            if "stated_rule_letter" in extra:
                rec["follows_stated_label"] = bool(rec["model_answer"] and rec["model_answer"] == extra["stated_rule_letter"])
            if cond == "swap":
                rec["tracks_donor"] = bool(rec["model_answer"] and rec["model_answer"] == extra["donor_key_letter"])
            out.append(rec)
            tag = ("OK" if rec.get("correct") else "wrong") if rec["correct"] is not None else f"p={rec.get('forecast_prob')}"
            print(f"    [{case['id']}/{phase}/{cond}] -> {rec['model_answer']} ({tag})", flush=True)
    return out


class MockClient:
    """Offline stand-in for an OpenAI-compatible client: deterministic, image- and context-blind answers."""

    class _Chat:
        class _Completions:
            @staticmethod
            def create(model, messages, **kw):
                text = json.dumps(messages, default=str)
                h = int(hashlib.sha1(text.encode()).hexdigest(), 16)
                body = json.dumps({"answer": "ABCD"[h % 4], "visual_grounding": "mock", "reasoning": "mock"})
                msg = type("M", (), {"content": body})
                return type("R", (), {"choices": [type("C", (), {"message": msg})]})
        completions = _Completions()
    chat = _Chat()


def run_all(cases: list[dict], swap_cases: list[dict] | None, model: str, base_url: str | None, api_key: str | None,
            conditions: tuple[str, ...], phases: tuple[str, ...] | None = None, mock: bool = False,
            lookup_cases: list[dict] | None = None) -> list[dict]:
    config.MODEL = model
    if mock:
        client = MockClient()
    else:
        kw: dict = {"api_key": api_key or "local"}
        if base_url:
            kw["base_url"] = base_url
        client = OpenAI(**kw)
    own_by_id = {q["id"]: q for c in (lookup_cases or cases) for qs in c["phases"].values() for q in qs}
    swap_by_case = {c["id"]: c for c in (swap_cases or [])}
    out = []
    for i, case in enumerate(cases, 1):
        print(f"\n{'=' * 60}\nCase {i}/{len(cases)}: {case['title']}\n{'=' * 60}", flush=True)
        out += run_case(case, swap_by_case.get(case["id"]), own_by_id, client, conditions, phases)
    return out


def summarize(records: list[dict]) -> dict:
    """Accuracy per (phase, condition); Brier score and base-rate skill for forecast items."""
    from src.analysis import _wilson_ci
    summary: dict = {}
    for r in records:
        summary.setdefault(r["phase"], {}).setdefault(r["condition"], []).append(r)
    out: dict = {}
    for phase, conds in summary.items():
        out[phase] = {}
        for cond, rs in conds.items():
            n = len(rs)
            if rs[0].get("forecast_outcome") is not None:
                scored = [r for r in rs if r["forecast_prob"] is not None]
                brier = sum((r["forecast_prob"] - r["forecast_outcome"]) ** 2 for r in scored) / len(scored) if scored else None
                out[phase][cond] = {"n": n, "scored": len(scored), "brier": None if brier is None else round(brier, 4)}
            else:
                k = sum(bool(r["correct"]) for r in rs)
                d = {"n": n, "acc": round(k / n, 3), "acc_ci": _wilson_ci(k, n), "parse_errors": sum(r["parse_error"] for r in rs)}
                if cond == "swap":
                    d["tracks_donor"] = sum(bool(r.get("tracks_donor")) for r in rs)
                if cond in ("flip_label", "flip_window"):
                    d["follows_flip"] = sum(bool(r.get("follows_flip")) for r in rs)
                out[phase][cond] = d
    return out
