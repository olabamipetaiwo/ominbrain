"""
Sampling-distribution validation for the donor-key permutation test (reviewer round 3, bullet 4).

The donor-key permutation (``tools.lumiere_v4_supplement.donor_dependence``) draws a uniform
permutation of the donor keys among recipients and, when a permuted key collides with a
recipient's OWN key (an assignment the swap construction forbids), REPAIRS the draw by random
swaps, discarding it if 20 repair rounds fail. A reviewer notes that the repair step's effect on
the test's null sampling distribution is not demonstrated. This script demonstrates it, with NO
model called (pure re-analysis of already-collected answers):

WHY THE REPAIR EXISTS. With the imaging phases' class multiplicities, a uniformly drawn whole
permutation almost never avoids every own-key collision, so rejecting colliding draws outright is
computationally infeasible (STEP 0 measures the vanishing acceptance rate). The implementation
therefore repairs collisions instead of rejecting them, and the repair must itself be validated.

STEP 1 -- Type-I calibration of the repair sampler under a no-tracking null (the core demonstration).
  We build many datasets in which the swap answer is independent of which donor was shown (the
  observed swap-answer texts are permuted among recipients, destroying any donor-specific
  association while preserving the real answer marginals; the imaging phases use a shared option
  vocabulary, so a permuted text is still a legal class label). On each null dataset we run the
  repair-based permutation test and record whether p<.05. A valid test rejects at most at the
  nominal 5% rate and its p-values are approximately uniform. Reported with a Wilson interval.

STEP 2 -- The repair does not drive the real result.
  An independent, repair-free sampler draws valid permutations by SEQUENTIAL CONSTRAINED assignment
  (each recipient draws a remaining donor key of a class other than its own; never collides, never
  repairs). On the real answers for the contested cells we compute the permutation p three ways
  (the paper's repair sampler re-implemented here, the shipped ``donor_dependence`` as a fidelity
  check, and the repair-free sequential sampler) and show they agree.

  python -m tools.lumiere_v4_perm_validation                 # Scout/DSCR and MedGemma/AIA
  python -m tools.lumiere_v4_perm_validation --cells Llama-4-Scout:DSCR --sims 2000 --nperm 2000
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.lumiere_loader import _shuffle_options
from tools.lumiere_gating_stats import wilson
import tools.lumiere_v4_stats as st
import tools.lumiere_v4_supplement as sup

DEFAULT_CELLS = [("Llama-4-Scout", "DSCR"), ("MedGemma-4B", "AIA")]


def gain_arrays(recs: dict, ph: str):
    """Replicate donor_dependence's per-recipient gain inputs: the option-mapped swap/text answer
    texts, the assigned donor key, and the own key, for every recipient with all three conditions."""
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
    sw_txt = [opts[c].get(r["model_answer"]) for c, r in zip(cs, sw)]
    tx_txt = [opts[c].get(r["model_answer"]) for c, r in zip(cs, tx)]
    return cs, sw_txt, tx_txt, dkey, okey


def _encode(sw_txt, tx_txt, dkey, okey):
    """Encode everything over the donor-key class vocabulary so a permutation's gain is a lookup."""
    classes = sorted({*dkey, *okey})
    idx = {t: k for k, t in enumerate(classes)}
    n, K = len(dkey), len(classes)
    Asw = np.zeros((n, K)); Btx = np.zeros((n, K))
    for i in range(n):
        if sw_txt[i] in idx:
            Asw[i, idx[sw_txt[i]]] = 1.0
        if tx_txt[i] in idx:
            Btx[i, idx[tx_txt[i]]] = 1.0
    dcode = np.array([idx[t] for t in dkey])
    ocode = np.array([idx[t] for t in okey])
    return Asw, Btx, dcode, ocode


def obs_gain(Asw, Btx, dcode):
    i = np.arange(len(dcode))
    return float((Asw[i, dcode] - Btx[i, dcode]).mean())


def whole_perm_accept_rate(dcode, ocode, rng, draws=200_000):
    """STEP 0: share of uniform whole permutations with NO own-key collision (why pure rejection fails)."""
    n = len(dcode)
    perm = np.argsort(rng.random((draws, n)), axis=1)
    keep = ~(dcode[perm] == ocode[None, :]).any(axis=1)
    return float(keep.mean())


