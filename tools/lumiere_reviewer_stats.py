"""
Statistical corrections for the LUMIERE grounding checks (senior-reviewer round 2, 2026-09-23).

Recomputes, from the existing v3 runs only (no model calls, no GPU):

  1. accuracy   Image vs text-only accuracy per model, on the item-level `correct` flag
                (salvaged answers count, as the paper's failed-response policy states), with
                the phase_score-based figure alongside to expose the parse-error discrepancy.
                Paired, patient-clustered bootstrap CIs (image - text-only) overall and PER PHASE,
                plus discordant-pair counts.
  2. cf         Counterfactual-image substitution: flip rate per phase with patient-clustered CIs
                and, among flipped LIL/DSCR items, the truth-tracking rate against an ITEM-SPECIFIC
                null (a flipped answer is drawn uniformly from that item's other checkable options),
                with patient- and donor-clustered bootstrap CIs. Also: how often the donor's own
                correct option is even among the options shown (answer-key compatibility), and how
                often flips move TOWARD the original patient's truth instead.
  3. baselines  Option-only guessers on the v3 items the models saw: longest option, most common
                answer letter, stem-overlap.

Read-only on results/ and data/; CPU-only, safe on a login node.

Usage
-----
python -m tools.lumiere_reviewer_stats                 # prints everything, writes results/lumiere_reviewer_stats.{json,md}
"""

import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import config
from src.lumiere_labels import canonical_answer_text
from src.lumiere_loader import load_lumiere
from tools.compile_lumiere_counterfactual import PAIRS_PATH, _direction_word, _rano_word, truth_label

MODELS = ["MedGemma-4B", "Gemma-3-12B", "Gemma-3-27B", "Llama-4-Scout"]
PHASES = list(config.PHASES)
N_BOOT = 10_000
SEED = 20260923


def latest(pattern: str) -> Path:
    runs = sorted(glob.glob(pattern))
    if not runs:
        raise FileNotFoundError(pattern)
    return Path(runs[-1])


def load_run(kind: str, model: str) -> list[dict]:
    pat = {"img": f"results/lumiere_{model}_v3_nogate_*",
           "txt": f"results/lumiere_{model}_textonly_v3_nogate_*",
           "cf": f"results/lumiere_{model}_cf_v3_nogate_*"}[kind]
    return json.loads((latest(pat) / "raw_results.json").read_text())


def item_table(cases: list[dict]) -> dict[tuple[str, str], dict]:
    return {(c["case_id"], ph): q for c in cases for ph, p in c["phases"].items() for q in p["questions"]}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def pct(x: float) -> str:
    return "n/a" if x is None or np.isnan(x) else f"{100 * x:.1f}"


