"""
LLM-drafts MCQ items from verified LUMIERE facts (src/lumiere_facts.py output).

Uses an existing proprietary model from config/models.py (default: GPT-5,
direct OpenAI API — no LiteLLM proxy needed) purely for its client wiring, the
same way src/evaluator.py does. No new model-serving infrastructure.

Runs one call per (patient, phase), in causal order, feeding prior phases'
drafted Q/A as authoring-time chain context so the chain reads coherently
end-to-end. Output is written per patient to data/lumiere/drafts/<id>.json,
already shaped like the OmniBrainBench flat-question schema plus the
additional fields lumiere_loader.py needs (patient_id, timepoint,
fact_provenance, review_status, needs_expert_judgment).
"""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

from openai import OpenAI

import config
import config.lumiere as lcfg
from config.models import MODEL_MAP
from src.lumiere_leakage import find_leaks
from src.lumiere_prompts import build_draft_prompt

LETTERS = "ABCDE"


def _call_model(client: OpenAI, model: str, messages: list[dict], label: str = "") -> str:
    """Same retry pattern as src/evaluator.py::_call_model, kept as a small
    local copy so this module doesn't depend on evaluator.py internals."""
    for attempt in range(config.API_RETRY_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages,
                max_tokens=config.MAX_TOKENS, temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            is_last = attempt == config.API_RETRY_ATTEMPTS - 1
            print(f"  [API error{f' ({label})' if label else ''}] attempt {attempt+1}: {e}")
            if is_last:
                return ""
            time.sleep(config.API_RETRY_DELAY * (2 ** attempt))
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


def build_client(model_name: str = "GPT-5") -> tuple[OpenAI, str]:
    model_cfg = MODEL_MAP[model_name]
    kwargs = {}
    if model_cfg.get("base_url"):
        kwargs["base_url"] = model_cfg["base_url"]
    kwargs["api_key"] = model_cfg.get("api_key") or None
    client = OpenAI(**{k: v for k, v in kwargs.items() if v is not None})
    return client, model_cfg["model"]


def _timepoint_for_phase(facts: dict, phase: str) -> str:
    lil = facts["phase_facts"]["LIL"]
    if phase == "AIA":
        return lil["baseline"]["timepoint_id"]
    if phase in ("LIL", "DSCR"):
        return lil["followup"]["timepoint_id"]
    return facts["followup_timepoint"]


LEAK_RETRIES = 8  # leak-free mode: violations are fed back to the drafter, so allow a few more attempts
LENGTH_RATIO_MAX = 1.05  # correct option may be at most 5% longer than the LONGEST distractor
LENGTH_RETRIES = 5


HEDGE = ("distinguish", "repeat", "follow-up", "review", "pseudoprogression", "reassess", "confirm", "before")
ABSOLUTE = ("immediately", "definitively", "directly", "without", "regardless", "always", "only", "solely", "must")


def _cue_biased(options: dict, answer: str) -> bool:
    """True if a hedge-minus-absolute keyword guesser would single out the correct option
    (the TCM wording cue; tools/check_option_bias.py). Only enforced for TCM."""
    score = {k: sum(w in v.lower() for w in HEDGE) - sum(w in v.lower() for w in ABSOLUTE)
             for k, v in options.items()}
    return score[answer] > max(v for k, v in score.items() if k != answer)


def _biased(phase: str, options: dict, answer: str) -> bool:
    return _length_biased(options, answer) or (phase == "TCM" and _cue_biased(options, answer))


def _length_biased(options: dict, answer: str) -> bool:
    """True if the correct option is longer than the longest distractor by >5% — the cue
    a length-only guesser exploits (tools/check_option_bias.py)."""
    lens = {k: len(v) for k, v in options.items()}
    others = [n for k, n in lens.items() if k != answer]
    return lens[answer] > LENGTH_RATIO_MAX * max(others)


def draft_patient_chain(patient_id: str, facts: dict, client: OpenAI, model: str,
                        only_phases: set[str] | None = None,
                        existing: list[dict] | None = None,
                        leak_free: bool = False) -> list[dict]:
    """only_phases: re-draft just these phases; every other phase is carried over
    unchanged from `existing` (and still fed to later phases as chain context).
    leak_free: use the v3 instructions and retry (with the violations fed back) until
    src/lumiere_leakage.find_leaks passes; an item still leaking after LEAK_RETRIES is
    kept with its reasons in "leak_check" so the build report surfaces it."""
    chain_context: list[dict] = []
    questions: list[dict] = []
    kept = {q["id"].split("_")[-1]: q for q in (existing or [])}

    for phase in config.PHASES:
        phase_facts = facts["phase_facts"].get(phase)
        if not phase_facts:
            continue

        if only_phases is not None and phase not in only_phases:
            if phase in kept:
                q = kept[phase]
                questions.append(q)
                chain_context.append({"phase": phase, "question": q["question"],
                                      "answer": q["correct_answer"],
                                      "answer_text": q["correct_answer_text"]})
            continue

        base_messages = build_draft_prompt(patient_id, phase, phase_facts, chain_context, leak_free=leak_free)
        messages = base_messages
        parsed = options = answer = None
        leaks: list[str] = []
        for attempt in range(LEAK_RETRIES if leak_free else LENGTH_RETRIES):
            raw = _call_model(client, model, messages, label=f"{patient_id}/{phase}")
            parsed = _parse_json(raw, ["question", "options", "answer"])
            if parsed is None:
                break
            answer = parsed["answer"].strip().upper()
            options = {k: v for k, v in parsed["options"].items() if k in LETTERS}
            if answer not in options or not (3 <= len(options) <= 5):
                break
            leaks = find_leaks(phase, parsed["question"], options, facts) if leak_free else []
            if leaks:
                print(f"  [retry] {patient_id}/{phase}: leaks {leaks[:3]} ({attempt+1}/{LEAK_RETRIES})")
                messages = base_messages + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": "That draft breaks the CHAIN RULE: " + "; ".join(leaks)
                     + ". Rewrite the whole item so none of these appear. Respond with the JSON only."},
                ]
                continue
            if not _biased(phase, options, answer):
                break
            messages = base_messages
            print(f"  [retry] {patient_id}/{phase}: correct option is length/wording-biased ({attempt+1}/{LENGTH_RETRIES})")
        if parsed is None:
            print(f"  [skip] {patient_id}/{phase}: draft parse failed")
            continue
        if answer not in options or not (3 <= len(options) <= 5):
            print(f"  [skip] {patient_id}/{phase}: invalid options/answer shape")
            continue

        q = {
            "id": f"{patient_id}_{phase}",
            "question": parsed["question"],
            "options": options,
            "correct_answer": answer,
            "correct_answer_text": options[answer],
            "task_label": lcfg.LUMIERE_TASK_LABEL_MAP[phase],
            "clinical_phase": config.PHASE_NAMES[phase],
            "patient_id": patient_id,
            "timepoint": _timepoint_for_phase(facts, phase),
            "facts_used": phase_facts,
            "distractor_rationale": parsed.get("distractor_rationale", ""),
            "distractor_confidence": parsed.get("distractor_confidence", "high"),
            "needs_expert_judgment": bool(phase_facts.get("needs_expert_judgment", phase in ("PJRF", "TCM"))),
            "review_status": "pending",
            "_image_path": "",  # filled in by lumiere_loader.py from rendered slices
            "_image_dir": "",
        }
        if leak_free:
            q["leak_check"] = leaks
        questions.append(q)
        chain_context.append({
            "phase": phase,
            "question": q["question"],
            "answer": answer,
            "answer_text": q["correct_answer_text"],
        })
        time.sleep(0.3)

    return questions


