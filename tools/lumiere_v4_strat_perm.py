"""Stratified, donor-grouped permutation for the E2 donor-key test (reviewer round 4, point 1).

The shipped donor permutation (``tools.lumiere_v4_supplement.donor_dependence``) treats the donor-key labels as
exchangeable among ALL recipients subject only to the no-own-key swap constraint. It therefore (i) does not preserve
the equal-image-count strata (a DSCR recipient shown three slices can only be paired with a three-slice donor, yet the
permutation moves two- and three-slice donor keys across that boundary), and (ii) does not keep a reused donor's keys
together (a donor used by two recipients donates the SAME key to both, but the permutation relabels each recipient
independently, so the twice-used multiplicity is not preserved). The real assignment respects both: donor pairs never
cross the scan-count stratum, and each donor serves at most two recipients.

This module runs the assignment-structure-preserving null the reviewer asks for. It is a conditional label-association
test (observed answers held fixed; no model is called), now with the correct exchangeability unit:

  * STRATA. Recipients are partitioned by scan count (DSCR: 2 vs 3 displayed slices; AIA, LIL: a single stratum of 1).
    Donor keys are permuted only WITHIN a stratum, so every permuted assignment is one the design could have produced.
  * BLOCKS. Recipients that share a donor form one block (size 1 or 2) carrying that donor's key. The permutation
    shuffles keys among BLOCKS, not among individual recipients, so a twice-used donor's key stays a single unit and the
    number of twice-used donors is identical in every draw. A block may not receive a key equal to any of its members'
    own keys (the swap construction forbids a recipient its own key).

Reported per cell: observed gain, the stratified-grouped permutation p, and, for comparison, the shipped unstratified p
(``donor_dependence``). For the two contested cells it also runs a Type-I calibration: draw a fresh constraint-valid
block-key assignment as a no-tracking truth, score the observed answers against it, and test with the same
stratified-grouped permutation; a valid test rejects at most at the nominal 5%.

  python -m tools.lumiere_v4_strat_perm                       # all open-model cells + Type-I on Scout/DSCR, MedGemma/AIA
  python -m tools.lumiere_v4_strat_perm --cells Llama-4-Scout:DSCR --nperm 20000 --sims 2000
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from src.lumiere_loader import _shuffle_options
from tools.lumiere_gating_stats import wilson
import tools.lumiere_v4_stats as st
# NOTE: tools.lumiere_v4_supplement is imported lazily inside main() only; supplement.donor_dependence imports the
# engine below, so a top-level import here would be circular.

IMG_PHASES = ("AIA", "LIL", "DSCR")
CONTESTED = [("Llama-4-Scout", "DSCR"), ("MedGemma-4B", "AIA")]


def _nimg(cid: str, ph: str) -> int:
    """Displayed scan count for a recipient's item = the equal-image-count stratum (DSCR is 2 or 3; AIA/LIL are 1)."""
    it = next(x for x in json.loads(Path(f"data/lumiere/v4/reviewed/{cid}.json").read_text())
              if x["id"].endswith("_" + ph))
    return len(it["image_files"])


def cell_arrays(recs: dict, ph: str):
    """Per-recipient option-mapped swap/text answer texts, assigned donor key, own key, donor id, and scan-count
    stratum, for every recipient that has all three conditions. Mirrors donor_dependence's inputs exactly."""
    cs = [c for c in sorted({k[0] for k in recs if k[1] == ph and k[2] == "swap"})
          if (c, ph, "text") in recs and (c, ph, "own") in recs]
    opts = {}
    for c in cs:
        it = next(x for x in json.loads(Path(f"data/lumiere/v4/reviewed/{c}.json").read_text())
                  if x["id"].endswith("_" + ph))
        opts[c] = it["options"] if it.get("ordered_options") else _shuffle_options(it["options"], it["correct_answer"], it["id"])[0]
    sw = [recs[(c, ph, "swap")] for c in cs]
    tx = [recs[(c, ph, "text")] for c in cs]
    dkey = [r["donor_key_text"] for r in sw]
    okey = [r["own_key_text"] for r in sw]
    donor = [r["donor"] for r in sw]
    sw_txt = [opts[c].get(r["model_answer"]) for c, r in zip(cs, sw)]
    tx_txt = [opts[c].get(r["model_answer"]) for c, r in zip(cs, tx)]
    stratum = [_nimg(c, ph) for c in cs]
    return cs, sw_txt, tx_txt, dkey, okey, donor, stratum