# ---------------------------------------------------------------- 1. accuracy
def accuracy_section(rng) -> tuple[dict, list[str]]:
    out, lines = {}, []
    lines += ["## 1. Image vs text-only accuracy (v3, non-gated)", "",
              "Δ = image − text-only, percentage points. CI = patient-clustered paired bootstrap "
              f"({N_BOOT:,} resamples of the 52 patients). 'phase-score basis' is the number the old table used: "
              "`evaluator.py` drops parse-error items from a phase's denominator, so a salvaged-correct answer "
              "scores 0 there but `correct=True` at item level.", "",
              "| Model | Image (item basis) | Text-only (item basis) | Δ item basis [95% CI] | Image (phase-score basis) | "
              "Text-only (phase-score basis) | Δ phase-score basis | parse errors img/txt (salvaged-correct img/txt) |",
              "|---|---|---|---|---|---|---|---|"]
    per_phase_lines = ["", "### Per-phase paired difference (image − text-only, pp) [patient-clustered 95% CI]  "
                       "(b = right only with image, c = right only text-only)", "",
                       "| Model | " + " | ".join(PHASES) + " |", "|---|" + "---|" * len(PHASES)]
    for m in MODELS:
        img, txt = load_run("img", m), load_run("txt", m)
        ti, tt = item_table(img), item_table(txt)
        patients = sorted({c for c, _ in ti})
        keys = [(c, ph) for c in patients for ph in PHASES if (c, ph) in ti and (c, ph) in tt]
        # per-patient x per-phase correct arrays (n_patients, 5); NaN = missing
        A = np.full((len(patients), len(PHASES)), np.nan)
        B = np.full_like(A, np.nan)
        pidx = {p: i for i, p in enumerate(patients)}
        for c, ph in keys:
            A[pidx[c], PHASES.index(ph)] = bool(ti[(c, ph)]["correct"])
            B[pidx[c], PHASES.index(ph)] = bool(tt[(c, ph)]["correct"])

        def diff(idx):
            a, b = A[idx], B[idx]
            return np.nanmean(a) - np.nanmean(b)

        d_all = diff(np.arange(len(patients)))
        boots = np.array([diff(rng.integers(0, len(patients), len(patients))) for _ in range(N_BOOT)])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        ph_cells, ph_json = [], {}
        for j, ph in enumerate(PHASES):
            a, b = A[:, j], B[:, j]
            ok = ~np.isnan(a) & ~np.isnan(b)
            d = np.mean(a[ok]) - np.mean(b[ok])
            bs = []
            for _ in range(N_BOOT):
                ix = rng.integers(0, len(patients), len(patients))
                k = ok[ix]
                bs.append(np.mean(a[ix][k]) - np.mean(b[ix][k]))
            plo, phi = np.percentile(bs, [2.5, 97.5])
            bcount = int(np.sum((a[ok] == 1) & (b[ok] == 0)))
            ccount = int(np.sum((a[ok] == 0) & (b[ok] == 1)))
            ph_cells.append(f"{100 * d:+.1f} [{100 * plo:+.1f}, {100 * phi:+.1f}] (b={bcount}, c={ccount})")
            ph_json[ph] = {"diff": d, "ci": [plo, phi], "b_right_only_img": bcount, "c_right_only_txt": ccount,
                           "n": int(ok.sum())}
        per_phase_lines.append(f"| {m} | " + " | ".join(ph_cells) + " |")

        n_img, n_txt = len(ti), len(tt)
        acc_i = sum(bool(q["correct"]) for q in ti.values()) / n_img
        acc_t = sum(bool(q["correct"]) for q in tt.values()) / n_txt
        ps_i = float(np.mean([c["overall_score"] for c in img]))
        ps_t = float(np.mean([c["overall_score"] for c in txt]))
        pe_i = sum(bool(q.get("parse_error")) for q in ti.values())
        pe_t = sum(bool(q.get("parse_error")) for q in tt.values())
        sv_i = sum(bool(q.get("parse_error")) and bool(q["correct"]) for q in ti.values())
        sv_t = sum(bool(q.get("parse_error")) and bool(q["correct"]) for q in tt.values())
        lines.append(f"| {m} | {pct(acc_i)} | {pct(acc_t)} | {100 * d_all:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] | "
                     f"{pct(ps_i)} | {pct(ps_t)} | {100 * (ps_i - ps_t):+.1f} | {pe_i}/{pe_t} ({sv_i}/{sv_t}) |")
        out[m] = {"acc_img": acc_i, "acc_txt": acc_t, "diff": d_all, "ci": [lo, hi],
                  "phase_score_img": ps_i, "phase_score_txt": ps_t, "parse_err": [pe_i, pe_t],
                  "salvaged_correct": [sv_i, sv_t], "per_phase": ph_json}
    return out, lines + per_phase_lines


# ---------------------------------------------------------------- 2. counterfactual
def option_tables(item_set: str = "v3") -> dict[str, dict]:
    """item id -> {'options': {letter: text}, 'correct_text': str}, as the models saw them (shuffled)."""
    t = {}
    for c in load_lumiere(include_unreviewed=True, item_set=item_set):
        for qs in c["phases"].values():
            for q in qs:
                t[q["id"]] = {"options": q["options"], "correct_text": q["correct_answer_text"],
                              "correct": q["correct_answer"]}
    return t


def _label(phase: str, text: str) -> str | None:
    return _direction_word(text) if phase == "LIL" else _rano_word(text)