_RESECTION = {"CRET": "complete resection of the enhancing tumor",
              "PRET": "partial resection of the enhancing tumor"}


def _week(tp: str) -> int:
    return int(tp.split("-")[1])


def _less_than_3_months(patient_id: str, timepoint: str) -> bool:
    path = Path(lcfg.LUMIERE_DATA_DIR) / "tabular" / "LUMIERE-ExpertRating-v202211.csv"
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["Patient"] == patient_id and row["Date"] == timepoint:
                return row["LessThan3Months"].strip().lower() == "x"
    return False


_REPORT_SUBS = [
    (re.compile(r"\s*\(PD according to clinic\)", re.I), ""),   # names a RANO label -> would leak the answer
    (re.compile(r"^Less than 3 months,\s*", re.I), ""),         # stated by the template's own 3-month line
    (re.compile(r"T2-Progr\.?"), "T2/FLAIR progression"),
    (re.compile(r"\bwith Avastin\b", re.I), "on bevacizumab (Avastin)"),
    (re.compile(r"\bL\.:\s*"), "lesion(s): "),
    (re.compile(r"\bL\.(?=\s|,|$)"), "lesion"),
    (re.compile(r"(\d+)mm x (\d+)mm"), r"\1 mm x \2 mm"),
    (re.compile(r"\s{2,}"), " "),
]