def repair_null_gains(Asw, Btx, dcode, ocode, n_perm, rng):
    """Gains from donor_dependence's repair sampler (its lines 292-305): draw a uniform permutation,
    repair own-key collisions by random swaps (<=20 rounds), discard if unrepaired."""
    n = len(dcode); ir = np.arange(n)
    dcl = list(dcode); ocl = list(ocode)
    gains = []
    for _ in range(n_perm):
        perm = list(rng.permutation(n))
        for _fix in range(20):
            bad = [i for i in range(n) if dcl[perm[i]] == ocl[i]]
            if not bad:
                break
            for i in bad:
                j = int(rng.integers(0, n))
                perm[i], perm[j] = perm[j], perm[i]
        else:
            continue
        a = dcode[perm]
        gains.append(float((Asw[ir, a] - Btx[ir, a]).mean()))
    return np.array(gains)


def sample_valid_seq(dcode, ocode, rng):
    """One valid donor-key arrangement by sequential constrained assignment: each recipient, in
    random order, draws a remaining key of a class other than its own, with probability proportional
    to the remaining count. Never collides, never repairs. Returns the assigned class codes, or None
    on the rare dead end. Independent of the repair sampler by construction."""
    n = len(dcode); K = int(dcode.max()) + 1
    counts = np.bincount(dcode, minlength=K).astype(int)
    a = np.empty(n, dtype=int)
    for i in rng.permutation(n):
        avail = counts.copy(); avail[ocode[i]] = 0
        tot = int(avail.sum())
        if tot == 0:
            return None
        r = int(rng.integers(0, tot)); c = 0
        while r >= avail[c]:
            r -= int(avail[c]); c += 1
        a[i] = c; counts[c] -= 1
    return a


def seq_null_gains(Asw, Btx, dcode, ocode, n_draw, rng):
    n = len(dcode); ir = np.arange(n)
    gains = []
    while len(gains) < n_draw:
        a = sample_valid_seq(dcode, ocode, rng)
        if a is None:
            continue
        gains.append(float((Asw[ir, a] - Btx[ir, a]).mean()))
    return np.array(gains)


def _p_from(gains, obs):
    return (1 + int((gains >= obs - 1e-12).sum())) / (1 + len(gains))


def step_real(cells, n_perm_real, rng):
    """Step 0 (why repair) + Step 2 (repair vs shipped vs repair-free on the real answers) +
    Step 3 (do the repair and the repair-free sampler induce the same null gain distribution?)."""
    from scipy.stats import ks_2samp
    rows = []
    for model, ph in cells:
        recs = st.load_records(model)
        cs, sw_txt, tx_txt, dkey, okey = gain_arrays(recs, ph)
        Asw, Btx, dcode, ocode = _encode(sw_txt, tx_txt, dkey, okey)
        obs = obs_gain(Asw, Btx, dcode)
        acc_rate = whole_perm_accept_rate(dcode, ocode, np.random.default_rng(st.SEED))
        g_rep = repair_null_gains(Asw, Btx, dcode, ocode, n_perm_real, np.random.default_rng(st.SEED))
        g_seq = seq_null_gains(Asw, Btx, dcode, ocode, n_perm_real, np.random.default_rng(st.SEED))
        p_sup = sup.donor_dependence(recs, np.random.default_rng(st.SEED), n_perm=n_perm_real).get(ph, {}).get("perm_p")
        qs = [50, 90, 95, 99]
        rows.append({"model": model, "phase": ph, "n": len(cs), "gain_pp": obs * 100,
                     "whole_perm_accept_rate": acc_rate,
                     "p_repair": _p_from(g_rep, obs), "p_shipped": p_sup, "p_sequential": _p_from(g_seq, obs),
                     "repair_accepted": len(g_rep), "null_mean_repair": float(g_rep.mean() * 100),
                     "null_mean_seq": float(g_seq.mean() * 100),
                     "null_sd_repair": float(g_rep.std() * 100), "null_sd_seq": float(g_seq.std() * 100),
                     "null_q_repair": [float(np.percentile(g_rep, q) * 100) for q in qs],
                     "null_q_seq": [float(np.percentile(g_seq, q) * 100) for q in qs],
                     "ks_stat": float(ks_2samp(g_rep, g_seq).statistic),
                     "ks_p": float(ks_2samp(g_rep, g_seq).pvalue)})
    return rows


