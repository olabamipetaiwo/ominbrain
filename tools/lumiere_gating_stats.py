"""
Compile the two 2026-09-23 control experiments (repeated-run control, gating-causality).

Read-only on results/; CPU-only, safe on a login node. Models whose runs have not finished yet are
skipped with a note, so this can be re-run as the queued jobs complete.

  1. repeat   Repeated identical-input control (`lumirep_*`, `--run-tag rep2`): the same v3 own-image,
              non-gated run done twice. Reports accuracy in both runs, the share of items with an
              identical answer / identical correctness, and per-phase answer flips. A nonzero flip
              rate is the run-to-run noise floor that the counterfactual flip rates must be read against.
  2. gating   Gating-causality (`lumigc_*`): each of LIL/DSCR/PJRF/TCM asked with correct, forced-wrong or
              absent upstream context. Paired contrasts per model x phase (correct-incorrect,
              correct-absent, absent-incorrect): accuracy difference with a patient-clustered
              bootstrap CI, discordant counts (b, c), exact two-sided McNemar p, and the share of
              items whose ANSWER changed. Item-level `correct` flag (salvaged answers count, as in
              lumiere_reviewer_stats.py); parse-error counts are reported per condition.
              p-values are uncorrected (20+ cells per contrast); read them as descriptive.

  3. ablation TCM-leakage check (`lumigcabl_*`): TCM with ONLY the DSCR entry (incl-DSCR) or with every
              upstream phase EXCEPT DSCR (excl-DSCR) injected, correct/incorrect conditions. Compared with the
              full-context and absent conditions of the primary run on the same patients.

  4. options LLM options-only baseline (`lumiopt_*`): the model sees only the four options (no image, no stem,
              no chain). Per phase: options-only accuracy, the no-chain-context baseline (gating-causality's
              'absent' condition for LIL-TCM; the own-image run for AIA, which has no upstream phase), own-image
              accuracy, and the paired own-image - options-only difference with a patient-bootstrap CI and
              exact McNemar p. Non-LLM reference rows (chance, majority answer text) come from the v3 items.

Usage
-----
python -m tools.lumiere_gating_stats      # prints, writes results/lumiere_gating_stats.{json,md}
"""

import glob
import json
from math import comb
from pathlib import Path

import numpy as np

MODELS = ["MedGemma-4B", "Gemma-3-12B", "Gemma-3-27B", "Llama-4-Scout"]
PHASES = ["AIA", "LIL", "DSCR", "PJRF", "TCM"]
GC_PHASES = ["LIL", "DSCR", "PJRF", "TCM"]
CONDITIONS = ["correct", "incorrect", "absent"]
CONTRASTS = [("correct", "incorrect"), ("correct", "absent"), ("absent", "incorrect")]
N_BOOT = 10_000
SEED = 20260923


def latest(pattern: str, need: str = "raw_results.json") -> Path | None:
    """Newest matching run dir that actually contains `need` (skips still-running jobs)."""
    runs = [Path(p) for p in sorted(glob.glob(pattern)) if (Path(p) / need).exists()]
    return runs[-1] if runs else None


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar (binomial on the discordant pairs)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def pct(x: float) -> str:
    return "n/a" if x is None or np.isnan(x) else f"{100 * x:.1f}"


# ---------------------------------------------------------------- 1. repeat
def item_table(cases: list[dict]) -> dict[str, dict]:
    return {q["id"]: dict(q, phase=ph) for c in cases for ph, p in c["phases"].items() for q in p["questions"]}