def donor_permutation_test(ev: list[dict], pairs: dict, n_perm: int = 20_000) -> dict:
    """Permutation null over DONOR ASSIGNMENT, at patient level.

    H0: a flipped answer is unrelated to which donor's image was shown. Each replicate redraws every patient's
    donor uniformly from the patients on the opposite LIL-direction side (exactly the pairing rule in
    tools/build_lumiere_counterfactual_pairs.py, reuse allowed), keeps every observed flipped answer fixed, and
    recounts truth-tracking against the new donor's truth label. One donor per patient is shared by all models
    and both phases, so shared-patient dependence and donor reuse are preserved rather than ignored."""
    prng = np.random.default_rng(SEED + 1)
    patients = sorted(pairs)
    pidx = {p: i for i, p in enumerate(patients)}
    side = {p: pairs[p]["own_direction"] for p in patients}
    eligible = [np.array([pidx[q] for q in patients if side[q] != side[p]]) for p in patients]
    ev_pat = np.array([pidx[e["patient"]] for e in ev])
    # M[e, d] = would event e count as truth-tracking if donor d had been shown
    M = np.zeros((len(ev), len(patients)), dtype=bool)
    for i, e in enumerate(ev):
        for j, d in enumerate(patients):
            M[i, j] = e["new_lab"] == truth_label(d, e["phase"])
    draws = np.stack([prng.integers(0, len(eligible[i]), n_perm) for i in range(len(patients))], axis=1)
    donor_idx = np.stack([eligible[i][draws[:, i]] for i in range(len(patients))], axis=1)   # (n_perm, n_patients)
    hits = M[np.arange(len(ev))[None, :], donor_idx[:, ev_pat]]                             # (n_perm, n_events)
    obs = np.array([e["tracks"] for e in ev], dtype=bool)
    counts = hits.sum(axis=1)
    out = {"n_perm": n_perm, "observed": int(obs.sum()), "n": len(ev), "perm_mean": float(counts.mean()),
           "perm_lo": float(np.percentile(counts, 2.5)), "perm_hi": float(np.percentile(counts, 97.5)),
           "p_ge": float((counts >= obs.sum()).mean()), "by_phase": {}}
    for ph in ("LIL", "DSCR"):
        sel = np.array([e["phase"] == ph for e in ev])
        c = hits[:, sel].sum(axis=1)
        out["by_phase"][ph] = {"observed": int(obs[sel].sum()), "n": int(sel.sum()), "perm_mean": float(c.mean()),
                               "p_ge": float((c >= obs[sel].sum()).mean())}
    return out