def step_typeI(cells, sims, n_perm, rng):
    """Type-I of the repair sampler under a PROPER no-tracking null: hold the real (swap, text)
    answers, draw a fresh VALID donor assignment with the repair-free sequential sampler (so the
    donor key is exchangeable by construction, subject to the same own-key constraint the test
    respects), then test with the repair sampler. A valid test rejects at <=5%."""
    rows = []
    for model, ph in cells:
        recs = st.load_records(model)
        cs, sw_txt, tx_txt, dkey, okey = gain_arrays(recs, ph)
        Asw, Btx, dcode, ocode = _encode(sw_txt, tx_txt, dkey, okey)
        ps = []; attempts = 0
        while len(ps) < sims and attempts < sims * 500:
            attempts += 1
            a = sample_valid_seq(dcode, ocode, rng)      # fresh valid donor-key vector (same multiset)
            if a is None:
                continue                                  # dead end: retry, do not consume a sim slot
            obs = obs_gain(Asw, Btx, a)
            g = repair_null_gains(Asw, Btx, a, ocode, n_perm, rng)
            ps.append(_p_from(g, obs))
        ps = np.array(ps); k = int((ps < 0.05).sum()); lo, hi = wilson(k, len(ps))
        rows.append({"model": model, "phase": ph, "n": len(cs), "sims": len(ps),
                     "typeI_05": k / len(ps), "typeI_05_ci": [float(lo), float(hi)],
                     "rej_10": float((ps < 0.10).mean()), "rej_25": float((ps < 0.25).mean()),
                     "p_median": float(np.median(ps)), "p_mean": float(ps.mean())})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", nargs="+", default=None, help="model:phase tokens; default Scout/DSCR + MedGemma/AIA")
    ap.add_argument("--sims", type=int, default=2000, help="null datasets for Type-I calibration")
    ap.add_argument("--nperm", type=int, default=2000, help="permutations per calibration test")
    ap.add_argument("--nperm-real", type=int, default=20000, help="null draws per sampler on the real data")
    ap.add_argument("--out", default="results/lumiere_v4_perm_validation.json")
    args = ap.parse_args()
    cells = ([tuple(c.split(":", 1)) for c in args.cells] if args.cells else DEFAULT_CELLS)
    rng = np.random.default_rng(st.SEED)

    s2 = step_real(cells, args.nperm_real, rng)
    s1 = step_typeI(cells, args.sims, args.nperm, rng)
    res = {"nominal_alpha": 0.05, "step0_2_3_real": s2, "step1_null_calibration": s1}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, default=float))

    print("\n=== STEP 0+2+3: real data -- why repair; does repair change the answer; same null dist? ===")
    print(f"  {'cell':<22}{'n':>4}{'gain':>7}{'whole-perm ok':>14}{'p_repair':>10}{'p_shipped':>11}{'p_seq':>8}{'KS':>7}")
    for r in s2:
        print(f"  {r['model']+'/'+r['phase']:<22}{r['n']:>4}{r['gain_pp']:>6.1f}%{r['whole_perm_accept_rate']*100:>13.3f}%"
              f"{r['p_repair']:>10.3f}{(r['p_shipped'] or float('nan')):>11.3f}{r['p_sequential']:>8.3f}{r['ks_stat']:>7.3f}")
        print(f"  {'':<22} null gain repair vs seq: mean {r['null_mean_repair']:.1f} vs {r['null_mean_seq']:.1f} pp, "
              f"sd {r['null_sd_repair']:.1f} vs {r['null_sd_seq']:.1f}, q95 {r['null_q_repair'][2]:.1f} vs {r['null_q_seq'][2]:.1f}, "
              f"KS p={r['ks_p']:.2f}")
    print("\n=== STEP 1: Type-I of the repair sampler under a proper no-tracking null (nominal 5%) ===")
    for r in s1:
        print(f"  {r['model']+'/'+r['phase']:<22} {r['typeI_05']:.1%} "
              f"[{r['typeI_05_ci'][0]:.1%}, {r['typeI_05_ci'][1]:.1%}] over {r['sims']} nulls; "
              f"median p={r['p_median']:.2f}, P(p<.10)={r['rej_10']:.1%}, P(p<.25)={r['rej_25']:.1%}")


if __name__ == "__main__":
    main()
