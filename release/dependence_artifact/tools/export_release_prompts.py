"""
Export every single-question prompt of the v4 intervention conditions exactly as it is built for the models (no model is called).

Runs src.v4_conditions.run_all with a recording client in place of the offline mock and writes one JSON line per (case, phase,
condition) with the system message, the user text and the number of images; image bytes are replaced by a placeholder.
Chain-run prompts are not exported here: they paste the model's own earlier answers into later prompts, so they exist only
after a model has answered (src/prompts.py::build_main_prompt builds them).

  python -m tools.export_release_prompts --out release/anon_artifact/prompts.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import v4_conditions as vc
from src.lumiere_loader import load_lumiere

CAPTURED: list[list[dict]] = []
_ORIG_CREATE = vc.MockClient._Chat._Completions.create


class RecordingClient:
    class _Chat:
        class _Completions:
            @staticmethod
            def create(model, messages, **kw):
                CAPTURED.append(json.loads(json.dumps(messages, default=str)))
                return _ORIG_CREATE(model, messages, **kw)
        completions = _Completions()
    chat = _Chat()


def _scrub(messages: list[dict]) -> tuple[str, str, int]:
    system, user_txt, n_img = "", [], 0
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            (user_txt if m["role"] != "system" else [system]).append(content) if m["role"] != "system" else None
            if m["role"] == "system":
                system = content
            continue
        for part in content:
            if part.get("type") == "text":
                user_txt.append(part["text"])
            elif "image" in str(part.get("type", "")):
                n_img += 1
                user_txt.append("[IMAGE]")
    return system, "\n".join(user_txt), n_img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="release/anon_artifact/prompts.jsonl")
    args = ap.parse_args()
    cases = load_lumiere(n_cases=None, min_phases=2, include_unreviewed=True, item_set="v4")
    swap_cases = load_lumiere(n_cases=None, min_phases=2, include_unreviewed=True, item_set="v4", counterfactual_images=True)
    vc.MockClient = RecordingClient
    records = vc.run_all(cases, swap_cases, model="prompt-export", base_url=None, api_key=None, conditions=vc.CONDITIONS, mock=True)
    if len(records) != len(CAPTURED):
        raise SystemExit(f"{len(records)} records but {len(CAPTURED)} prompts: the one-call-per-record assumption fails")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for rec, msgs in zip(records, CAPTURED):
            system, user, n_img = _scrub(msgs)
            f.write(json.dumps({"case_id": rec["case_id"], "phase": rec["phase"], "condition": rec["condition"],
                                "n_images": n_img, "system": system, "user": user}) + "\n")
    print(f"wrote {len(records)} prompts to {out}")


if __name__ == "__main__":
    main()