def build_blocks(dkey, okey, donor, stratum):
    """Group recipients sharing a donor into one block. Returns per-block: member recipient indices, the block's donor
    key, its stratum, and the set of keys forbidden to it (any member's own key). Validates that a donor's recipients
    share one key and one stratum (true by construction: pairs never cross scan count)."""
    order = {}
    for i, d in enumerate(donor):
        order.setdefault(d, []).append(i)
    blocks = []
    for d, idx in order.items():
        keys = {dkey[i] for i in idx}
        strata = {stratum[i] for i in idx}
        assert len(keys) == 1, f"donor {d} has inconsistent donor keys {keys}"
        assert len(strata) == 1, f"donor {d} spans strata {strata}"
        blocks.append({"members": idx, "key": dkey[idx[0]], "stratum": stratum[idx[0]],
                       "forbidden": frozenset(okey[i] for i in idx)})
    return blocks


def encode(sw_txt, tx_txt, blocks, n):
    """Encode over the donor-key class vocabulary so a key-assignment's gain is a vectorised lookup. Returns the
    one-hot swap/text match matrices (n x K), the per-block member-index arrays, each block's forbidden key codes,
    the block's own (observed) key code, and the block->stratum map."""
    classes = sorted({b["key"] for b in blocks} | {f for b in blocks for f in b["forbidden"]})
    idx = {t: k for k, t in enumerate(classes)}
    K = len(classes)
    Asw = np.zeros((n, K)); Btx = np.zeros((n, K))
    for i in range(n):
        if sw_txt[i] in idx:
            Asw[i, idx[sw_txt[i]]] = 1.0
        if tx_txt[i] in idx:
            Btx[i, idx[tx_txt[i]]] = 1.0
    benc = [{"members": np.array(b["members"]), "key": idx[b["key"]],
             "forbidden": np.array([idx[f] for f in b["forbidden"]]), "stratum": b["stratum"]} for b in blocks]
    return Asw, Btx, benc, K


def perm_p_from_arrays(sw_txt, tx_txt, dkey, okey, donor, stratum, rng, n_perm=5000):
    """Stratified, block-grouped permutation p from already-extracted per-recipient arrays. This is the single engine
    that ``lumiere_v4_supplement.donor_dependence`` reports, so the reported p, the synthetic-predictor validation and
    the robustness re-runs all use the same test. Returns (p, n_accepted)."""
    blocks = build_blocks(dkey, okey, donor, stratum)
    n = len(sw_txt)
    Asw, Btx, benc, _ = encode(sw_txt, tx_txt, blocks, n)
    p, accepted, _ = strat_perm_p(Asw, Btx, benc, n, n_perm, rng)
    return p, accepted


def _gain(Asw, Btx, codes):
    i = np.arange(len(codes))
    return float((Asw[i, codes] - Btx[i, codes]).mean())


def _expand(benc, block_codes, n):
    codes = np.empty(n, dtype=int)
    for b, c in zip(benc, block_codes):
        codes[b["members"]] = c
    return codes


