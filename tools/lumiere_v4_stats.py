"""
Analysis of the v4 intervention runs, as specified in paper/preregistration_v4.md (CPU only).

Reads results/lumiere_v4_<model>_*/raw_results.json (several job folders per model are merged; a later record for the
same case/phase/condition replaces an earlier one) and, for the secondary chain analysis, the ordinary chain runs
results/lumiere_<model>_v4_nogate_* and results/lumiere_<model>_textonly_v4_nogate_*.

Estimands (per model), unit = patient (one question per phase, so patient-clustered = item-level paired):
  E1  image effect        acc(own image) - acc(text only), paired, phases AIA (positive control), LIL, DSCR.
                          verdict: "image helps" if the 95% bootstrap CI is above 0; "within margin" if the CI lies
                          inside (-MARGIN, +MARGIN); otherwise "inconclusive".
  E2  donor tracking      G = mean(1[swap answer = donor key] - 1[text answer = donor key]): does the shown image move
                          answers toward its own label beyond the no-image prior? Also own-key retention.
  E3  TCM fact use        share of answers following the rule after (a) the stated label is flipped (flip_label) and
                          (b) the stated timing moves across the 12-week window (flip_window; progressive-disease items
                          are the informative ones), and accuracy under gold/wrong/absent context by rule class.
  E4  context effects     paired accuracy differences gold / wrong / absent for LIL, DSCR, PJRF, TCM.
  E5  PJRF forecast       Brier score against the recorded outcome, Brier skill against the leave-one-out constant
                          base rate, AUC.
  E6  chain total effect  (secondary) own-chain image vs text-only per phase from the ordinary chain runs.
Holm correction is applied across the E1 family (models x phases); all other contrasts are descriptive and unadjusted.

Writes results/lumiere_v4_stats.{md,json}.
"""

from __future__ import annotations

import glob
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from tools.lumiere_gating_stats import latest, mcnemar_exact, wilson

MODELS = ["MedGemma-4B", "Gemma-3-12B", "Gemma-3-27B", "Llama-4-Scout"]
MARGIN = 10.0            # percentage points; fixed in paper/preregistration_v4.md before any v4 model run
N_BOOT = 10_000
SEED = 20260925
IMG_PHASES = ["AIA", "LIL", "DSCR"]
TCM_CLASSES = ["continue", "confirm", "escalate"]


# ------------------------------------------------------------------ loading

def load_records(model: str, results_dir: Path = Path("results")) -> dict[tuple, dict]:
    """(case, phase, condition) -> record, merged over all finished v4 job folders of the model (oldest first)."""
    merged: dict[tuple, dict] = {}
    for d in sorted(glob.glob(str(results_dir / f"lumiere_v4_{model}_*"))):
        p = Path(d) / "raw_results.json"
        if not p.exists():
            continue
        for r in json.loads(p.read_text()):
            merged[(r["case_id"], r["phase"], r["condition"])] = r
    return merged


def item_flags() -> dict[str, dict]:
    """Per patient: DSCR expert agreement and TCM rule class, from the v4 facts and drafts."""
    out = {}
    for f in sorted(Path("data/lumiere/v4/reviewed").glob("Patient-*.json")):
        items = {it["id"].split("_")[-1]: it for it in json.loads(f.read_text())}
        out[f.stem] = {"expert_agrees": bool(items["DSCR"]["facts_used"]["concordant"]),
                       "tcm_class": items["TCM"]["tcm_rule"]["class"], "tcm_rano": items["TCM"]["tcm_rule"]["rano"]}
    return out


def _acc(rs: list[dict | None]) -> np.ndarray:
    return np.array([1.0 if (r and r.get("correct")) else 0.0 for r in rs])


