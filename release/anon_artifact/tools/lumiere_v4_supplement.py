"""
Post-review descriptive supplement to tools/lumiere_v4_stats.py (CPU only; added 2026-09-25 after the first external review).

Nothing here changes the pre-registered analyses; every quantity below is descriptive and unadjusted and is labelled as
added after the runs. It reports what the review asked for and the registered analysis did not:

  A. Audit breakdown      agreement among determinate follow-ups only, and the expert-by-rule confusion matrix.
  B. Output handling      per model x phase: records, parse failures, records with no answer letter.
  C. Three outcomes       output sensitivity (own vs text answers differ; swapped vs own answers differ), to sit beside the
                          accuracy benefit and donor tracking that the stats file already reports.
  D. E3 transitions       for the two fact flips, paired against the same item under the true context: how many answers
                          moved to the rule's new answer, were already there, stayed elsewhere, or changed to another
                          answer; the informative rate is moved / (items whose original answer was not already the new one).
  E. PJRF                 no-forecast items counted separately, Brier difference to the base rate with a patient bootstrap
                          CI, and the same on answered items only.

Writes results/lumiere_v4_supplement.{md,json}.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from tools.lumiere_gating_stats import wilson
from tools.lumiere_v4_stats import CONTROLS, IMG_PHASES, MODELS, N_BOOT, SEED, boot_ci, item_flags, load_records


def _none(r) -> bool:
    return not (r and r.get("model_answer"))


def audit() -> dict:
    s = json.loads(Path("data/lumiere/v4/selection_report.json").read_text())
    c = s["rule_vs_expert_concordance"]
    n_und = s["n_undetermined_followups"]
    lo, hi = wilson(c["concordant"], c["n"])
    conf = c["confusion_expert_by_rule"]
    by_rule = Counter()
    for k, v in conf.items():
        e, r = k.split("|")
        if e != r:
            by_rule[r] += v
    return {"followups": c["n"] + n_und, "undetermined": n_und, "determinate": c["n"], "concordant": c["concordant"],
            "pct_of_all": 100 * c["concordant"] / (c["n"] + n_und), "pct_of_determinate": 100 * c["concordant"] / c["n"],
            "wilson_determinate": [100 * lo, 100 * hi], "disagreements": c["n"] - c["concordant"],
            "disagreements_by_rule_label": dict(by_rule), "by_expert": c["by_expert_label"], "confusion_expert_by_rule": conf,
            "undetermined_by_expert": s["undetermined_by_expert"]}


def audit_clustered() -> dict:
    """Patient-clustered uncertainty for the audit. The follow-ups are repeated visits of the same patients, so the Wilson interval
    (which treats them as independent) is too narrow if agreement is patient-specific; resample patients instead."""
    from src.lumiere_v4 import enumerate_candidates
    rng = np.random.default_rng(SEED + 7)
    per = {}
    for pid, r in enumerate_candidates().items():
        per[pid] = ([bool(c["concordant"]) for c in r["candidates"]], len(r["undetermined"]))
    # patients with only undetermined follow-ups are not returned by enumerate_candidates; the counts are reconciled with the selection report
    pids = sorted(per)
    det = np.array([len(per[p][0]) for p in pids], float)
    agree = np.array([sum(per[p][0]) for p in pids], float)
    und = np.array([per[p][1] for p in pids], float)
    idx = rng.integers(0, len(pids), size=(N_BOOT, len(pids)))
    b_det = agree[idx].sum(axis=1) / np.maximum(det[idx].sum(axis=1), 1)
    b_all = agree[idx].sum(axis=1) / np.maximum((det + und)[idx].sum(axis=1), 1)
    sr = json.loads(Path("data/lumiere/v4/selection_report.json").read_text())
    return {"patients": len(pids), "followups_by_patient_min": int((det + und).min()), "followups_by_patient_max": int((det + und).max()),
            "followups_by_patient_median": float(np.median(det + und)),
            "determinate": int(det.sum()), "concordant": int(agree.sum()), "undetermined": int(und.sum()),
            "matches_selection_report": bool(int(det.sum()) == sr["rule_vs_expert_concordance"]["n"]
                                              and int(agree.sum()) == sr["rule_vs_expert_concordance"]["concordant"]
                                              and int(und.sum()) == sr["n_undetermined_followups"]),
            "pct_determinate": float(agree.sum() / det.sum() * 100),
            "cluster_ci_determinate": [float(np.percentile(b_det, 2.5)) * 100, float(np.percentile(b_det, 97.5)) * 100],
            "pct_all": float(agree.sum() / (det + und).sum() * 100),
            "cluster_ci_all": [float(np.percentile(b_all, 2.5)) * 100, float(np.percentile(b_all, 97.5)) * 100]}


def audit_size_sensitivity() -> dict:
    """Does agreement with the expert depend on how close our measured enhancing product is to the product of the diameters the rater
    recorded for the target lesion (LUMIERE rationale text)? Only follow-ups where the rater recorded both diameters can be used."""
    import re
    from scipy.stats import fisher_exact
    from src.lumiere_v4 import enumerate_candidates
    rows = []
    for r in enumerate_candidates().values():
        for c in r["candidates"]:
            m = re.search(r"(\d+)\s*mm\s*x\s*(\d+)\s*mm", str(c["rationale"]))
            if m and c["bp_fu"] > 0:
                rows.append((c["bp_fu"] / (int(m.group(1)) * int(m.group(2))), bool(c["concordant"]), c["expert"]))
    out = {"n": len(rows), "expert_counts": dict(Counter(e for *_, e in rows)), "agree": sum(c for _, c, _ in rows)}
    for lo, hi in ((0.67, 1.5),):
        close = [c for r_, c, _ in rows if lo <= r_ <= hi]
        far = [c for r_, c, _ in rows if not lo <= r_ <= hi]
        a, b = sum(close), sum(far)
        out[f"ratio_{lo}_{hi}"] = {"close_n": len(close), "close_agree": a, "other_n": len(far), "other_agree": b,
                                   "fisher_p": float(fisher_exact([[a, len(close) - a], [b, len(far) - b]])[1])}
    return out


def audit_new_lesion_pattern(min_dist_mm: float = 15.0, similar_frac: float = 0.5) -> dict:
    """Of the follow-ups where the rule says complete response but the expert rated progressive disease,
    how many show a plausible 'new lesion elsewhere' pattern that our tracked-lesion rule cannot see (it
    has no RANO new-lesion criterion; paper/review.md concern 1 follow-up, 2026-09-28)? For each such
    follow-up: is there another enhancing component, at least `min_dist_mm` from the tracked lesion, that
    is itself measurable and either absent or under `similar_frac` of its own size at the nadir?"""
    from src.lumiere_measure import measurable, nearest_component
    from src.lumiere_v4 import enumerate_candidates, load_measure

    def others(anchor, comps):
        if anchor is None:
            return comps
        a = np.array(anchor)
        return [c for c in comps if float(np.linalg.norm(np.array(c["centroid_xyz"]) - a)) > min_dist_mm]

    counts = Counter()
    for pid, rec in enumerate_candidates().items():
        for c in rec["candidates"]:
            if not (c["expert"] == "progressive disease" and c["rule"] == "complete response"):
                continue
            m_ref, m_fu, m_nad = load_measure(pid, rec["ref"]), load_measure(pid, c["tp"]), load_measure(pid, c["nadir_tp"])
            anchor = m_ref["enh"]["centroid_xyz"] if (m_ref or {}).get("enh") else None
            fu_others = [o for o in others(anchor, (m_fu or {}).get("enh_components") or [])
                         if measurable(o["d1_mm"], o["d2_mm"])]
            if not fu_others:
                counts["no_distinct_measurable_component_elsewhere"] += 1
                continue
            biggest = max(fu_others, key=lambda o: o["bp_mm2"])
            match = nearest_component(biggest["centroid_xyz"], others(anchor, (m_nad or {}).get("enh_components") or []))
            preexisting = match is not None and measurable(match["d1_mm"], match["d2_mm"]) and match["bp_mm2"] >= similar_frac * biggest["bp_mm2"]
            counts["preexisting_secondary_lesion" if preexisting else "plausible_new_lesion"] += 1
    n = sum(counts.values())
    return {"n": n, **dict(counts)}


def handling(recs) -> dict:
    cells: dict = {}
    for (c, ph, cond), r in recs.items():
        d = cells.setdefault((ph, cond), [0, 0, 0])
        d[0] += 1
        d[1] += bool(r.get("parse_error"))
        d[2] += _none(r)
    out = {f"{ph}|{cond}": {"n": n, "parse_error": pe, "no_answer": na} for (ph, cond), (n, pe, na) in sorted(cells.items())}
    tot = [sum(v[i] for v in cells.values()) for i in range(3)]
    out["ALL"] = {"n": tot[0], "parse_error": tot[1], "no_answer": tot[2]}
    return out


def dscr_valid_json(recs) -> dict:
    """DSCR own-image accuracy on all records and on records whose JSON parsed (does parsing explain a low score?)."""
    rs = [v for (c, p, k), v in recs.items() if p == "DSCR" and k == "own"]
    ok = [v for v in rs if not v.get("parse_error")]
    if not rs or not ok:
        return {}
    return {"n": len(rs), "acc_all": 100 * sum(bool(v["correct"]) for v in rs) / len(rs), "n_valid": len(ok),
            "acc_valid": 100 * sum(bool(v["correct"]) for v in ok) / len(ok),
            "letters": dict(Counter(v["model_answer"] for v in rs))}


def outcomes(recs) -> dict:
    out = {}
    for ph in IMG_PHASES:
        cs = [c for c in sorted({k[0] for k in recs if k[1] == ph}) if all((c, ph, k) in recs for k in ("own", "text", "swap"))]
        if not cs:
            continue
        own, txt, sw = ([recs[(c, ph, k)] for c in cs] for k in ("own", "text", "swap"))
        out[ph] = {"n": len(cs),
                   "own_vs_text_answer_differs": float(np.mean([a["model_answer"] != b["model_answer"] for a, b in zip(own, txt)]) * 100),
                   "swap_vs_own_answer_differs": float(np.mean([a["model_answer"] != b["model_answer"] for a, b in zip(sw, own)]) * 100)}
    return out


def transitions(recs, flags) -> dict:
    """Per condition x subset, how answers move under a context flip.

    Baseline eligibility ("informative") is defined from the BASELINE true-context answer alone, before the
    flipped answer is examined (matching the table caption): an item is informative iff its baseline answer was
    NOT already the new target. ``already_at_new`` therefore counts every item whose baseline answer equals the
    target, whether it then stays or moves away, and those items are excluded from the informative denominator.
    ``stayed_at_target`` and ``started_at_target_moved_away`` split that excluded set, so items that begin at the
    target and then leave it are reported separately rather than silently inflating the follows-rule rate."""
    out = {}
    for cond in ("flip_label", "flip_window"):
        cs = sorted(c for (c, p, k) in recs if p == "TCM" and k == cond and (c, "TCM", "ctx_gold") in recs)
        for subset, keep in (("all", cs), ("pd", [c for c in cs if flags[c]["tcm_rano"] == "progressive disease"])):
            if not keep:
                continue
            cnt = Counter()
            for c in keep:
                base, new = recs[(c, "TCM", "ctx_gold")], recs[(c, "TCM", cond)]
                exp = new["expected_letter"]
                a0, a1 = base.get("model_answer"), new.get("model_answer")
                if a0 == exp:                       # baseline already at target -> NOT informative (excluded)
                    cnt["already_at_new"] += 1
                    cnt["stayed_at_target" if a1 == exp else "started_at_target_moved_away"] += 1
                    continue
                if not a1:                          # baseline not at target -> informative from here on
                    cnt["no_answer"] += 1
                elif a1 == exp:
                    cnt["moved_to_new"] += 1
                elif a1 == a0:
                    cnt["unchanged_elsewhere"] += 1
                else:
                    cnt["changed_to_other"] += 1
            n = len(keep)
            informative = n - cnt["already_at_new"]
            out[f"{cond}|{subset}"] = {"n": n,
                                       **{k: cnt[k] for k in ("moved_to_new", "already_at_new", "stayed_at_target",
                                                              "started_at_target_moved_away", "unchanged_elsewhere",
                                                              "changed_to_other", "no_answer")},
                                       "follows_rule_total": 100 * (cnt["moved_to_new"] + cnt["stayed_at_target"]) / n,
                                       "informative_n": informative,
                                       "moved_of_informative": 100 * cnt["moved_to_new"] / informative if informative else float("nan")}
    return out


def explicit_rule(recs, rng) -> dict:
    """TCM with the management rule stated in the prompt versus the same items under the true context without it (paired by patient)."""
    cs = sorted(c for (c, p, k) in recs if p == "TCM" and k == "explicit_rule" and (c, "TCM", "ctx_gold") in recs)
    if not cs:
        return {}
    a = np.array([1.0 if recs[(c, "TCM", "explicit_rule")].get("correct") else 0.0 for c in cs])
    b = np.array([1.0 if recs[(c, "TCM", "ctx_gold")].get("correct") else 0.0 for c in cs])
    lo, hi = boot_ci(a - b, rng)
    return {"n": len(cs), "acc_explicit": float(a.mean() * 100), "acc_gold": float(b.mean() * 100),
            "diff": float((a - b).mean() * 100), "diff_ci": [lo * 100, hi * 100],
            "only_explicit": int(((a == 1) & (b == 0)).sum()), "only_gold": int(((a == 0) & (b == 1)).sum()),
            "parse_error_explicit": sum(bool(recs[(c, "TCM", "explicit_rule")].get("parse_error")) for c in cs),
            "parse_error_gold": sum(bool(recs[(c, "TCM", "ctx_gold")].get("parse_error")) for c in cs)}


def donor_dependence(recs, rng, n_perm: int = 5000) -> dict:
    """E2 sensitivity to the donor assignment (post hoc; the registered interval resamples recipients only).

    Each patient can donate to up to two recipients, and a patient is both a recipient and a donor, so recipients that share
    a donor (or are each other's donor) are not independent. Two checks per phase:
      * donor-cluster bootstrap and leave-one-donor-out: recipients that share a donor image are one cluster and whole
        clusters are resampled or dropped (the estimand stays conditional on the fixed assignment but respects shared donors);
      * assignment permutation: the donor key text is permuted among recipients (never onto the recipient's own key), and
        the gain recomputed with the observed answers; p is the share of permutations with a gain at least as large.

    SCOPE OF THE PERMUTATION TEST (interpretation, per reviewer round 3): this is a conditional LABEL-ASSOCIATION test,
    not a design-based assignment test. It holds the recipients and their observed answers fixed and shuffles the donor-key
    labels across recipients subject only to never landing on a recipient's own key. It does NOT reconstruct the original
    constrained assignment mechanism: it does not preserve the matching-scan-count strata and does not keep the label block
    of a donor used by two recipients together. It therefore answers only the narrow question of whether answers are more
    aligned to their own donor's key than to a random other donor's key; it does not license a design-based claim about the
    randomized image assignment. ``n_perm`` in the output is the number of permutations actually ACCEPTED (collision repair
    can fail and skip a draw), which is <= the attempted count and is what should be reported."""
    out = {}
    for ph in IMG_PHASES:
        cs = [c for c in sorted({k[0] for k in recs if k[1] == ph and k[2] == "swap"})
              if (c, ph, "text") in recs and (c, ph, "own") in recs]
        if len(cs) < 5:
            continue
        # the runner shows each question's options in a fixed shuffled order (src.lumiere_loader._shuffle_options, seeded by id);
        # rebuild it to translate answer letters back to option texts
        from src.lumiere_loader import _shuffle_options
        opts = {}
        strat = {}
        for c in cs:
            it = next(x for x in json.loads(Path(f"data/lumiere/v4/reviewed/{c}.json").read_text()) if x["id"].endswith("_" + ph))
            opts[c] = it["options"] if it.get("ordered_options") else _shuffle_options(it["options"], it["correct_answer"], it["id"])[0]
            strat[c] = len(it["image_files"])      # equal-image-count stratum (DSCR 2 or 3 slices; AIA/LIL 1)
        sw = [recs[(c, ph, "swap")] for c in cs]
        tx = [recs[(c, ph, "text")] for c in cs]
        donor = [r["donor"] for r in sw]
        dkey = [r["donor_key_text"] for r in sw]
        okey = [r["own_key_text"] for r in sw]
        stratum = [strat[c] for c in cs]
        sw_txt = [opts[c].get(r["model_answer"]) for c, r in zip(cs, sw)]
        tx_txt = [opts[c].get(r["model_answer"]) for c, r in zip(cs, tx)]
        g = np.array([float(s_ == d) - float(t_ == d) for s_, t_, d in zip(sw_txt, tx_txt, dkey)])
        # cluster = recipients that share a donor image (each recipient has exactly one donor); connected components of the
        # recipient-donor graph are useless here because every patient is both a donor and a recipient (2-4 components)
        comp: dict = {}
        for i, d in enumerate(donor):
            comp.setdefault(d, []).append(i)
        groups = list(comp.values())
        sums = np.array([g[idx].sum() for idx in groups])
        sizes = np.array([len(idx) for idx in groups])
        pick = rng.integers(0, len(groups), size=(N_BOOT, len(groups)))
        boot = sums[pick].sum(axis=1) / sizes[pick].sum(axis=1)
        # leave-one-donor-out: gain after dropping every recipient of one donor
        loo = [float((g.sum() - sums[k]) / (len(g) - sizes[k])) * 100 for k in range(len(groups))]
        # assignment permutation: stratified, donor-grouped (permutes donor keys only within the equal-image-count
        # stratum and keeps each reused donor's recipients as one block). Single engine, so the synthetic-predictor
        # validation and the robustness re-runs (which also call this function) use the same test.
        obs = float(g.mean())
        n = len(cs)
        from tools.lumiere_v4_strat_perm import perm_p_from_arrays
        perm_p, done = perm_p_from_arrays(sw_txt, tx_txt, dkey, okey, donor, stratum, rng, n_perm=n_perm)
        uses = Counter(donor)
        out[ph] = {"n": n, "distinct_donors": len(uses), "max_uses": max(uses.values()), "donors_used_twice": sum(v > 1 for v in uses.values()),
                   "strata": dict(Counter(stratum)),
                   "loo_donor_min": min(loo), "loo_donor_max": max(loo),
                   "gain": obs * 100, "cluster_ci": [float(np.percentile(boot, 2.5)) * 100, float(np.percentile(boot, 97.5)) * 100],
                   "perm_p": perm_p, "n_perm": done}
    return out


def _unstratified_perm_p(sw_txt, tx_txt, dkey, okey, rng, n_perm: int = 5000) -> float:
    """The earlier unstratified, ungrouped donor-key permutation (collision-repaired whole permutation), kept only as
    a diagnostic comparison for ``tools.lumiere_v4_strat_perm``; not used in the reported results."""
    n = len(sw_txt)
    obs = float(np.mean([float(s_ == d) - float(t_ == d) for s_, t_, d in zip(sw_txt, tx_txt, dkey)]))
    ge = 0
    done = 0
    for _ in range(n_perm):
        perm = list(rng.permutation(n))
        for _fix in range(20):
            bad = [i for i in range(n) if dkey[perm[i]] == okey[i]]
            if not bad:
                break
            for i in bad:
                j = int(rng.integers(0, n))
                perm[i], perm[j] = perm[j], perm[i]
        else:
            continue
        gp = np.mean([float(s_ == dkey[perm[i]]) - float(t_ == dkey[perm[i]]) for i, (s_, t_) in enumerate(zip(sw_txt, tx_txt))])
        done += 1
        ge += gp >= obs - 1e-12
    return (1 + ge) / (1 + done)


def pjrf(recs, rng) -> dict:
    rs = [r for (c, p, k), r in sorted(recs.items()) if p == "PJRF" and k == "ctx_gold"]
    if not rs:
        return {}
    y = np.array([r["forecast_outcome"] for r in rs], float)
    ok = np.array([r["forecast_prob"] is not None for r in rs])
    p = np.array([r["forecast_prob"] if r["forecast_prob"] is not None else 0.5 for r in rs])
    loo = np.array([np.delete(y, i).mean() for i in range(len(y))])
    d = (p - y) ** 2 - (loo - y) ** 2
    lo, hi = boot_ci(d, rng)
    res = {"n": len(rs), "no_forecast": int((~ok).sum()), "diff_to_base": float(d.mean()), "diff_ci": [lo, hi]}
    if ok.sum() > 5:
        da = d[ok]
        lo, hi = boot_ci(da, rng)
        res.update({"answered_n": int(ok.sum()), "answered_diff_to_base": float(da.mean()), "answered_diff_ci": [lo, hi]})
    return res


def pjrf_origin_check() -> dict:
    """What can be checked about the PJRF outcome without the (undocumented) time origin and censoring.

    LUMIERE documents that all dates are relative to the pre-operative image, but neither the paper nor the readme states the origin
    of overall survival or mentions censoring. Two internal checks: (a) survival shorter than the last imaging week (impossible
    if both share an origin and the patient was imaged alive); (b) how many of the v4 outcome labels (death within 52 weeks of the
    scan) could flip if the survival origin were shifted by a few weeks."""
    import re
    import pandas as pd
    d = pd.read_csv("data/lumiere/tabular/LUMIERE-Demographics_Pathology.csv")
    d["os"] = pd.to_numeric(d["Survival time (weeks)"], errors="coerce")
    wk = lambda t: int(m.group(1)) if (m := re.match(r"week-(\d+)", str(t))) else None    # noqa: E731
    img = pd.read_csv("data/lumiere/tabular/LUMIERE-datacompleteness.csv")
    img["w"] = img["Timepoint"].map(wk)
    last = img.groupby("Patient")["w"].max()
    k = d.set_index("Patient")[["os"]].join(last.rename("last_img")).dropna(subset=["os"])
    short = k[k.os < k.last_img]
    rows = []
    for f in sorted(Path("data/lumiere/v4/reviewed").glob("Patient-*.json")):
        it = next((x for x in json.loads(f.read_text()) if x["id"].endswith("_PJRF")), None)
        if it:
            fu = it["facts_used"]
            rows.append((f.stem, fu["survival_weeks"], fu["prediction_week"]))
    flips = {}
    for sh in (2, 4, 8, 12):
        flips[sh] = sum(1 for _, s_, p_ in rows if len({s_ - sh - p_ <= 52, s_ - p_ <= 52, s_ + sh - p_ <= 52}) > 1)
    return {"patients": len(d), "with_survival": len(k), "without_survival": int(d.os.isna().sum()),
            "survival_before_last_imaging": len(short),
            "survival_before_last_imaging_detail": {i: [float(r.os), int(r.last_img)] for i, r in short.iterrows()},
            "in_v4_cohort": [i for i in short.index if i in {r[0] for r in rows}], "v4_pjrf_items": len(rows),
            "labels_that_flip_under_origin_shift": flips}


def aia_confusions(models_recs) -> dict:
    """Key sequence x answered sequence (own image), per model, and the reference model's item-level errors."""
    from collections import defaultdict
    from src.lumiere_loader import _shuffle_options
    items = {}
    for f in Path("data/lumiere/v4/reviewed").glob("Patient-*.json"):
        for it in json.loads(f.read_text()):
            items[it["id"]] = it

    def opts(it):
        o, c = it["options"], it["correct_answer"]
        return (o, c) if it.get("ordered_options") else _shuffle_options(o, c, it["id"])
    short = {"T1-weighted, before contrast": "T1", "T1-weighted, after gadolinium contrast": "T1c", "T2-weighted": "T2",
             "FLAIR (fluid-attenuated inversion recovery)": "FLAIR"}
    out = {"confusion": {}, "reference_errors": []}
    for m, recs in models_recs.items():
        conf = defaultdict(Counter)
        for (c, ph, k), v in recs.items():
            if ph == "AIA" and k == "own":
                o, cl = opts(items[f"{c}_AIA"])
                assert cl == v["correct_answer"], (m, c)
                conf[short.get(o[v["correct_answer"]], o[v["correct_answer"]])][short.get(o.get(v["model_answer"]), "none")] += 1
        out["confusion"][m] = {k: dict(v) for k, v in sorted(conf.items())}
    out["modal_answer_share"] = {}
    for m, conf in out["confusion"].items():
        tot = Counter()
        for row in conf.values():
            tot.update(row)
        seq, n = tot.most_common(1)[0]
        out["modal_answer_share"][m] = {"sequence": seq, "n": n, "share": 100 * n / sum(tot.values())}
    ref = models_recs.get("Gemini-3.6-Flash", {})
    for (c, ph, k), v in sorted(ref.items()):
        if ph in ("AIA", "LIL") and k == "own" and not v["correct"]:
            o, cl = opts(items[f"{c}_{ph}"])
            out["reference_errors"].append({"patient": c, "phase": ph, "key": o[v["correct_answer"]], "answered": o.get(v["model_answer"])})
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    flags = item_flags()
    res: dict = {"audit": audit(), "audit_clustered": audit_clustered(), "audit_size": audit_size_sensitivity(), "audit_new_lesion": audit_new_lesion_pattern(),
                 "pjrf_origin": pjrf_origin_check(), "models": {}}
    all_recs = {}
    for m in MODELS + CONTROLS:
        recs = load_records(m)
        if not recs:
            continue
        all_recs[m] = recs
        r = {"handling": handling(recs), "outcomes": outcomes(recs), "dscr_valid_json": dscr_valid_json(recs)}
        if m in MODELS:
            r["transitions"] = transitions(recs, flags)
            r["explicit_rule"] = explicit_rule(recs, rng)
            r["pjrf"] = pjrf(recs, rng)
        if m in MODELS:
            r["donor_dependence"] = donor_dependence(recs, rng)
        res["models"][m] = r
    res["aia"] = aia_confusions(all_recs)
    a = res["audit"]
    full = {"CR": "complete response", "PR": "partial response", "SD": "stable disease", "PD": "progressive disease"}
    md = ["# LUMIERE v4 post-review supplement", "",
          f"Generated by `tools/lumiere_v4_supplement.py`; seed {SEED}, {N_BOOT:,} resamples. Descriptive, unadjusted, added after the runs "
          "(not part of the pre-registered analysis).", "",
          "## A. Audit: rule versus expert RANO rating", "",
          f"{a['followups']} first-line follow-ups; {a['undetermined']} undetermined (no measurable enhancing disease on the baseline or nadir); "
          f"{a['determinate']} determinate. The rule agrees with the expert in {a['concordant']}: {a['pct_of_all']:.1f}% of all follow-ups, "
          f"{a['pct_of_determinate']:.1f}% of determinate ones (Wilson 95% [{a['wilson_determinate'][0]:.1f}, {a['wilson_determinate'][1]:.1f}]).", "",
          f"Disagreements ({a['disagreements']}) by the rule's label: {a['disagreements_by_rule_label']}.", "",
          "| expert \\ rule | CR | PR | SD | PD | undetermined |", "|---|---|---|---|---|---|"]
    for e in ("PD", "SD", "PR", "CR"):
        row = [str(a["confusion_expert_by_rule"].get(f"{full[e]}|{full[r_]}", 0)) for r_ in ("CR", "PR", "SD", "PD")]
        md.append(f"| {e} | " + " | ".join(row) + f" | {a['undetermined_by_expert'].get(full[e], 0)} |")
    phs = IMG_PHASES + ["PJRF", "TCM"]
    md += ["", "## B. Output handling (records / parse failures / no answer letter)", "",
           "| Model | " + " | ".join(phs) + " | all |", "|---" * (len(phs) + 2) + "|"]
    for m, r in res["models"].items():
        cells = []
        for ph in phs:
            n = pe = na = 0
            for k, v in r["handling"].items():
                if k.split("|")[0] == ph:
                    n, pe, na = n + v["n"], pe + v["parse_error"], na + v["no_answer"]
            cells.append(f"{n} / {pe} / {na}")
        h = r["handling"]["ALL"]
        md.append(f"| {m} | " + " | ".join(cells) + f" | {h['n']} / {h['parse_error']} / {h['no_answer']} |")
    md += ["", "## C. Output sensitivity (percent of items whose answer letter differs)", "",
           "| Model | Phase | own vs text-only | swapped vs own |", "|---|---|---|---|"]
    for m, r in res["models"].items():
        for ph, v in r["outcomes"].items():
            md.append(f"| {m} | {ph} | {v['own_vs_text_answer_differs']:.1f} | {v['swap_vs_own_answer_differs']:.1f} |")
    md += ["", "## D. TCM fact flips, paired against the same item under the true context", "",
           "| Model | flip | items | moved to new | already at new | unchanged elsewhere | changed to other | no answer | moved / informative |", "|---|---|---|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        for k, v in r.get("transitions", {}).items():
            md.append(f"| {m} | {k} | {v['n']} | {v['moved_to_new']} | {v['already_at_new']} | {v['unchanged_elsewhere']} | "
                      f"{v['changed_to_other']} | {v['no_answer']} | {v['moved_of_informative']:.1f}% of {v['informative_n']} |")
    md += ["", "## D2. TCM with the management rule stated in the prompt (explicit_rule) versus the true context without it, paired by patient", "",
           "| Model | n | true context | rule stated | diff [95% CI] | only rule / only context | parse errors (context / rule) |", "|---|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        v = r.get("explicit_rule")
        if v:
            md.append(f"| {m} | {v['n']} | {v['acc_gold']:.1f} | {v['acc_explicit']:.1f} | {v['diff']:+.1f} [{v['diff_ci'][0]:+.1f}, {v['diff_ci'][1]:+.1f}] | "
                      f"{v['only_explicit']} / {v['only_gold']} | {v['parse_error_gold']} / {v['parse_error_explicit']} |")
    md += ["", "## E. PJRF (true context): Brier difference to the leave-one-out base rate (negative = better than the constant)", "",
           "| Model | n | no forecast | diff [95% CI], no forecast = 0.5 | answered n | diff [95% CI], answered only |", "|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        v = r.get("pjrf")
        if v:
            ans = (f"{v['answered_n']} | {v['answered_diff_to_base']:+.3f} [{v['answered_diff_ci'][0]:+.3f}, {v['answered_diff_ci'][1]:+.3f}]"
                   if "answered_n" in v else "- | -")
            md.append(f"| {m} | {v['n']} | {v['no_forecast']} | {v['diff_to_base']:+.3f} [{v['diff_ci'][0]:+.3f}, {v['diff_ci'][1]:+.3f}] | {ans} |")
    md += ["", "## I. E2 donor dependence (post hoc): donor-cluster bootstrap, leave-one-donor-out and assignment permutation", "",
           "| Model | Phase | n | distinct donors | max uses | gain | donor-cluster bootstrap 95% CI | leave-one-donor-out range | permutation p |", "|---|---|---|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        for ph, v in r.get("donor_dependence", {}).items():
            md.append(f"| {m} | {ph} | {v['n']} | {v['distinct_donors']} | {v['max_uses']} | {v['gain']:+.1f} | "
                      f"[{v['cluster_ci'][0]:+.1f}, {v['cluster_ci'][1]:+.1f}] | [{v['loo_donor_min']:+.1f}, {v['loo_donor_max']:+.1f}] | {v['perm_p']:.3f} |")
    ac = res["audit_clustered"]
    md += ["", "## A2. Audit with patient-clustered uncertainty", "",
           f"{ac['determinate'] + ac['undetermined']} follow-ups from {ac['patients']} patients ({ac['followups_by_patient_min']} to {ac['followups_by_patient_max']} per patient, "
           f"median {ac['followups_by_patient_median']:.0f}); reconciles with the selection report: {ac['matches_selection_report']}. Agreement among determinate follow-ups "
           f"{ac['pct_determinate']:.1f}% (patient-bootstrap 95% [{ac['cluster_ci_determinate'][0]:.1f}, {ac['cluster_ci_determinate'][1]:.1f}]); among all follow-ups "
           f"{ac['pct_all']:.1f}% ([{ac['cluster_ci_all'][0]:.1f}, {ac['cluster_ci_all'][1]:.1f}])."]
    z = res["audit_size"]
    k = z["ratio_0.67_1.5"]
    md += ["", "## H. Audit: agreement by closeness of our lesion size to the rater's recorded target-lesion size", "",
           f"{z['n']} follow-ups have both (expert labels {z['expert_counts']}). Agreement with the expert when our product is within a factor of 1.5 of the "
           f"rater's: {k['close_agree']}/{k['close_n']}; otherwise {k['other_agree']}/{k['other_n']} (Fisher p = {k['fisher_p']:.2f})."]
    o = res["pjrf_origin"]
    md += ["", "## F. PJRF outcome: what can be checked about the survival time origin", "",
           f"{o['with_survival']} of {o['patients']} patients have a survival time. Survival shorter than the last imaging week (impossible if survival and "
           f"scan weeks share an origin and the patient was imaged alive): {o['survival_before_last_imaging']} patients {o['survival_before_last_imaging_detail']}; "
           f"in the v4 cohort: {o['in_v4_cohort']}. Of {o['v4_pjrf_items']} v4 PJRF labels, the number that could flip if the origin were shifted by "
           f"2/4/8/12 weeks: {o['labels_that_flip_under_origin_shift']}.",
           "", "## G. AIA: key sequence (rows) by answered sequence (own image), and the reference model's errors", "",
           "| model | key: {answered: n} |", "|---|---|"]
    for m, conf in res["aia"]["confusion"].items():
        md.append(f"| {m} | " + "; ".join(f"{k}: {v}" for k, v in conf.items()) + " |")
    md += ["", "Reference-model errors: " + "; ".join(f"{e['patient']} {e['phase']} key {e['key']} answered {e['answered']}" for e in res["aia"]["reference_errors"])]
    text = "\n".join(md)
    Path("results/lumiere_v4_supplement.md").write_text(text)
    Path("results/lumiere_v4_supplement.json").write_text(json.dumps(res, indent=2, default=float))
    print(text)


if __name__ == "__main__":
    main()