def _assign_stratum(sblocks, skeys, rng, tries=400):
    """One valid key assignment for a stratum's blocks by sequential constrained draw, retried on dead ends. Each
    block, in random order, draws a remaining key not among its forbidden (own) keys, with probability proportional to
    the remaining count. Returns block codes in the stratum's block order, or None if no valid draw in ``tries``."""
    nb = len(sblocks)
    forb = [set(b["forbidden"].tolist()) for b in sblocks]
    base = Counter(skeys)
    for _ in range(tries):
        pool = dict(base)
        out = [None] * nb
        ok = True
        for bi in rng.permutation(nb):
            fb = forb[bi]
            tot = 0
            items = []
            for k, c in pool.items():
                if c > 0 and k not in fb:
                    items.append((k, c)); tot += c
            if tot == 0:
                ok = False
                break
            r = rng.random() * tot
            acc = 0
            for k, c in items:
                acc += c
                if r < acc:
                    out[bi] = k; pool[k] -= 1; break
        if ok:
            return out
    return None


def _draw_assignment(benc, by_stratum, rng):
    """A full constraint-valid block-key assignment across all strata (per-stratum rejection sampling). None if a
    stratum is infeasible."""
    block_codes = [None] * len(benc)
    for s, bis in by_stratum.items():
        sblocks = [benc[bi] for bi in bis]
        skeys = [benc[bi]["key"] for bi in bis]
        a = _assign_stratum(sblocks, skeys, rng)
        if a is None:
            return None
        for bi, k in zip(bis, a):
            block_codes[bi] = k
    return block_codes


def strat_perm_p(Asw, Btx, benc, n, n_perm, rng, obs=None):
    """Stratified, block-grouped permutation p: within each stratum permute the block keys among the stratum's blocks
    (never onto a block's own key), scoring the held answers against the reassigned block key."""
    by_stratum = {}
    for bi, b in enumerate(benc):
        by_stratum.setdefault(b["stratum"], []).append(bi)
    if obs is None:
        obs = _gain(Asw, Btx, _expand(benc, [b["key"] for b in benc], n))
    ge = 0; done = 0
    for _ in range(n_perm):
        bc = _draw_assignment(benc, by_stratum, rng)
        if bc is None:
            continue
        gp = _gain(Asw, Btx, _expand(benc, bc, n))
        done += 1
        ge += gp >= obs - 1e-12
    return (1 + ge) / (1 + done), done, obs