def repeat_section() -> tuple[dict, list[str]]:
    out, notes = {}, []
    lines = ["## 1. Repeated identical-input control (v3, own-image, non-gated)", "",
             "Run 1 = the primary v3 run, run 2 = `rep2` re-run with the same flags. Items are matched by question id.", "",
             "| Model | n | Acc run 1 | Acc run 2 | Identical answer | Same correctness | Parse errors r1/r2 |",
             "|---|---|---|---|---|---|---|"]
    per_phase = ["", "### Per-phase answer flips between runs (correct r1 / correct r2 / flipped answers, of n)", "",
                 "| Model | " + " | ".join(PHASES) + " |", "|---|" + "---|" * len(PHASES)]
    for m in MODELS:
        r1 = latest(f"results/lumiere_{m}_v3_nogate_2*")
        r2 = latest(f"results/lumiere_{m}_rep2_v3_nogate_*")
        if not (r1 and r2):
            notes.append(f"- {m}: repeated run not available yet (run 1: {bool(r1)}, run 2: {bool(r2)})")
            continue
        a = item_table(json.loads((r1 / "raw_results.json").read_text()))
        b = item_table(json.loads((r2 / "raw_results.json").read_text()))
        ids = [i for i in a if i in b]
        n = len(ids)
        if n != len(a) or n != len(b):
            notes.append(f"- {m}: only {n} of {len(a)}/{len(b)} items matched between runs")
        ca = sum(bool(a[i]["correct"]) for i in ids)
        cb = sum(bool(b[i]["correct"]) for i in ids)
        same_ans = sum(a[i]["model_answer"] == b[i]["model_answer"] for i in ids)
        same_cor = sum(bool(a[i]["correct"]) == bool(b[i]["correct"]) for i in ids)
        pe1 = sum(bool(a[i].get("parse_error")) for i in ids)
        pe2 = sum(bool(b[i].get("parse_error")) for i in ids)
        lo1, hi1 = wilson(ca, n)
        lo2, hi2 = wilson(cb, n)
        lines.append(f"| {m} | {n} | {pct(ca / n)} [{pct(lo1)}–{pct(hi1)}] | {pct(cb / n)} [{pct(lo2)}–{pct(hi2)}] | "
                     f"{same_ans}/{n} ({pct(same_ans / n)}%) | {same_cor}/{n} ({pct(same_cor / n)}%) | {pe1}/{pe2} |")
        cells, ph_json = [], {}
        for ph in PHASES:
            s = [i for i in ids if a[i]["phase"] == ph]
            k1 = sum(bool(a[i]["correct"]) for i in s)
            k2 = sum(bool(b[i]["correct"]) for i in s)
            fl = sum(a[i]["model_answer"] != b[i]["model_answer"] for i in s)
            cells.append(f"{k1} / {k2} / {fl} of {len(s)}")
            ph_json[ph] = {"n": len(s), "correct_r1": k1, "correct_r2": k2, "answer_flips": fl}
        per_phase.append(f"| {m} | " + " | ".join(cells) + " |")
        out[m] = {"n": n, "acc_r1": ca / n, "acc_r2": cb / n, "identical_answer": same_ans, "same_correctness": same_cor,
                  "parse_errors": [pe1, pe2], "run1": str(r1), "run2": str(r2), "per_phase": ph_json}
    return out, lines + per_phase + ([""] + notes if notes else [])


# ---------------------------------------------------------------- 2. gating
def gating_section(rng) -> tuple[dict, list[str]]:
    out, notes = {}, []
    lines = ["## 2. Gating-causality: upstream context correct / forced-wrong / absent", "",
             "n = one item per patient per phase. Accuracy uses the item-level `correct` flag. "
             "Wilson 95% CIs on the marginal accuracies; contrasts are PAIRED on the same patient's item.", ""]
    marg = ["### Accuracy by condition (%) [Wilson 95% CI]", "",
            "| Model | Phase | n | correct ctx | incorrect ctx | absent ctx | parse errors c/i/a |", "|---|---|---|---|---|---|---|"]
    contr = ["", "### Paired contrasts (percentage points) [patient-clustered 95% bootstrap CI]", "",
             f"b = right only under the first condition, c = right only under the second. McNemar p is exact, two-sided, "
             f"UNCORRECTED for multiplicity. 'answer changed' = share of items whose chosen letter differs between the two conditions. "
             f"{N_BOOT:,} resamples, seed {SEED}.", "",
             "| Model | Phase | Contrast | Δ [95% CI] | b / c | McNemar p | answer changed |", "|---|---|---|---|---|---|---|"]
    for m in MODELS:
        d = latest(f"results/lumiere_gatingcausality_{m}_*", need="summary.json")
        if d is None or not (d / "raw_results.json").exists():
            notes.append(f"- {m}: gating-causality run not finished yet")
            continue
        cases = json.loads((d / "raw_results.json").read_text())
        out[m] = {"run": str(d), "n_patients": len(cases), "phases": {}}
        for ph in GC_PHASES:
            rows = [c["phases"][ph] for c in cases if ph in c["phases"] and all(k in c["phases"][ph] for k in CONDITIONS)]
            n = len(rows)
            if n == 0:
                continue
            ok = {k: np.array([bool(r[k]["correct"]) for r in rows], dtype=float) for k in CONDITIONS}
            ans = {k: np.array([r[k]["model_answer"] for r in rows]) for k in CONDITIONS}
            pe = {k: int(sum(bool(r[k].get("parse_error")) for r in rows)) for k in CONDITIONS}
            cells = []
            for k in CONDITIONS:
                lo, hi = wilson(int(ok[k].sum()), n)
                cells.append(f"{pct(ok[k].mean())} [{pct(lo)}–{pct(hi)}]")
            marg.append(f"| {m} | {ph} | {n} | " + " | ".join(cells) + f" | {pe['correct']}/{pe['incorrect']}/{pe['absent']} |")
            ph_json = {"n": n, "acc": {k: float(ok[k].mean()) for k in CONDITIONS}, "parse_errors": pe, "contrasts": {}}
            for x, y in CONTRASTS:
                diff = ok[x] - ok[y]
                idx = rng.integers(0, n, (N_BOOT, n))
                boots = diff[idx].mean(axis=1)
                lo, hi = np.percentile(boots, [2.5, 97.5])
                b = int(np.sum((ok[x] == 1) & (ok[y] == 0)))
                c = int(np.sum((ok[x] == 0) & (ok[y] == 1)))
                p = mcnemar_exact(b, c)
                chg = float(np.mean(ans[x] != ans[y]))
                contr.append(f"| {m} | {ph} | {x} − {y} | {100 * diff.mean():+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] | "
                             f"{b} / {c} | {p:.3f} | {pct(chg)}% |")
                ph_json["contrasts"][f"{x}-{y}"] = {"diff": float(diff.mean()), "ci": [float(lo), float(hi)], "b": b, "c": c,
                                                    "mcnemar_p": p, "answer_changed": chg}
            out[m]["phases"][ph] = ph_json
    return out, lines + marg + contr + ([""] + notes if notes else [])


