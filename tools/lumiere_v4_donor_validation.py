"""
Protocol validation for the donor-swap test (reviewer request, T-R10a).

Does the donor-key permutation test actually separate *correct, donor-specific tracking* from a
*generic response to any image*? We answer by running the paper's own estimators
(``tools.lumiere_v4_stats.e2`` and ``tools.lumiere_v4_supplement.donor_dependence``) on synthetic
predictors whose behaviour is known by construction, on the real items and the real donor assignment:

  constant       always answers the modal class (own = text = swap).                 -> no gain, not separable
  random         answers a uniformly random option in every condition.               -> no gain, not separable
  image_shift    text -> modal class; own/swap -> one fixed favoured class,           -> gain can be > 0 but
                 the same regardless of which donor image is shown.                      NOT separable (generic)
  tracker(rho)   text -> modal class; own -> own key w.p. rho; swap -> the shown        -> gain > 0 and separable
                 donor's key w.p. rho (else random).                                      (detection falls with rho)

For each predictor we report, over ``--sims`` simulation seeds, the median donor-tracking gain and the
share of seeds whose permutation p < .05 (the protocol's detection rate). ``--assignments`` repeats the
tracker/image_shift on randomly re-drawn valid donor assignments to show stability.

  python -m tools.lumiere_v4_donor_validation            # DSCR by default; writes results/lumiere_v4_donor_validation.json
  python -m tools.lumiere_v4_donor_validation --phases AIA LIL DSCR --sims 50
No model is called; this is pure re-analysis with controlled inputs.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

from src.lumiere_loader import _shuffle_options
import tools.lumiere_v4_stats as st
import tools.lumiere_v4_supplement as sup

V4 = Path("data/lumiere/v4")
PAIRS = json.loads((V4 / "counterfactual_pairs.json").read_text())


def load_item(c: str, ph: str):
    items = json.loads((V4 / "reviewed" / f"{c}.json").read_text())
    it = next(x for x in items if x["id"].endswith("_" + ph))
    if it.get("ordered_options"):
        return dict(it["options"]), it["correct_answer"]
    return _shuffle_options(it["options"], it["correct_answer"], it["id"])


def build_table(pairs: dict, ph: str) -> dict:
    """Per recipient: shuffled options (as the model saw them), own key, and the assigned donor's key."""
    rows = {}
    for c, v in sorted(pairs.items()):
        d = v.get("detail", {}).get(ph)
        if not d:
            continue
        sh, corr = load_item(c, ph)
        dkl = next((L for L in sh if sh[L] == d["donor_key"]), None)
        if dkl is None:
            continue  # donor key not an option here (should not happen given full option sets)
        rows[c] = {"sh": sh, "letters": list(sh), "corr": corr, "own_text": sh[corr],
                   "donor": d["partner"], "dk_text": d["donor_key"], "dk_letter": dkl}
    return rows


def _letter_of(row, text, rng):
    sh = row["sh"]
    return next((L for L in sh if sh[L] == text), rng.choice(row["letters"]))


def predict(kind: str, row: dict, cond: str, rng: random.Random, cls: dict, rho: float) -> str:
    # cls holds the class texts: modal own class, and the most/least common DONOR class
    if kind == "constant":
        return _letter_of(row, cls["modal"], rng)
    if kind == "random":
        return rng.choice(row["letters"])
    if kind == "image_shift":
        # generic response to any image: answer the most common donor class when an image is present,
        # a rarer class otherwise -- produces a positive gain that is not donor-specific
        return _letter_of(row, cls["prior"] if cond == "text" else cls["favoured"], rng)
    if kind == "tracker":
        if cond == "text":
            return _letter_of(row, cls["modal"], rng)
        target = row["corr"] if cond == "own" else row["dk_letter"]
        return target if rng.random() < rho else rng.choice(row["letters"])
    raise ValueError(kind)


def make_recs(rows: dict, ph: str, kind: str, seed: int, rho: float = 1.0) -> dict:
    rng = random.Random(seed)
    dk_counts = Counter(r["dk_text"] for r in rows.values()).most_common()
    cls = {"modal": Counter(r["own_text"] for r in rows.values()).most_common(1)[0][0],
           "favoured": dk_counts[0][0], "prior": dk_counts[-1][0]}
    recs = {}
    for c, row in rows.items():
        for cond in ("own", "text", "swap"):
            recs[(c, ph, cond)] = {"model_answer": predict(kind, row, cond, rng, cls, rho),
                                   "correct_answer": row["corr"], "donor_key_letter": row["dk_letter"],
                                   "donor": row["donor"], "donor_key_text": row["dk_text"], "own_key_text": row["own_text"]}
    return recs