def _report_findings(rationale: str | None) -> str | None:
    """The expert rater's recorded findings (LUMIERE 'Rating rationale'), abbreviations expanded,
    RANO labels removed. The rating often rests on evidence the rendered CT1 slice can't show
    (T2/FLAIR progression, new or non-measurable lesions, comparison to the nadir) — without it
    most DSCR items were unanswerable from what the model sees (only ~18/52 ratings agree with
    the visible volume change)."""
    if not rationale:
        return None
    text = rationale.strip()
    for pat, rep in _REPORT_SUBS:
        text = pat.sub(rep, text)
    text = text.strip(" ,")
    return text[0].upper() + text[1:] if text else None


def dscr_leak_free_stem(patient_id: str, facts: dict) -> str:
    """Fixed-template DSCR stem (no LLM): only non-imaging clinical facts from the LUMIERE tables.
    LUMIERE has no steroid/neurological-status fields, so none are stated (v2 stems invented them)."""
    lil = facts["phase_facts"]["LIL"]
    base_tp, follow_tp = lil["baseline"]["timepoint_id"], lil["followup"]["timepoint_id"]
    post_ops = [d for d in facts["all_dscr_facts"] if d["rating_code"] == "Post-Op"]
    surgery = "surgical resection"
    if post_ops and post_ops[0].get("rationale") in _RESECTION:
        surgery = f"surgical resection ({_RESECTION[post_ops[0]['rationale']]})"
    # scan timing relative to surgery is clinical context, and RANO measures against the post-op scan
    base_code = next((d["rating_code"] for d in facts["all_dscr_facts"] if d["timepoint_id"] == base_tp), None)
    base_note = {"Pre-Op": ", pre-operative", "Post-Op": ", post-operative"}.get(base_code, "")
    re_resected = any(_week(base_tp) < _week(d["timepoint_id"]) <= _week(follow_tp) for d in post_ops[1:])
    stem = (f"{patient_id} has glioblastoma and was treated with {surgery} followed by temozolomide "
            f"chemoradiation (Stupp protocol)"
            + (", with a re-resection between these two scans" if re_resected else "")
            + f". You are shown the baseline ({base_tp}{base_note}) and follow-up ({follow_tp}) MRI.")
    if _less_than_3_months(patient_id, follow_tp):
        stem += " The follow-up scan was acquired within 3 months of completing radiotherapy."
    if report := _report_findings(facts["phase_facts"]["DSCR"].get("rationale")):
        stem += f' Radiology report findings at {follow_tp}: "{report}."'
    return stem + (f" Using the images and your earlier assessment of this patient, what is the RANO "
                   f"response category at {follow_tp}?")


def refresh_dscr_stems(item_set: str = "v3") -> None:
    """Re-apply dscr_leak_free_stem() to an existing set's DSCR items in place (drafts + reviewed),
    leaving every other item untouched."""
    root = Path(lcfg.ITEM_SETS[item_set]["dir"])
    facts_dir = Path(lcfg.ITEM_SETS[item_set]["facts_dir"])
    for sub in ("drafts", "reviewed"):
        for path in sorted((root / sub).glob("Patient-*.json")):
            facts = json.loads((facts_dir / path.name).read_text())
            items = json.loads(path.read_text())
            for q in items:
                if q["id"].endswith("_DSCR"):
                    q["question"] = dscr_leak_free_stem(path.stem, facts)
                    q["leak_check"] = find_leaks("DSCR", q["question"], q["options"], facts)
            path.write_text(json.dumps(items, indent=2, default=str))
    print(f"Refreshed DSCR stems in {root}")