def counterfactual_section(rng) -> tuple[dict, list[str]]:
    pairs = json.load(open(PAIRS_PATH))
    opts = option_tables()
    # extractor self-check: every option must be labelled, and the correct option's label must equal truth_label
    for iid, o in opts.items():
        ph = iid.rsplit("_", 1)[1]
        if ph in ("LIL", "DSCR"):
            assert all(_label(ph, t) for t in o["options"].values()), f"unlabelled option in {iid}"
    lines = ["## 2. Counterfactual-image substitution", ""]
    out = {"per_model_phase": {}, "pooled": {}}

    # ---- flip rates with patient-clustered CI
    lines += ["### Flip rate (own image → donor image), patient-clustered 95% CI", "",
              "| Model | " + " | ".join(PHASES) + " |", "|---|" + "---|" * len(PHASES)]
    events = []   # one record per flipped, checkable LIL/DSCR item
    for m in MODELS:
        own, cf = item_table(load_run("img", m)), item_table(load_run("cf", m))
        patients = sorted({c for c, _ in cf})
        cells = []
        for ph in PHASES:
            flips = {}
            for c in patients:
                a, b = own.get((c, ph)), cf.get((c, ph))
                if a is None or b is None or a.get("model_answer") is None or b.get("model_answer") is None:
                    continue
                flips[c] = a["model_answer_text"] != b["model_answer_text"]
            arr = np.array([flips[c] for c in flips], dtype=float)
            f = arr.mean()
            bs = [arr[rng.integers(0, len(arr), len(arr))].mean() for _ in range(N_BOOT)]
            lo, hi = np.percentile(bs, [2.5, 97.5])
            cells.append(f"{100 * f:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}] (n={len(arr)})")
            out["per_model_phase"][f"{m}/{ph}"] = {"flip": float(f), "ci": [float(lo), float(hi)], "n": len(arr)}
        lines.append(f"| {m} | " + " | ".join(cells) + " |")

        # collect item-specific events
        for c in patients:
            pr = pairs[c]
            for ph in ("LIL", "DSCR"):
                a, b = own.get((c, ph)), cf.get((c, ph))
                if a is None or b is None or a.get("model_answer") is None or b.get("model_answer") is None:
                    continue
                if a["model_answer_text"] == b["model_answer_text"]:
                    continue
                partner_truth = truth_label(pr["partner"], ph)
                own_truth = truth_label(c, ph)
                new_lab = _label(ph, b["model_answer_text"])
                if not partner_truth or not new_lab:
                    continue   # same checkability filter as tools/compile_lumiere_counterfactual
                others = [t for t in opts[b["id"]]["options"].values() if t != a["model_answer_text"]]
                labs = [_label(ph, t) for t in others]
                labs = [x for x in labs if x]
                p_null = (sum(x == partner_truth for x in labs) / len(labs)) if labs else np.nan
                events.append({"model": m, "phase": ph, "patient": c, "donor": pr["partner"], "new_lab": new_lab,
                               "tracks": int(new_lab == partner_truth),
                               "toward_own": int(new_lab == own_truth), "p_null": p_null,
                               "same_label_as_before": int(new_lab == _label(ph, a["model_answer_text"]))})

    ev = [e for e in events if not np.isnan(e["p_null"])]
    k = sum(e["tracks"] for e in ev)
    n = len(ev)
    p_null = np.array([e["p_null"] for e in ev])
    exp = float(p_null.sum())
    sims = rng.random((20000, n)) < p_null
    sim_counts = sims.sum(axis=1)
    p_below = float((sim_counts <= k).mean())
    p_above = float((sim_counts >= k).mean())
    w_lo, w_hi = wilson(k, n)

    def cluster_boot(key):
        groups = defaultdict(list)
        for e in ev:
            groups[e[key]].append(e)
        names = list(groups)
        rates, excess = [], []
        for _ in range(N_BOOT):
            samp = [e for g in rng.integers(0, len(names), len(names)) for e in groups[names[g]]]
            if not samp:
                continue
            rates.append(np.mean([e["tracks"] for e in samp]))
            excess.append(np.mean([e["tracks"] - e["p_null"] for e in samp]))
        return np.percentile(rates, [2.5, 97.5]), np.percentile(excess, [2.5, 97.5])

    (pl, ph_), (el, eh) = cluster_boot("patient")
    (dl, dh), (del_, deh) = cluster_boot("donor")
    obs_excess = float(np.mean([e["tracks"] - e["p_null"] for e in ev]))
    toward_own = float(np.mean([e["toward_own"] for e in ev]))
    toward_own_ph = {ph: float(np.mean([e["toward_own"] for e in ev if e["phase"] == ph])) for ph in ("LIL", "DSCR")}
    same_lab = float(np.mean([e["same_label_as_before"] for e in ev]))

    perm = donor_permutation_test(ev, pairs)

    lines += ["", "### Truth-tracking among flipped, checkable LIL/DSCR items (pooled over models)", "",
              f"- Observed: {k}/{n} = {100 * k / n:.1f}%. Naive Wilson (treats items as independent): "
              f"[{100 * w_lo:.1f}, {100 * w_hi:.1f}].",
              f"- Item-specific null (flipped answer drawn uniformly among that item's OTHER checkable options): "
              f"expected {exp:.1f}/{n} = {100 * exp / n:.1f}%. P(count ≤ observed | null) = {p_below:.3f}; "
              f"P(count ≥ observed | null) = {p_above:.3f}.",
              f"- Excess over item-specific null: {100 * obs_excess:+.1f} pp. Patient-clustered 95% CI of the excess "
              f"[{100 * el:+.1f}, {100 * eh:+.1f}]; donor-clustered [{100 * del_:+.1f}, {100 * deh:+.1f}].",
              f"- Observed rate, patient-clustered CI [{100 * pl:.1f}, {100 * ph_:.1f}]; donor-clustered "
              f"[{100 * dl:.1f}, {100 * dh:.1f}].",
              f"- Flips that land on the ORIGINAL patient's own truth label: LIL {100 * toward_own_ph['LIL']:.1f}%, "
              f"DSCR {100 * toward_own_ph['DSCR']:.1f}% (DSCR own and donor RANO labels coincide for some pairs, e.g. PD→PD, "
              f"so 'donor truth' and 'own truth' are not exclusive there).",
              f"- Flips that keep the same direction/RANO label (only wording, magnitude, or location changed): "
              f"{100 * same_lab:.1f}% — these are flips but cannot be truth-tracking by construction.",
              f"- **Donor-permutation test** (patient-level; {perm['n_perm']:,} replicates): each patient's donor is redrawn "
              f"uniformly from the patients on the opposite LIL-direction side (the pairing design; reuse allowed), the model's "
              f"observed flipped answers are held fixed, and truth-tracking is recounted. Observed {perm['observed']}/{n}; "
              f"permutation mean {perm['perm_mean']:.1f} (95% range {perm['perm_lo']:.0f}–{perm['perm_hi']:.0f}); "
              f"one-sided P(count ≥ observed) = {perm['p_ge']:.3f}. LIL: {perm['by_phase']['LIL']['observed']}/"
              f"{perm['by_phase']['LIL']['n']} vs mean {perm['by_phase']['LIL']['perm_mean']:.1f} "
              f"(p = {perm['by_phase']['LIL']['p_ge']:.3f}); DSCR: {perm['by_phase']['DSCR']['observed']}/"
              f"{perm['by_phase']['DSCR']['n']} vs mean {perm['by_phase']['DSCR']['perm_mean']:.1f} "
              f"(p = {perm['by_phase']['DSCR']['p_ge']:.3f}). Unlike the item-specific null, this respects the shared-patient "
              f"and donor-reuse structure (one donor per patient across all models and phases). CAVEAT: the pairing rule fixes every "
              f"donor's LIL direction to the opposite of the patient's, so for LIL every eligible donor has the same label and the "
              f"permutation cannot separate donors (its p is ~0.5 by construction); only the DSCR row, where donor RANO labels "
              f"differ, is informative about donor-specificity.",
              "", "Per model × phase (k/n observed vs expected under the item-specific null):", "",
              "| Model | Phase | observed | expected | n |", "|---|---|---|---|---|"]
    for m in MODELS:
        for ph in ("LIL", "DSCR"):
            sub = [e for e in ev if e["model"] == m and e["phase"] == ph]
            if sub:
                lines.append(f"| {m} | {ph} | {sum(e['tracks'] for e in sub)} | "
                             f"{sum(e['p_null'] for e in sub):.1f} | {len(sub)} |")

    # ---- answer-key compatibility: does the donor's own correct option appear among the options shown?
    comp = []
    for m in MODELS[:1]:                       # options/pairs are model-independent
        for c, pr in pairs.items():
            for ph in ("LIL", "DSCR"):
                own_id, donor_id = f"{c}_{ph}", f"{pr['partner']}_{ph}"
                if own_id in opts and donor_id in opts:
                    shown = set(opts[own_id]["options"].values())
                    comp.append((ph, canonical_answer_text(opts[donor_id]["correct_text"]) in {canonical_answer_text(s) for s in shown}))
    for ph in ("LIL", "DSCR"):
        vals = [v for p, v in comp if p == ph]
        lines.append("")
        lines.append(f"- Answer-key compatibility, {ph}: the donor's own correct option text is among the options shown "
                     f"for {sum(vals)}/{len(vals)} patients (donor-truth label present in options: see below)."
                     if ph == "LIL" else
                     f"- Answer-key compatibility, {ph}: the donor's own correct option text is among the options shown "
                     f"for {sum(vals)}/{len(vals)} patients.")
    lab_avail = []
    for c, pr in pairs.items():
        own_id = f"{c}_DSCR"
        if own_id in opts:
            labs = {_rano_word(t) for t in opts[own_id]["options"].values()}
            lab_avail.append(truth_label(pr["partner"], "DSCR") in labs)
    lil_lab = []
    for c, pr in pairs.items():
        own_id = f"{c}_LIL"
        if own_id in opts:
            labs = {_direction_word(t) for t in opts[own_id]["options"].values()}
            lil_lab.append(truth_label(pr["partner"], "LIL") in labs)
    lines.append(f"- Donor's truth LABEL is present among the options shown: LIL direction {sum(lil_lab)}/{len(lil_lab)}, "
                 f"DSCR RANO label {sum(lab_avail)}/{len(lab_avail)}. Label-level matching is what the truth-tracking "
                 f"test uses; a fully correct option (location + magnitude + direction) essentially never exists for LIL.")
    small = 0
    for c, pr in pairs.items():
        small += "stable" in (truth_label(c, "LIL"), truth_label(pr["partner"], "LIL"))
    lines.append(f"- Pairs where the patient's or donor's own LIL truth is worded 'stable' (|volume change| small, so the "
                 f"'opposite direction' guarantee is a sign flip on a near-zero change, not a substantive difference): "
                 f"{small}/{len(pairs)}.")

    out["pooled"] = {"k": k, "n": n, "expected_null": exp, "p_below": p_below, "p_above": p_above,
                     "naive_wilson": [w_lo, w_hi], "excess": obs_excess,
                     "excess_ci_patient": [float(el), float(eh)], "excess_ci_donor": [float(del_), float(deh)],
                     "rate_ci_patient": [float(pl), float(ph_)], "rate_ci_donor": [float(dl), float(dh)],
                     "toward_own_truth": toward_own, "toward_own_truth_by_phase": toward_own_ph, "same_label_flip": same_lab,
                     "donor_permutation": perm}
    return out, lines