def type_I(Asw, Btx, benc, n, sims, n_perm, rng):
    """Draw a fresh constraint-valid block-key assignment as a no-tracking truth, score the held answers against it,
    and test with the stratified-grouped permutation. A valid test rejects at most at the nominal 5%."""
    by_stratum = {}
    for bi, b in enumerate(benc):
        by_stratum.setdefault(b["stratum"], []).append(bi)
    ps = []; attempts = 0
    while len(ps) < sims and attempts < sims * 50:
        attempts += 1
        bc = _draw_assignment(benc, by_stratum, rng)
        if bc is None:
            continue
        obs = _gain(Asw, Btx, _expand(benc, bc, n))
        tenc = [dict(b, key=c) for b, c in zip(benc, bc)]   # blocks carrying the drawn truth key
        p, _, _ = strat_perm_p(Asw, Btx, tenc, n, n_perm, rng, obs=obs)
        ps.append(p)
    ps = np.array(ps)
    k = int((ps < 0.05).sum()); lo, hi = wilson(k, len(ps))
    return {"sims": len(ps), "typeI_05": k / len(ps), "typeI_05_ci": [float(lo), float(hi)],
            "rej_10": float((ps < 0.10).mean()), "p_median": float(np.median(ps))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", nargs="+", default=None, help="model:phase tokens; default all open-model image cells")
    ap.add_argument("--nperm", type=int, default=20000)
    ap.add_argument("--sims", type=int, default=2000, help="null datasets for Type-I (contested cells only)")
    ap.add_argument("--nperm-typeI", type=int, default=2000)
    ap.add_argument("--out", default="results/lumiere_v4_strat_perm.json")
    args = ap.parse_args()
    rng = np.random.default_rng(st.SEED)

    if args.cells:
        cells = [tuple(c.split(":", 1)) for c in args.cells]
    else:
        cells = [(m, ph) for m in st.MODELS for ph in IMG_PHASES]

    rows = []
    for model, ph in cells:
        recs = st.load_records(model)
        cs, sw_txt, tx_txt, dkey, okey, donor, stratum = cell_arrays(recs, ph)
        if len(cs) < 5:
            continue
        blocks = build_blocks(dkey, okey, donor, stratum)
        n = len(cs)
        Asw, Btx, benc, K = encode(sw_txt, tx_txt, blocks, n)
        p_strat, accepted, obs = strat_perm_p(Asw, Btx, benc, n, args.nperm, np.random.default_rng(st.SEED))
        import tools.lumiere_v4_supplement as sup   # lazy: supplement imports this module's engine
        p_unstrat = sup._unstratified_perm_p(sw_txt, tx_txt, dkey, okey, np.random.default_rng(st.SEED), n_perm=args.nperm)
        row = {"model": model, "phase": ph, "n": n,
               "strata": dict(Counter(stratum)), "n_blocks": len(blocks),
               "donors_used_twice": sum(v > 1 for v in Counter(donor).values()),
               "gain_pp": obs * 100, "p_strat_grouped": p_strat, "accepted": accepted,
               "p_unstratified_shipped": p_unstrat}
        if (model, ph) in CONTESTED or args.cells:
            row["typeI"] = type_I(Asw, Btx, benc, n, args.sims, args.nperm_typeI, rng)
        rows.append(row)

    # Holm across all open-model image cells run in this pass (the paper's family is the 12 model-phase tests)
    ps = sorted([(r["p_strat_grouped"], i) for i, r in enumerate(rows)])
    m = len(ps)
    running = 0.0
    for rank, (p, i) in enumerate(ps):
        running = max(running, min(1.0, p * (m - rank)))
        rows[i]["p_strat_holm"] = running
    summary = {"n_cells": m, "n_below_05_raw": sum(r["p_strat_grouped"] < 0.05 for r in rows),
               "n_below_05_holm": sum(r.get("p_strat_holm", 1.0) < 0.05 for r in rows),
               "cells_below_05_raw": [f"{r['model']}/{r['phase']}={r['p_strat_grouped']:.3f}"
                                      for r in rows if r["p_strat_grouped"] < 0.05]}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"nominal_alpha": 0.05, "n_perm": args.nperm, "seed": st.SEED,
                                           "cells": rows, "family_summary": summary}, indent=1, default=float))

    print(f"\n{'cell':<24}{'n':>4}{'strata':>12}{'blk':>5}{'2x':>4}{'gain':>8}{'p_strat':>9}{'p_holm':>9}{'p_unstrat':>11}{'acc':>8}")
    for r in rows:
        print(f"  {r['model']+'/'+r['phase']:<22}{r['n']:>4}{str(r['strata']):>12}{r['n_blocks']:>5}"
              f"{r['donors_used_twice']:>4}{r['gain_pp']:>7.1f}%{r['p_strat_grouped']:>9.3f}{r.get('p_strat_holm', float('nan')):>9.3f}"
              f"{(r['p_unstratified_shipped'] if r['p_unstratified_shipped'] is not None else float('nan')):>11.3f}{r['accepted']:>8}")
        if "typeI" in r:
            t = r["typeI"]
            print(f"  {'':<22} Type-I@5%: {t['typeI_05']:.1%} [{t['typeI_05_ci'][0]:.1%}, {t['typeI_05_ci'][1]:.1%}] "
                  f"over {t['sims']} nulls; median null p={t['p_median']:.2f}")
    print(f"\nfamily: {summary['n_below_05_raw']} of {summary['n_cells']} cells raw p<.05 "
          f"({summary['cells_below_05_raw']}); {summary['n_below_05_holm']} survive Holm.")


if __name__ == "__main__":
    main()