def build_leak_free_set(model_name: str, patient_ids: list[str], item_set: str = "v3",
                        force: bool = False) -> None:
    """Build a leak-free item set from the v2 drafts (data/lumiere/drafts/) into
    ITEM_SETS[item_set]["dir"]/{drafts,reviewed}/. AIA carried over; LIL carried over unless it
    leaks (then re-drafted); DSCR stem replaced by dscr_leak_free_stem() with its RANO-label options
    and answer kept, and shown both images; PJRF + TCM re-drafted in leak-free mode. Facts come from the
    set's own facts_dir (v3: post-op baseline) — LIL is re-drafted too whenever its baseline changed.
    Skips patients whose v3 file already exists with no leaks (unless force)."""
    facts_dir = Path(lcfg.ITEM_SETS[item_set]["facts_dir"])
    root = Path(lcfg.ITEM_SETS[item_set]["dir"])
    (root / "drafts").mkdir(parents=True, exist_ok=True)
    (root / "reviewed").mkdir(parents=True, exist_ok=True)
    client, model = build_client(model_name)
    for pid in patient_ids:
        out_path = root / "drafts" / f"{pid}.json"
        if out_path.exists() and not force:
            done = json.loads(out_path.read_text())
            if len(done) == 5 and not any(q.get("leak_check") for q in done):
                print(f"  [skip] {pid}: already built and clean")
                continue
        src = Path(lcfg.LUMIERE_DATA_DIR) / "drafts" / f"{pid}.json"
        fpath = facts_dir / f"{pid}.json"
        if not (src.exists() and fpath.exists()):
            print(f"  [skip] {pid}: missing v2 draft or facts")
            continue
        facts = json.loads(fpath.read_text())
        existing = {q["id"].split("_")[-1]: dict(q) for q in json.loads(src.read_text())}
        todo = {"PJRF", "TCM"}
        lil = existing.get("LIL")
        lil_facts = facts["phase_facts"]["LIL"]
        if lil and (find_leaks("LIL", lil["question"], lil["options"], facts)
                    or lil["facts_used"]["baseline"]["timepoint_id"] != lil_facts["baseline"]["timepoint_id"]):
            todo.add("LIL")
        if "AIA" in existing:
            existing["AIA"]["timepoint"] = lil_facts["baseline"]["timepoint_id"]
        if "DSCR" in existing:
            existing["DSCR"]["question"] = dscr_leak_free_stem(pid, facts)
            existing["DSCR"]["image_timepoints"] = [lil_facts["baseline"]["timepoint_id"],
                                                    lil_facts["followup"]["timepoint_id"]]
        print(f"Building {item_set} for {pid} (re-drafting {sorted(todo)})…")
        questions = draft_patient_chain(pid, facts, client, model, todo, list(existing.values()), leak_free=True)
        got = {q["id"] for q in questions}
        missing = [q for q in existing.values() if q["id"] not in got]
        for q in missing:  # draft failed outright: keep the v2 item but flag it, never silently pass it off as clean
            q["leak_check"] = find_leaks(q["id"].split("_")[-1], q["question"], q["options"], facts) or ["draft failed"]
        questions += missing
        questions.sort(key=lambda q: config.PHASES.index(q["id"].split("_")[-1]))
        for q in questions:
            q.setdefault("leak_check", find_leaks(q["id"].split("_")[-1], q["question"], q["options"], facts))
        out_path.write_text(json.dumps(questions, indent=2, default=str))
        (root / "reviewed" / f"{pid}.json").write_text(json.dumps(questions, indent=2, default=str))
        flagged = [q["id"] for q in questions if q["leak_check"]]
        print(f"  -> {out_path}" + (f"  STILL LEAKING: {flagged}" if flagged else "  (clean)"))


def draft_all(patient_ids: list[str], model_name: str = "GPT-5",
              facts_dir: Path | None = None, out_dir: Path | None = None,
              force: bool = False, only_phases: set[str] | None = None) -> None:
    facts_dir = facts_dir or Path(lcfg.LUMIERE_DATA_DIR) / "facts"
    out_dir = out_dir or Path(lcfg.LUMIERE_DATA_DIR) / "drafts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Skip patients already drafted — avoids re-spending API credit when
    # re-running against an expanded patient list (see plan: idempotency fix).
    # An empty [] file means every phase failed last time (e.g. the LLM proxy
    # was down) — that must NOT count as "done", or a transient outage would
    # permanently strand those patients with no drafted items.
    to_process = []
    for pid in patient_ids:
        out_path = out_dir / f"{pid}.json"
        if out_path.exists() and not force and only_phases is None:
            existing = json.loads(out_path.read_text())
            if existing:
                print(f"  [skip] draft already exists for {pid} ({len(existing)} items)")
                continue
            print(f"  [retry] {pid} had an empty/failed draft — redrafting")
        to_process.append(pid)

    if not to_process:
        print("Nothing new to draft.")
        return

    client, model = build_client(model_name)
    for pid in to_process:
        fpath = facts_dir / f"{pid}.json"
        if not fpath.exists():
            print(f"  [skip] no facts for {pid}")
            continue
        facts = json.loads(fpath.read_text())
        print(f"Drafting chain for {pid}…")
        src_path = Path(lcfg.LUMIERE_DATA_DIR) / "drafts" / f"{pid}.json"
        existing = json.loads(src_path.read_text()) if only_phases and src_path.exists() else None
        questions = draft_patient_chain(pid, facts, client, model, only_phases, existing)
        out_path = out_dir / f"{pid}.json"
        out_path.write_text(json.dumps(questions, indent=2, default=str))
        print(f"  -> {out_path} ({len(questions)} phases drafted)")