# ---------------------------------------------------------------- 3. ablation
ABLATIONS = [("incl-DSCR", "DSCR entry only"), ("excl-DSCR", "AIA + LIL + PJRF (no DSCR)")]


def _paired(x: np.ndarray, y: np.ndarray, rng) -> dict:
    n = len(x)
    diff = x - y
    lo, hi = np.percentile(diff[rng.integers(0, n, (N_BOOT, n))].mean(axis=1), [2.5, 97.5])
    b, c = int(np.sum((x == 1) & (y == 0))), int(np.sum((x == 0) & (y == 1)))
    return {"diff": float(diff.mean()), "ci": [float(lo), float(hi)], "b": b, "c": c, "mcnemar_p": mcnemar_exact(b, c)}


def ablation_section(rng) -> tuple[dict, list[str]]:
    out, notes = {}, []
    lines = ["## 3. TCM context ablation (which upstream entries carry the effect?)", "",
             "Accuracy on TCM, same 52 patients. 'full' and 'absent' come from the primary gating-causality run; "
             "the two ablations inject only the listed upstream entries. Δ rows are paired, patient-clustered "
             f"bootstrap CIs ({N_BOOT:,} resamples); p is exact McNemar, uncorrected.", "",
             "| Model | Context | correct ctx | incorrect ctx | Δ correct − incorrect [95% CI] (b/c, p) | Δ correct − absent [95% CI] (b/c, p) |",
             "|---|---|---|---|---|---|"]
    for m in MODELS:
        prim = latest(f"results/lumiere_gatingcausality_{m}_*", need="summary.json")
        if prim is None:
            continue
        pc = {c["case_id"]: c["phases"].get("TCM") for c in json.loads((prim / "raw_results.json").read_text())}
        found = False
        rows = {}
        for tag, desc in [("full", "all upstream (primary run)")] + ABLATIONS:
            if tag == "full":
                src = pc
            else:
                d = latest(f"results/lumiere_gcablate_{m}_{tag}_*", need="summary.json")
                if d is None:
                    notes.append(f"- {m} {tag}: ablation run not finished yet")
                    continue
                found = True
                src = {c["case_id"]: c["phases"].get("TCM") for c in json.loads((d / "raw_results.json").read_text())}
            ids = sorted(i for i in src if src[i] and pc.get(i))
            ok = lambda cond, S: np.array([float(bool(S[i][cond]["correct"])) for i in ids])
            cor, inc = ok("correct", src), ok("incorrect", src)
            ab = ok("absent", pc)
            rows[tag] = (desc, cor, inc, ab, len(ids))
        if not found:
            continue
        out[m] = {}
        for tag, (desc, cor, inc, ab, n) in rows.items():
            ci_, cc_ = _paired(cor, inc, rng), _paired(cor, ab, rng)
            fmt = lambda r: f"{100 * r['diff']:+.1f} [{100 * r['ci'][0]:+.1f}, {100 * r['ci'][1]:+.1f}] ({r['b']}/{r['c']}, p={r['mcnemar_p']:.3f})"
            lines.append(f"| {m} | {desc} | {pct(cor.mean())} | {pct(inc.mean())} | {fmt(ci_)} | {fmt(cc_)} |")
            out[m][tag] = {"n": n, "acc_correct": float(cor.mean()), "acc_incorrect": float(inc.mean()),
                           "acc_absent_primary": float(ab.mean()), "correct-incorrect": ci_, "correct-absent": cc_}
    return out, lines + ([""] + notes if notes else [])


