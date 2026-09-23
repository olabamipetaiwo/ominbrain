"""
Build deterministic patient-pairing for the counterfactual-image test (step 4 of the
2026-09-22 non-grounding investigation, scoped 2026-09-23).

Purpose: for each v3 patient, assign a "counterfactual partner" — a different real
patient whose own rendered slices will be substituted in place of the original
patient's images at load time (src/lumiere_loader.py), while every text field (stem,
options, chain context, image labels) stays exactly as the original patient's. This
tests whether models' answers change when the actual pixels contradict the (unchanged)
text — a direct test of image-grounding, not just an ablation.

Pairing rule: every patient is paired with a partner whose LIL volume-change direction
is OPPOSITE (v3's real split, per paper/update.md: 20 up / 32 down) — the single
cleanest, always-available signal in the dataset. This is not optimized jointly against
DSCR's RANO label (that would require a more complex matching for a marginal gain); the
resulting overlap with differing RANO labels is measured and reported, not engineered.

Usage: python -m tools.build_lumiere_counterfactual_pairs
Output: data/lumiere/v3/counterfactual_pairs.json
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import config.lumiere as lcfg

FACTS_DIR = Path(lcfg.ITEM_SETS["v3"]["facts_dir"])
OUT_PATH = Path(lcfg.ITEM_SETS["v3"]["dir"]) / "counterfactual_pairs.json"
SEED = 42


def _load_patient_facts() -> dict[str, dict]:
    out = {}
    for fpath in sorted(FACTS_DIR.glob("*.json")):
        d = json.loads(fpath.read_text())
        pf = d.get("phase_facts", {})
        lil = pf.get("LIL", {})
        dscr = pf.get("DSCR", {})
        pct = lil.get("volume_change_pct")
        rating = dscr.get("rating_code")
        if pct is None or rating is None:
            print(f"WARNING: {d['patient_id']} missing LIL volume_change_pct or DSCR "
                  f"rating_code — excluded from pairing (pct={pct}, rating={rating}).")
            continue
        out[d["patient_id"]] = {"direction": "up" if pct > 0 else "down", "rano": rating}
    return out


def build_pairs() -> dict[str, dict]:
    facts = _load_patient_facts()
    ups = sorted(p for p, f in facts.items() if f["direction"] == "up")
    downs = sorted(p for p, f in facts.items() if f["direction"] == "down")

    rng = random.Random(SEED)
    rng.shuffle(ups)
    rng.shuffle(downs)

    pairs: dict[str, dict] = {}
    # Every "up" patient gets a "down" partner, cycling through downs; every "down"
    # patient gets an "up" partner, cycling through ups. Guarantees 100% opposite-
    # direction pairing (the group-size mismatch, 20 vs 32, just means ups get reused
    # as partners more than once — fine, this is a pairing FOR images, not a 1:1
    # matching, and reuse doesn't leak anything between the reused pairs' own items).
    for i, p in enumerate(ups):
        partner = downs[i % len(downs)]
        pairs[p] = {"partner": partner, "own_direction": "up", "partner_direction": "down",
                    "own_rano": facts[p]["rano"], "partner_rano": facts[partner]["rano"]}
    for i, p in enumerate(downs):
        partner = ups[i % len(ups)]
        pairs[p] = {"partner": partner, "own_direction": "down", "partner_direction": "up",
                    "own_rano": facts[p]["rano"], "partner_rano": facts[partner]["rano"]}

    return pairs


def main() -> None:
    pairs = build_pairs()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(pairs, indent=2))

    n = len(pairs)
    rano_diff = sum(1 for v in pairs.values() if v["own_rano"] != v["partner_rano"])
    print(f"Built {n} counterfactual pairs -> {OUT_PATH}")
    print(f"LIL direction: 100% opposite by construction ({n}/{n})")
    print(f"DSCR RANO label also differs (not optimized, measured only): "
          f"{rano_diff}/{n} ({rano_diff / n:.0%})")


if __name__ == "__main__":
    main()