def redraft_biased(model_name: str, drafts_dir: Path, phases: set[str]) -> None:
    """Re-draft, in place, only the `phases` items in drafts_dir that are still length-biased
    (or missing). Other items are left exactly as they are."""
    facts_dir = Path(lcfg.LUMIERE_DATA_DIR) / "facts"
    client, model = build_client(model_name)
    for path in sorted(drafts_dir.glob("Patient-*.json")):
        pid = path.stem
        existing = json.loads(path.read_text())
        have = {q["id"].split("_")[-1]: q for q in existing}
        todo = {ph for ph in phases
                if ph not in have or _biased(ph, have[ph]["options"], have[ph]["correct_answer"])}
        facts_path = facts_dir / f"{pid}.json"
        if not todo or not facts_path.exists():
            continue
        print(f"Re-drafting {sorted(todo)} for {pid}…")
        facts = json.loads(facts_path.read_text())
        questions = draft_patient_chain(pid, facts, client, model, todo, existing)
        # draft_patient_chain drops a phase it could not draft; keep the old item then
        got = {q["id"] for q in questions}
        questions += [q for q in existing if q["id"] not in got]
        questions.sort(key=lambda q: config.PHASES.index(q["id"].split("_")[-1]))
        path.write_text(json.dumps(questions, indent=2, default=str))


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="LLM-draft LUMIERE MCQ items from facts")
    p.add_argument("--patients", type=str, default=None,
                    help="comma-separated patient IDs; default: all in data/lumiere/facts/")
    p.add_argument("--model", type=str, default="GPT-5")
    p.add_argument("--force", action="store_true", help="re-draft even if output already exists")
    p.add_argument("--phases", type=str, default=None,
                    help="comma-separated phases to re-draft (e.g. PJRF,TCM); others are carried over "
                         "from data/lumiere/drafts/. Use with --out-dir to avoid overwriting.")
    p.add_argument("--out-dir", type=str, default=None)
    p.add_argument("--fix-biased", action="store_true",
                    help="re-draft only still length-biased --phases items, in place in --out-dir")
    p.add_argument("--base-url", type=str, default=None, help="override the model's base_url")
    p.add_argument("--leak-free-set", type=str, default=None,
                    help="build a leak-free item set (e.g. v3, see config/lumiere.py ITEM_SETS) from data/lumiere/drafts/")
    p.add_argument("--refresh-dscr", type=str, default=None, metavar="ITEM_SET",
                    help="re-apply the DSCR template stems in an existing item set (e.g. v3), in place")
    args = p.parse_args()
    if args.base_url:
        MODEL_MAP[args.model]["base_url"] = args.base_url

    if args.fix_biased:
        redraft_biased(args.model, Path(args.out_dir), set(args.phases.split(",")))
        raise SystemExit(0)

    if args.patients:
        ids = args.patients.split(",")
    else:
        facts_dir = Path(lcfg.LUMIERE_DATA_DIR) / "facts"
        ids = sorted(p.stem for p in facts_dir.glob("Patient-*.json"))

    if args.refresh_dscr:
        refresh_dscr_stems(args.refresh_dscr)
        raise SystemExit(0)
    if args.leak_free_set:
        build_leak_free_set(args.model, ids, args.leak_free_set, force=args.force)
        raise SystemExit(0)

    draft_all(ids, model_name=args.model, force=args.force,
              out_dir=Path(args.out_dir) if args.out_dir else None,
              only_phases=set(args.phases.split(",")) if args.phases else None)