# ---------------------------------------------------------------- 3. baselines
STOP = set("the a an of and or to in with by for at on is was were be as that this which from into between".split())


def _toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP}


def baseline_section() -> tuple[dict, list[str]]:
    cases = load_lumiere(include_unreviewed=True, item_set="v3")
    by_phase = defaultdict(list)
    for c in cases:
        for ph, qs in c["phases"].items():
            for q in qs:
                by_phase[ph].append(q)
    lines = ["## 3. Option-only baselines on the v3 items exactly as shown (shuffled options)", "",
             "Longest option = pick the longest option text. Letter-prior = always the most common correct letter "
             "(fitted on the same items, so optimistic). Stem-overlap = option sharing most words with the stem "
             "(ties → first). Chance = 1/#options. Wilson 95% CI. 'Options-only' and 'no-chain-context' LLM "
             "baselines need model runs and are NOT in this table.", "",
             "| Phase | n | chance | longest option | letter-prior | stem-overlap | answer-text majority |",
             "|---|---|---|---|---|---|---|"]
    out = {}
    for ph in PHASES:
        qs = by_phase.get(ph, [])
        if not qs:
            continue
        n = len(qs)
        chance = np.mean([1 / len(q["options"]) for q in qs])
        longest = sum(max(q["options"], key=lambda k: len(q["options"][k])) == q["correct_answer"] for q in qs)
        letter = Counter(q["correct_answer"] for q in qs).most_common(1)[0][1]
        ov = 0
        for q in qs:
            st = _toks(q["question"])
            best = max(q["options"], key=lambda k: len(st & _toks(q["options"][k])))
            ov += best == q["correct_answer"]
        text_maj = Counter(canonical_answer_text(q["correct_answer_text"]) for q in qs).most_common(1)[0][1]

        def cell(k):
            lo, hi = wilson(k, n)
            return f"{100 * k / n:.0f}% [{100 * lo:.0f}–{100 * hi:.0f}]"
        lines.append(f"| {ph} | {n} | {100 * chance:.0f}% | {cell(longest)} | {cell(letter)} | {cell(ov)} | {cell(text_maj)} |")
        out[ph] = {"n": n, "chance": float(chance), "longest": longest, "letter_prior": letter,
                   "stem_overlap": ov, "text_majority": text_maj}
    return out, lines


def main():
    rng = np.random.default_rng(SEED)
    res, md = {}, ["# LUMIERE reviewer-round-2 statistics (v3)", "",
                   f"Generated by `tools/lumiere_reviewer_stats.py`, seed {SEED}, {N_BOOT:,} bootstrap resamples.", ""]
    for name, fn in (("accuracy", lambda: accuracy_section(rng)),
                     ("counterfactual", lambda: counterfactual_section(rng)),
                     ("baselines", baseline_section)):
        r, lines = fn()
        res[name] = r
        md += lines + [""]
    text = "\n".join(md)
    print(text)
    Path("results/lumiere_reviewer_stats.md").write_text(text)
    Path("results/lumiere_reviewer_stats.json").write_text(json.dumps(res, indent=2, default=float))
    print("Saved -> results/lumiere_reviewer_stats.{md,json}")


if __name__ == "__main__":
    main()
