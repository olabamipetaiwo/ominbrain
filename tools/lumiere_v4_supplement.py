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
                if not a1:
                    cnt["no_answer"] += 1
                elif a1 == exp:
                    cnt["already_at_new" if a0 == exp else "moved_to_new"] += 1
                elif a1 == a0:
                    cnt["unchanged_elsewhere"] += 1
                else:
                    cnt["changed_to_other"] += 1
            n = len(keep)
            informative = n - cnt["already_at_new"]
            out[f"{cond}|{subset}"] = {"n": n, **{k: cnt[k] for k in ("moved_to_new", "already_at_new", "unchanged_elsewhere", "changed_to_other", "no_answer")},
                                       "follows_rule_total": 100 * (cnt["moved_to_new"] + cnt["already_at_new"]) / n,
                                       "informative_n": informative,
                                       "moved_of_informative": 100 * cnt["moved_to_new"] / informative if informative else float("nan")}
    return out


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
    res: dict = {"audit": audit(), "audit_size": audit_size_sensitivity(), "pjrf_origin": pjrf_origin_check(), "models": {}}
    all_recs = {}
    for m in MODELS + CONTROLS:
        recs = load_records(m)
        if not recs:
            continue
        all_recs[m] = recs
        r = {"handling": handling(recs), "outcomes": outcomes(recs), "dscr_valid_json": dscr_valid_json(recs)}
        if m in MODELS:
            r["transitions"] = transitions(recs, flags)
            r["pjrf"] = pjrf(recs, rng)
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
    md += ["", "## E. PJRF (true context): Brier difference to the leave-one-out base rate (negative = better than the constant)", "",
           "| Model | n | no forecast | diff [95% CI], no forecast = 0.5 | answered n | diff [95% CI], answered only |", "|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        v = r.get("pjrf")
        if v:
            ans = (f"{v['answered_n']} | {v['answered_diff_to_base']:+.3f} [{v['answered_diff_ci'][0]:+.3f}, {v['answered_diff_ci'][1]:+.3f}]"
                   if "answered_n" in v else "- | -")
            md.append(f"| {m} | {v['n']} | {v['no_forecast']} | {v['diff_to_base']:+.3f} [{v['diff_ci'][0]:+.3f}, {v['diff_ci'][1]:+.3f}] | {ans} |")
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