def boot_ci(x: np.ndarray, rng) -> tuple[float, float]:
    if len(x) == 0:
        return (float("nan"), float("nan"))
    idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
    m = x[idx].mean(axis=1)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def paired(a: np.ndarray, b: np.ndarray, rng) -> dict:
    """Paired difference a - b in percentage points with a patient-bootstrap CI and exact McNemar p."""
    d = a - b
    lo, hi = boot_ci(d, rng)
    bb, cc = int(((a == 1) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    return {"n": int(len(a)), "acc_a": float(a.mean() * 100), "acc_b": float(b.mean() * 100), "diff": float(d.mean() * 100),
            "ci": [lo * 100, hi * 100], "only_a": bb, "only_b": cc, "p": mcnemar_exact(bb, cc)}


def verdict(ci: list[float]) -> str:
    if ci[0] > 0:
        return "image helps"
    if ci[0] > -MARGIN and ci[1] < MARGIN:
        return f"within +/-{MARGIN:.0f}pp"
    return "inconclusive"


def holm(ps: list[float]) -> list[float]:
    order = np.argsort(ps)
    m = len(ps)
    adj = np.zeros(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj.tolist()


# ------------------------------------------------------------------ analyses

def e1(recs, flags, rng) -> dict:
    out = {}
    for ph in IMG_PHASES:
        cases = sorted({c for (c, p, k) in recs if p == ph and k == "own"} & {c for (c, p, k) in recs if p == ph and k == "text"})
        if not cases:
            continue
        own, txt = _acc([recs[(c, ph, "own")] for c in cases]), _acc([recs[(c, ph, "text")] for c in cases])
        res = paired(own, txt, rng)
        res["verdict"] = verdict(res["ci"])
        res["parse_errors_own"] = sum(bool(recs[(c, ph, "own")]["parse_error"]) for c in cases)
        res["parse_errors_text"] = sum(bool(recs[(c, ph, "text")]["parse_error"]) for c in cases)
        if ph == "DSCR":       # sensitivity: items whose category also equals the expert RANO rating
            keep = np.array([flags[c]["expert_agrees"] for c in cases])
            if keep.sum() >= 5:
                sub = paired(own[keep], txt[keep], rng)
                res["expert_agreeing_subset"] = {k: sub[k] for k in ("n", "acc_a", "acc_b", "diff", "ci", "p")}
        out[ph] = res
    return out


def e2(recs, rng) -> dict:
    out = {}
    for ph in IMG_PHASES:
        cases = sorted(c for (c, p, k) in recs if p == ph and k == "swap")
        cases = [c for c in cases if (c, ph, "text") in recs and (c, ph, "own") in recs]
        if not cases:
            continue
        swap = [recs[(c, ph, "swap")] for c in cases]
        text = [recs[(c, ph, "text")] for c in cases]
        own = [recs[(c, ph, "own")] for c in cases]
        donor_key = [s["donor_key_letter"] for s in swap]
        sw_hit = np.array([1.0 if s["model_answer"] and s["model_answer"] == dk else 0.0 for s, dk in zip(swap, donor_key)])
        tx_hit = np.array([1.0 if t["model_answer"] and t["model_answer"] == dk else 0.0 for t, dk in zip(text, donor_key)])
        own_ok = _acc(own)
        g = sw_hit - tx_hit
        lo, hi = boot_ci(g, rng)
        keep_own = np.array([1.0 if s["model_answer"] and s["model_answer"] == s["correct_answer"] else 0.0 for s in swap])
        out[ph] = {"n": len(cases), "own_image_correct": float(own_ok.mean() * 100),
                   "swap_answers_donor_key": float(sw_hit.mean() * 100), "text_answers_donor_key": float(tx_hit.mean() * 100),
                   "gain": float(g.mean() * 100), "gain_ci": [lo * 100, hi * 100],
                   "swap_keeps_own_key": float(keep_own.mean() * 100),
                   "swap_flips_answer_vs_own": float(np.mean([s["model_answer"] != o["model_answer"] for s, o in zip(swap, own)]) * 100)}
    return out


def e3(recs, flags, rng) -> dict:
    out: dict = {}
    for cond in ("ctx_gold", "ctx_wrong", "ctx_absent"):
        cases = sorted(c for (c, p, k) in recs if p == "TCM" and k == cond)
        if not cases:
            continue
        by_class = {cls: [c for c in cases if flags[c]["tcm_class"] == cls] for cls in TCM_CLASSES}
        cell = {"n": len(cases), "acc": float(_acc([recs[(c, "TCM", cond)] for c in cases]).mean() * 100)}
        for cls, cs in by_class.items():
            if cs:
                a = _acc([recs[(c, "TCM", cond)] for c in cs])
                cell[f"acc_{cls}"] = {"n": len(cs), "acc": float(a.mean() * 100), "wilson": [x * 100 for x in wilson(int(a.sum()), len(cs))]}
        # does the answer match the rule applied to the label the context STATED (right or wrong)?
        st = [recs[(c, "TCM", cond)] for c in cases if "follows_stated_label" in recs[(c, "TCM", cond)]]
        if st:
            cell["follows_stated_label"] = {"n": len(st), "share": float(np.mean([r["follows_stated_label"] for r in st]) * 100)}
        out[cond] = cell
    for cond in ("flip_label", "flip_window"):
        cases = sorted(c for (c, p, k) in recs if p == "TCM" and k == cond)
        if not cases:
            continue
        f = np.array([1.0 if recs[(c, "TCM", cond)].get("follows_flip") else 0.0 for c in cases])
        lo, hi = boot_ci(f, rng)
        cell = {"n": len(cases), "follows_rule_after_flip": float(f.mean() * 100), "ci": [lo * 100, hi * 100]}
        pd_cases = [c for c in cases if flags[c]["tcm_rano"] == "progressive disease"]
        if pd_cases and cond == "flip_window":
            fp = np.array([1.0 if recs[(c, "TCM", cond)].get("follows_flip") else 0.0 for c in pd_cases])
            lo, hi = boot_ci(fp, rng)
            cell["progressive_disease_items"] = {"n": len(pd_cases), "follows": float(fp.mean() * 100), "ci": [lo * 100, hi * 100]}
        # was the original (unflipped) answer already correct? flips only mean something if the model was right before
        gold_ok = [c for c in cases if (c, "TCM", "ctx_gold") in recs and recs[(c, "TCM", "ctx_gold")]["correct"]]
        if gold_ok:
            cell["follows_given_gold_correct"] = {"n": len(gold_ok),
                                                  "share": float(np.mean([1.0 if recs[(c, "TCM", cond)].get("follows_flip") else 0.0 for c in gold_ok]) * 100)}
        out[cond] = cell
    return out


def e4(recs, rng) -> dict:
    out = {}
    for ph in ("LIL", "DSCR", "PJRF", "TCM"):
        cell = {}
        arms = {"gold": "ctx_gold", "wrong": "ctx_wrong", "absent": "ctx_absent" if ph in ("PJRF", "TCM") else "own"}
        cases = sorted({c for (c, p, k) in recs if p == ph and k == "ctx_gold"})
        if ph == "PJRF":
            continue      # PJRF is scored by Brier, in e5
        for a, b in (("gold", "wrong"), ("gold", "absent"), ("absent", "wrong")):
            cs = [c for c in cases if all((c, ph, arms[x]) in recs for x in (a, b))]
            if cs:
                r = paired(_acc([recs[(c, ph, arms[a])] for c in cs]), _acc([recs[(c, ph, arms[b])] for c in cs]), rng)
                cell[f"{a}_minus_{b}"] = {k: r[k] for k in ("n", "acc_a", "acc_b", "diff", "ci", "p")}
        if cell:
            out[ph] = cell
    return out


def _auc(p: np.ndarray, y: np.ndarray) -> float:
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float((np.sum(pos[:, None] > neg[None, :]) + 0.5 * np.sum(pos[:, None] == neg[None, :])) / (len(pos) * len(neg)))


def e5(recs, rng) -> dict:
    out = {}
    for cond in ("ctx_gold", "ctx_wrong", "ctx_absent"):
        rs = [r for (c, p, k), r in sorted(recs.items()) if p == "PJRF" and k == cond]
        if not rs:
            continue
        y = np.array([r["forecast_outcome"] for r in rs], float)
        ok = np.array([r["forecast_prob"] is not None for r in rs])
        p = np.array([r["forecast_prob"] if r["forecast_prob"] is not None else np.nan for r in rs])
        # a parse failure is forecast as the uninformative 0.5 (documented; mirrors "scored incorrect")
        p_f = np.where(ok, p, 0.5)
        loo = np.array([np.delete(y, i).mean() for i in range(len(y))])
        d = (p_f - y) ** 2 - (loo - y) ** 2          # per-patient squared-error difference vs the base rate
        lo, hi = boot_ci(d, rng)
        out[cond] = {"n": len(rs), "parse_failures": int((~ok).sum()), "brier": float(((p_f - y) ** 2).mean()),
                     "brier_base_rate_loo": float(((loo - y) ** 2).mean()), "brier_minus_base": float(d.mean()),
                     "brier_minus_base_ci": [lo, hi], "skill": float(1 - ((p_f - y) ** 2).mean() / ((loo - y) ** 2).mean()),
                     "auc": _auc(p_f, y), "mean_forecast": float(p_f.mean()), "answer_counts": dict(Counter(r["model_answer"] for r in rs))}
    return out


def e6(model: str, rng) -> dict:
    """Secondary: total effect of removing images through the chain, from the ordinary chain runs."""
    def per_q(pattern):
        d = latest(pattern, "raw_results.json")
        if d is None:
            return None
        rows = json.loads((d / "raw_results.json").read_text())
        return {(c["case_id"], ph): [q["correct"] for q in v["questions"]] for c in rows for ph, v in c["phases"].items() if v.get("questions")}
    own = per_q(f"results/lumiere_{model}_v4_nogate_*")
    txt = per_q(f"results/lumiere_{model}_textonly_v4_nogate_*")
    if not own or not txt:
        return {}
    out = {}
    for ph in ["AIA", "LIL", "DSCR", "TCM"]:
        keys = sorted(k for k in own if k[1] == ph and k in txt)
        if keys:
            r = paired(np.array([float(own[k][0]) for k in keys]), np.array([float(txt[k][0]) for k in keys]), rng)
            out[ph] = {k: r[k] for k in ("n", "acc_a", "acc_b", "diff", "ci", "p")}
    return out


# ------------------------------------------------------------------ report

def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    models = ap.parse_args().models.split(",")
    rng = np.random.default_rng(SEED)
    flags = item_flags()
    res: dict = {"margin_pp": MARGIN, "models": {}}
    md = ["# LUMIERE v4 results", "", f"Generated by `tools/lumiere_v4_stats.py`; seed {SEED}, {N_BOOT:,} bootstrap resamples; margin +/-{MARGIN:.0f}pp "
          "fixed in `paper/preregistration_v4.md`. Bootstrap CIs resample patients; p-values are exact McNemar. Items are not clinician-validated.", ""]
    e1_rows = []
    for m in models:
        recs = load_records(m)
        if not recs:
            md.append(f"*{m}: no finished v4 results yet.*")
            continue
        r = {"n_records": len(recs), "E1": e1(recs, flags, rng), "E2": e2(recs, rng), "E3": e3(recs, flags, rng),
             "E4": e4(recs, rng), "E5": e5(recs, rng), "E6": e6(m, rng)}
        res["models"][m] = r
        for ph, v in r["E1"].items():
            e1_rows.append((m, ph, v))
    adj = holm([v["p"] for _, _, v in e1_rows]) if e1_rows else []
    for (m, ph, v), a in zip(e1_rows, adj):
        v["p_holm"] = a
    md += ["## E1. Image effect (own image minus text only; no upstream context)", "",
           "| Model | Phase | n | own | text-only | diff [95% CI] | only-own / only-text | p (Holm) | verdict |", "|---|---|---|---|---|---|---|---|---|"]
    for m, ph, v in e1_rows:
        md.append(f"| {m} | {ph} | {v['n']} | {v['acc_a']:.1f} | {v['acc_b']:.1f} | {v['diff']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | "
                  f"{v['only_a']}/{v['only_b']} | {v['p']:.3f} ({v['p_holm']:.3f}) | {v['verdict']} |")
    md += ["", "AIA is the positive control: its answer is visible only in the image, so a model with no AIA gain has not shown that this "
           "test can detect image use, and its LIL and DSCR rows say nothing about image use.", ""]
    md += ["## E2. Donor tracking (image swapped for a donor whose key differs; no upstream context)", "",
           "| Model | Phase | n | own-image correct | swap answers donor key | text answers donor key | gain [95% CI] | swap keeps own key | answer changes vs own |", "|---|---|---|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        for ph, v in r["E2"].items():
            md.append(f"| {m} | {ph} | {v['n']} | {v['own_image_correct']:.1f} | {v['swap_answers_donor_key']:.1f} | {v['text_answers_donor_key']:.1f} | "
                      f"{v['gain']:+.1f} [{v['gain_ci'][0]:+.1f}, {v['gain_ci'][1]:+.1f}] | {v['swap_keeps_own_key']:.1f} | {v['swap_flips_answer_vs_own']:.1f} |")
    md += ["", "## E3. TCM: use of the stated facts", "",
           "| Model | gold ctx acc (continue / confirm / escalate) | wrong ctx acc | absent ctx acc | follows rule after label flip | follows rule after timing flip (PD items) |", "|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        e = r["E3"]
        g = e.get("ctx_gold", {})
        cls = " / ".join(f"{g[f'acc_{c}']['acc']:.0f} (n={g[f'acc_{c}']['n']})" if f"acc_{c}" in g else "-" for c in TCM_CLASSES)
        fl, fw = e.get("flip_label", {}), e.get("flip_window", {})
        pdw = fw.get("progressive_disease_items")
        md.append(f"| {m} | {g.get('acc', float('nan')):.1f}: {cls} | {e.get('ctx_wrong', {}).get('acc', float('nan')):.1f} | "
                  f"{e.get('ctx_absent', {}).get('acc', float('nan')):.1f} | "
                  f"{fl.get('follows_rule_after_flip', float('nan')):.1f} | "
                  f"{(str(round(pdw['follows'], 1)) + ' (n=' + str(pdw['n']) + ')') if pdw else '-'} |")
    md += ["", "## E4. Upstream-context effects (paired accuracy differences, pp)", "", "| Model | Phase | contrast | n | diff [95% CI] | p |", "|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        for ph, cell in r["E4"].items():
            for name, v in cell.items():
                md.append(f"| {m} | {ph} | {name} | {v['n']} | {v['diff']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['p']:.3f} |")
    md += ["", "## E5. PJRF one-year-mortality forecast", "", "| Model | context | n | parse fail | Brier | base-rate Brier | skill | AUC | mean forecast |", "|---|---|---|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        for cond, v in r["E5"].items():
            md.append(f"| {m} | {cond} | {v['n']} | {v['parse_failures']} | {v['brier']:.3f} | {v['brier_base_rate_loo']:.3f} | {v['skill']:+.3f} | {v['auc']:.3f} | {v['mean_forecast']:.2f} |")
    md += ["", "## E6. Chain total effect (secondary; ordinary chain runs, own answers as context)", "", "| Model | Phase | n | image | text-only | diff [95% CI] | p |", "|---|---|---|---|---|---|---|"]
    for m, r in res["models"].items():
        for ph, v in r["E6"].items():
            md.append(f"| {m} | {ph} | {v['n']} | {v['acc_a']:.1f} | {v['acc_b']:.1f} | {v['diff']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['p']:.3f} |")
    text = "\n".join(md)
    Path("results/lumiere_v4_stats.md").write_text(text)
    Path("results/lumiere_v4_stats.json").write_text(json.dumps(res, indent=2, default=float))
    print(text)


if __name__ == "__main__":
    main()