def evaluate(recs: dict, ph: str) -> dict:
    """Run the paper's own E2 gain and donor-key permutation on a set of synthetic records."""
    e2 = st.e2(recs, np.random.default_rng(st.SEED)).get(ph, {})
    dd = sup.donor_dependence(recs, np.random.default_rng(st.SEED), n_perm=5000).get(ph, {})
    return {"gain": e2.get("gain"), "gain_ci": e2.get("gain_ci"), "gain_p": e2.get("gain_p"),
            "perm_p": dd.get("perm_p"), "n": e2.get("n")}


def random_assignment(rows: dict, seed: int) -> dict:
    """A re-drawn valid donor assignment: every recipient gets a donor whose key differs from its own."""
    rng = random.Random(seed)
    cs = list(rows)
    for _ in range(200):
        donors = cs[:]
        rng.shuffle(donors)
        if all(rows[d]["own_text"] != rows[c]["own_text"] and d != c for c, d in zip(cs, donors)):
            break
    else:
        return rows  # fall back to the original if no clean derangement found
    new = {}
    for c, d in zip(cs, donors):
        r = dict(rows[c]); r["donor"] = d; r["dk_text"] = rows[d]["own_text"]
        r["dk_letter"] = next((L for L in r["sh"] if r["sh"][L] == r["dk_text"]), r["dk_letter"])
        new[c] = r
    return new


def run_phase(ph: str, sims: int, assignments: int) -> dict:
    rows = build_table(PAIRS, ph)
    specs = [("constant", 1.0), ("random", 1.0), ("image_shift", 1.0),
             ("tracker", 1.0), ("tracker", 0.7), ("tracker", 0.4)]
    out = {"n_recipients": len(rows), "predictors": {}}
    for kind, rho in specs:
        name = kind if kind != "tracker" else f"tracker_rho{rho:g}"
        gains, perms = [], []
        for s in range(sims):
            r = evaluate(make_recs(rows, ph, kind, seed=1000 * s + 7, rho=rho), ph)
            gains.append(r["gain"]); perms.append(r["perm_p"])
        out["predictors"][name] = {
            "gain_median": float(np.median(gains)), "gain_iqr": [float(np.percentile(gains, 25)), float(np.percentile(gains, 75))],
            "perm_p_median": float(np.median(perms)), "detection_rate": float(np.mean([p < 0.05 for p in perms])), "sims": sims}
    # stability across re-drawn assignments (genuine tracker vs generic shift)
    stab = {}
    for kind, rho in [("tracker", 1.0), ("image_shift", 1.0)]:
        name = kind if kind != "tracker" else f"tracker_rho{rho:g}"
        g2, p2 = [], []
        for a in range(assignments):
            ar = random_assignment(rows, seed=500 * a + 3)
            r = evaluate(make_recs(ar, ph, kind, seed=13, rho=rho), ph)
            g2.append(r["gain"]); p2.append(r["perm_p"])
        stab[name] = {"gain_median": float(np.median(g2)), "detection_rate": float(np.mean([p < 0.05 for p in p2])), "assignments": assignments}
    out["across_assignments"] = stab
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", nargs="+", default=["DSCR"])
    ap.add_argument("--sims", type=int, default=50)
    ap.add_argument("--assignments", type=int, default=20)
    ap.add_argument("--out", default="results/lumiere_v4_donor_validation.json")
    args = ap.parse_args()
    res = {ph: run_phase(ph, args.sims, args.assignments) for ph in args.phases}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1))
    for ph, r in res.items():
        print(f"\n=== {ph}  ({r['n_recipients']} recipients, {args.sims} sims) ===")
        print(f"  {'predictor':<16} {'gain(med)':>10} {'perm_p(med)':>12} {'detect<.05':>11}")
        for name, d in r["predictors"].items():
            print(f"  {name:<16} {d['gain_median']:>9.1f} {d['perm_p_median']:>12.3f} {d['detection_rate']:>10.0%}")
        print("  across re-drawn assignments:")
        for name, d in r["across_assignments"].items():
            print(f"    {name:<14} gain(med)={d['gain_median']:.1f}  detect<.05={d['detection_rate']:.0%}")


if __name__ == "__main__":
    main()