# ---------------------------------------------------------------- 4. options-only
def options_section(rng) -> tuple[dict, list[str]]:
    from collections import Counter

    from src.lumiere_loader import load_lumiere
    from tools.lumiere_reviewer_stats import item_table as rs_item_table, load_run

    out, notes = {}, []
    cases = load_lumiere(include_unreviewed=True, item_set="v3")
    ref = {}
    for ph in PHASES:
        qs = [c["phases"][ph][0] for c in cases if c["phases"].get(ph)]
        ref[ph] = {"n": len(qs), "chance": float(np.mean([1 / len(q["options"]) for q in qs])),
                   "text_majority": Counter(q["correct_answer_text"] for q in qs).most_common(1)[0][1] / len(qs)}
    lines = ["## 4. LLM options-only baseline (no image, no question stem, no chain context)", "",
             "Reference rows are non-LLM: chance = mean 1/#options; majority = share of the most common correct answer TEXT. "
             "'no-chain ctx' = gating-causality's absent condition (LIL-TCM), own-image run for AIA. Δ = own-image − options-only, "
             f"paired, patient-clustered bootstrap ({N_BOOT:,} resamples); p exact McNemar, uncorrected.", "",
             "| Phase | n | chance | majority text |", "|---|---|---|---|"]
    for ph in PHASES:
        lines.append(f"| {ph} | {ref[ph]['n']} | {pct(ref[ph]['chance'])} | {pct(ref[ph]['text_majority'])} |")
    lines += ["", "| Model | Phase | options-only [Wilson 95%] | no-chain ctx | own-image | Δ own − options-only [95% CI] (b/c, p) | parse errors (options-only) |",
              "|---|---|---|---|---|---|---|"]
    for m in MODELS:
        d = latest(f"results/lumiere_optionsonly_{m}_*", need="summary.json")
        if d is None:
            notes.append(f"- {m}: options-only run not finished yet")
            continue
        oo = json.loads((d / "raw_results.json").read_text())
        own = rs_item_table(load_run("img", m))
        prim = latest(f"results/lumiere_gatingcausality_{m}_*", need="summary.json")
        absent = {}
        if prim:
            for c in json.loads((prim / "raw_results.json").read_text()):
                for ph, v in c["phases"].items():
                    absent[(c["case_id"], ph)] = bool(v["absent"]["correct"])
        out[m] = {"run": str(d), "phases": {}}
        for ph in PHASES:
            rows = [(c["case_id"], c["phases"][ph]) for c in oo if ph in c["phases"]]
            ids = [i for i, _ in rows if (i, ph) in own]
            x = np.array([float(bool(v["correct"])) for i, v in rows if (i, ph) in own])   # options-only
            y = np.array([float(bool(own[(i, ph)]["correct"])) for i in ids])              # own-image
            n = len(ids)
            pe = int(sum(bool(v.get("parse_error")) for _, v in rows))
            lo, hi = wilson(int(x.sum()), n)
            nc = y if ph == "AIA" else np.array([float(absent[(i, ph)]) for i in ids]) if all((i, ph) in absent for i in ids) else None
            r = _paired(y, x, rng)
            fmt = lambda r: f"{100 * r['diff']:+.1f} [{100 * r['ci'][0]:+.1f}, {100 * r['ci'][1]:+.1f}] ({r['b']}/{r['c']}, p={r['mcnemar_p']:.3f})"
            lines.append(f"| {m} | {ph} | {pct(x.mean())} [{pct(lo)}–{pct(hi)}] | {pct(nc.mean()) if nc is not None else 'n/a'} | "
                         f"{pct(y.mean())} | {fmt(r)} | {pe} |")
            out[m]["phases"][ph] = {"n": n, "acc_options_only": float(x.mean()), "acc_own_image": float(y.mean()),
                                    "acc_no_chain": None if nc is None else float(nc.mean()), "own-options": r, "parse_errors": pe}
    return out, lines + ([""] + notes if notes else [])


def main():
    rng = np.random.default_rng(SEED)
    res, md = {}, ["# LUMIERE control experiments: repeated-run, gating-causality, TCM ablation and options-only (v3)", "",
                   "Generated by `tools/lumiere_gating_stats.py`.", ""]
    for name, fn in (("repeat", repeat_section), ("gating", lambda: gating_section(rng)),
                     ("ablation", lambda: ablation_section(rng)), ("options", lambda: options_section(rng))):
        r, lines = fn()
        res[name] = r
        md += lines + [""]
    text = "\n".join(md)
    print(text)
    Path("results/lumiere_gating_stats.md").write_text(text)
    Path("results/lumiere_gating_stats.json").write_text(json.dumps(res, indent=2, default=float))
    print("Saved -> results/lumiere_gating_stats.{md,json}")


if __name__ == "__main__":
    main()
