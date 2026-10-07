"""
Protocol validation for the donor-swap test (reviewer request, T-R10a).

Does the donor-key permutation test actually separate *correct, donor-specific tracking* from a
*generic response to any image*? We answer by running the paper's own estimators
(``tools.lumiere_v4_stats.e2`` and ``tools.lumiere_v4_supplement.donor_dependence``) on synthetic
predictors whose behaviour is known by construction, on the real items and the real donor assignment:

  constant       always answers the modal class (own = text = swap).                 -> no gain, not flagged
  random         answers a uniformly random option in every condition.               -> no gain, not flagged
  image_shift    text -> modal class; own/swap -> one fixed favoured class,           -> gain can be > 0 but
                 the same regardless of which donor image is shown.                      NOT flagged (generic)
  position       text -> modal class; own/swap -> a FIXED option position (letters    -> no-tracking confound
                 are shuffled per item), independent of the donor.                       (false-positive check)
  image_count    text -> modal class; own/swap -> a class chosen by HOW MANY scans    -> no-tracking confound
                 are shown, never by which donor.                                        (false-positive check)
  tracker(rho)   text -> modal class; own -> own key w.p. rho; swap -> the shown        -> gain > 0 and flagged
                 donor's key w.p. rho (else uniform guess).                               (power; detection falls with rho)

The position/image_count predictors are no-tracking confounds: a well-calibrated test must NOT flag them
(detection near the nominal 5%). Note on rho: the guess branch can also land on the donor key, so the EFFECTIVE
probability of emitting the donor's key is rho + (1-rho)/|options| (rho=0.4, 4 options -> 0.55); rho is the
tracking-branch probability, not the donor-answer accuracy.

For each predictor we report, over ``--sims`` simulation seeds, the median donor-tracking gain and the share of
seeds whose permutation p < .05 (the observed detection rate, with a Wilson CI; the nominal threshold is 5%).
``--assignments`` caps how many
GENUINELY DISTINCT, constraint-valid donor assignments (drawn by re-running the real build_pairs under fresh
seeds; see valid_assignments) the stability check uses; it reports how many distinct assignments actually
exist and makes no stability claim when the original is the only valid one.

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
from src.lumiere_v4 import build_pairs
from tools.lumiere_gating_stats import wilson
import tools.lumiere_v4_stats as st
import tools.lumiere_v4_supplement as sup

V4 = Path("data/lumiere/v4")
PAIRS = json.loads((V4 / "counterfactual_pairs.json").read_text())


def load_item(c: str, ph: str):
    items = json.loads((V4 / "reviewed" / f"{c}.json").read_text())
    it = next(x for x in items if x["id"].endswith("_" + ph))
    n_img = len(it.get("image_files") or [])
    if it.get("ordered_options"):
        return dict(it["options"]), it["correct_answer"], n_img
    sh, corr = _shuffle_options(it["options"], it["correct_answer"], it["id"])
    return sh, corr, n_img


def build_table(pairs: dict, ph: str) -> dict:
    """Per recipient: shuffled options (as the model saw them), own key, and the assigned donor's key."""
    rows = {}
    for c, v in sorted(pairs.items()):
        d = v.get("detail", {}).get(ph)
        if not d:
            continue
        sh, corr, n_img = load_item(c, ph)
        dkl = next((L for L in sh if sh[L] == d["donor_key"]), None)
        if dkl is None:
            continue  # donor key not an option here (should not happen given full option sets)
        rows[c] = {"sh": sh, "letters": list(sh), "corr": corr, "own_text": sh[corr], "n_img": n_img,
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
    if kind == "position":
        # DONOR-INDEPENDENT confound: when an image is present, answer a FIXED option position (letters are
        # shuffled per item, so this is a position bias, not a class bias). swap == own, no donor dependence.
        return cls["modal_letter_of"](row) if cond == "text" else row["letters"][0]
    if kind == "image_count":
        # DONOR-INDEPENDENT confound: the answer depends only on HOW MANY scans are shown, never on which donor.
        if cond == "text":
            return _letter_of(row, cls["modal"], rng)
        return _letter_of(row, cls["favoured"] if row.get("n_img", 0) >= cls["img_large"] else cls["prior"], rng)
    if kind == "tracker":
        # tracker(rho): with prob rho emit the shown image's key, else guess uniformly. The random branch can also
        # be correct, so the EFFECTIVE prob of emitting the donor key is rho + (1-rho)/|options| (e.g. rho=0.4,
        # 4 options -> 0.55), not rho. rho is the tracking-branch probability, not the donor-answer accuracy.
        if cond == "text":
            return _letter_of(row, cls["modal"], rng)
        target = row["corr"] if cond == "own" else row["dk_letter"]
        return target if rng.random() < rho else rng.choice(row["letters"])
    raise ValueError(kind)


def make_recs(rows: dict, ph: str, kind: str, seed: int, rho: float = 1.0) -> dict:
    rng = random.Random(seed)
    dk_counts = Counter(r["dk_text"] for r in rows.values()).most_common()
    modal_text = Counter(r["own_text"] for r in rows.values()).most_common(1)[0][0]
    cls = {"modal": modal_text, "favoured": dk_counts[0][0], "prior": dk_counts[-1][0],
           "img_large": max((r.get("n_img", 1) for r in rows.values()), default=1),
           "modal_letter_of": lambda row: _letter_of(row, modal_text, rng)}
    recs = {}
    for c, row in rows.items():
        for cond in ("own", "text", "swap"):
            recs[(c, ph, cond)] = {"model_answer": predict(kind, row, cond, rng, cls, rho),
                                   "correct_answer": row["corr"], "donor_key_letter": row["dk_letter"],
                                   "donor": row["donor"], "donor_key_text": row["dk_text"], "own_key_text": row["own_text"]}
    return recs


def evaluate(recs: dict, ph: str) -> dict:
    """Run the paper's own E2 gain and donor-key permutation on a set of synthetic records.

    Also returns the image-vs-text answer-change rate (own answer differs from the text-only answer; the E1-style
    output-sensitivity diagnostic) so the diagnostics-comparison (reviewer concern 3) can contrast what each
    diagnostic concludes on the SAME predictor: a generic response to image presence raises both the donor gain
    and the answer-change rate (each then reads as image use), yet the permutation does not flag it, whereas a
    genuine donor tracker is flagged by all three."""
    e2 = st.e2(recs, np.random.default_rng(st.SEED)).get(ph, {})
    dd = sup.donor_dependence(recs, np.random.default_rng(st.SEED), n_perm=5000).get(ph, {})
    # image-vs-text answer change over recipients present in both arms (own = image arm, text = no-image arm)
    cases = sorted(c for (c, p, k) in recs if p == ph and k == "own" and (c, ph, "text") in recs)
    chg = (100.0 * np.mean([recs[(c, ph, "own")]["model_answer"] != recs[(c, ph, "text")]["model_answer"]
                            for c in cases])) if cases else float("nan")
    return {"gain": e2.get("gain"), "gain_ci": e2.get("gain_ci"), "gain_p": e2.get("gain_p"),
            "answer_change": float(chg), "perm_p": dd.get("perm_p"), "n": e2.get("n")}


def _items_by_patient() -> dict:
    """All reviewed AIA/LIL/DSCR items per patient in the shape build_pairs expects (correct_answer_text + image_files).

    build_pairs builds all three imaging phases in one call (as the dataset was built), so we pass every phase
    and extract the one we need; passing a single phase would leave the other two empty and break its solver."""
    ibp: dict[str, dict] = {}
    for f in sorted((V4 / "reviewed").glob("Patient-*.json")):
        d = {}
        for it in json.loads(f.read_text()):
            ph = it["id"].split("_")[-1]
            if ph in ("AIA", "LIL", "DSCR") and it.get("image_files") and it.get("correct_answer_text"):
                d[ph] = {"correct_answer_text": it["correct_answer_text"], "image_files": it["image_files"]}
        if d:
            ibp[f.stem] = d
    return ibp


def base_rows(ph: str) -> dict:
    """Per-recipient option structure (shuffled options, own key) for EVERY patient with a `ph` item, no donor.

    Unlike build_table (which is keyed on the fixed original pairs), this covers the whole pool so an alternative
    assignment can be evaluated on whatever recipient set it covers."""
    rows = {}
    for f in sorted((V4 / "reviewed").glob("Patient-*.json")):
        c = f.stem
        try:
            sh, corr, n_img = load_item(c, ph)
        except StopIteration:
            continue
        rows[c] = {"sh": sh, "letters": list(sh), "corr": corr, "own_text": sh[corr], "n_img": n_img}
    return rows


def valid_assignments(ph: str, n_seeds: int = 500) -> tuple[list[dict], int, int]:
    """Distinct, constraint-valid donor assignments for `ph`, OTHER than the original.

    Rather than a hand-rolled derangement, this re-runs the paper's own ``build_pairs`` over the full patient pool
    (distinct key, no self, MATCHING SCAN COUNT, at most two recipients per donor, linear_sum_assignment with seed
    jitter) under fresh seeds and keeps the distinct full solutions. Each draw is evaluated on whatever recipient set
    it covers (build_pairs drops recipients with no feasible donor, so the covered set itself can vary); the donor key
    is read from build_pairs' own output. The original assignment is excluded. Returns
    (distinct assignments as {recipient: {"donor","donor_key"}} dicts, distinct solutions incl. original, seeds tried)."""
    ibp = _items_by_patient()
    orig_key = frozenset((c, v["detail"][ph]["partner"]) for c, v in PAIRS.items() if ph in v.get("detail", {}))
    seen: dict[frozenset, dict] = {}
    for s in range(n_seeds):
        pr = build_pairs(ibp, seed=10_000 + s)
        amap = {c: pr[c]["detail"][ph] for c in pr if ph in pr[c].get("detail", {})}
        key = frozenset((c, amap[c]["partner"]) for c in amap)
        seen.setdefault(key, {c: {"donor": amap[c]["partner"], "donor_key": amap[c]["donor_key"]} for c in amap})
    distinct = [a for k, a in seen.items() if k != orig_key]
    return distinct, len(seen), n_seeds


def rows_under(rows: dict, amap: dict) -> dict:
    """Rebuild the per-recipient table for a given donor assignment {recipient: {"donor","donor_key"}}."""
    new = {}
    for c, info in amap.items():
        if c not in rows:
            continue
        r = dict(rows[c]); r["donor"] = info["donor"]; r["dk_text"] = info["donor_key"]
        r["dk_letter"] = next((L for L in r["sh"] if r["sh"][L] == r["dk_text"]), None)
        if r["dk_letter"] is None:
            continue                       # donor key not an option here (should not happen given full option sets)
        new[c] = r
    return new


def run_phase(ph: str, sims: int, assignments: int) -> dict:
    rows = build_table(PAIRS, ph)
    # constant/random: deterministic/no-image controls.  image_shift/position/image_count: NO-TRACKING confounds that
    # depend on image presence, option position, or scan count but never on which donor -> false-positive calibration.
    # tracker(rho): genuine donor-specific tracking -> power.
    specs = [("constant", 1.0), ("random", 1.0), ("image_shift", 1.0), ("position", 1.0), ("image_count", 1.0),
             ("tracker", 1.0), ("tracker", 0.7), ("tracker", 0.4)]
    out = {"n_recipients": len(rows), "nominal_alpha": 0.05, "predictors": {}}
    for kind, rho in specs:
        name = kind if kind != "tracker" else f"tracker_rho{rho:g}"
        gains, perms, changes = [], [], []
        for s in range(sims):
            r = evaluate(make_recs(rows, ph, kind, seed=1000 * s + 7, rho=rho), ph)
            gains.append(r["gain"]); perms.append(r["perm_p"]); changes.append(r["answer_change"])
        k = int(sum(p < 0.05 for p in perms))
        lo, hi = wilson(k, sims)
        out["predictors"][name] = {
            "gain_median": float(np.median(gains)), "gain_iqr": [float(np.percentile(gains, 25)), float(np.percentile(gains, 75))],
            "answer_change_median": float(np.median(changes)),
            "perm_p_median": float(np.median(perms)), "detection_rate": float(k / sims),
            "detection_ci": [float(lo), float(hi)], "sims": sims}
    # stability across GENUINELY DISTINCT, constraint-valid re-drawn assignments (no silent fallback)
    distinct, n_unique, n_tried = valid_assignments(ph)
    base = base_rows(ph)
    cover = sorted(len(a) for a in distinct)
    stab = {"n_distinct_assignments": len(distinct), "n_unique_incl_original": n_unique, "n_seeds_tried": n_tried,
            "assignment_cover_min": (cover[0] if cover else 0), "assignment_cover_max": (cover[-1] if cover else 0)}
    if len(distinct) < 2:
        stab["note"] = ("the constraint-valid assignment space is degenerate for this phase/cohort "
                        f"({len(distinct)} distinct valid assignment(s) other than the original across {n_tried} seeds); "
                        "assignment stability cannot be meaningfully assessed and no stability claim should be made")
    else:
        use = distinct[:assignments]
        # include the NOISY tracker (the one whose detection rate precedes the stability claim), not only the perfect one
        for kind, rho in [("tracker", 1.0), ("tracker", 0.7), ("tracker", 0.4), ("image_shift", 1.0)]:
            name = kind if kind != "tracker" else f"tracker_rho{rho:g}"
            g2, p2 = [], []
            for i, amap in enumerate(use):
                ar = rows_under(base, amap)
                r = evaluate(make_recs(ar, ph, kind, seed=777 * i + 11, rho=rho), ph)  # vary the prediction seed per assignment
                g2.append(r["gain"]); p2.append(r["perm_p"])
            stab[name] = {"gain_median": float(np.median(g2)),
                          "detection_rate": float(np.mean([p < 0.05 for p in p2])), "assignments": len(use)}
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
        print(f"  {'predictor':<16} {'gain(med)':>10} {'chg%(med)':>10} {'perm_p(med)':>12} {'detect<.05':>11} {'95% CI':>14}")
        for name, d in r["predictors"].items():
            ci = d.get("detection_ci", [float('nan'), float('nan')])
            print(f"  {name:<16} {d['gain_median']:>9.1f} {d.get('answer_change_median', float('nan')):>9.1f} {d['perm_p_median']:>12.3f} {d['detection_rate']:>10.0%}"
                  f"   [{ci[0]:.0%}, {ci[1]:.0%}]")
        a = r["across_assignments"]
        print(f"  across re-drawn assignments ({a['n_distinct_assignments']} distinct valid, "
              f"{a['n_unique_incl_original']} unique incl. original, from {a['n_seeds_tried']} seeds):")
        if a.get("note"):
            print(f"    NOTE: {a['note']}")
        for name, d in a.items():
            if isinstance(d, dict):
                print(f"    {name:<14} gain(med)={d['gain_median']:.1f}  detect<.05={d['detection_rate']:.0%}  (n={d['assignments']})")


if __name__ == "__main__":
    main()
