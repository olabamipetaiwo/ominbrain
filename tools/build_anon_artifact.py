"""
Assemble the anonymous reproducibility artifact (T-15): everything a reviewer needs to regenerate the intervention-study
tables from the model responses, with no cluster paths, account names or author information.

  python -m tools.build_anon_artifact --out release/anon_artifact         # copy, manifest, checksums, scrub check (CPU, light)
  python -m tools.export_release_prompts --out release/anon_artifact/prompts.jsonl   # run from inside the artifact (see README)

Contents of the artifact
  code/data/results   same layout as the repository, so `python -m tools.*` runs unchanged from the artifact root
  run_manifest.json   which job folder supplied every record; which later records replaced earlier ones (the loader keeps
                      the LAST record per (case, phase, condition) over job folders sorted by timestamp; the DSCR rerun relied on this)
  overrides.jsonl     one line per replaced record, with whether the answer letter changed
  analysis_versions.json  interpreter and package versions, seeds, margin, first admitted job stamp, hashes of the analysis scripts
  expected/           the statistics and generated tables as shipped with the paper; reproduce.sh diffs a fresh run against them
  SHA256SUMS          checksum of every file
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from tools import lumiere_v4_stats as st

ROOT = Path(".")
CODE_DIRS = ["src", "config", "tests"]
TOOLS = ["lumiere_v4_stats", "lumiere_v4_supplement", "lumiere_v4_baselines", "lumiere_v4_input_check", "paper_numbers",
         "paper_v4_example", "lumiere_gating_stats", "export_release_prompts", "compute_budget",
         "lumiere_v4_donor_validation", "lumiere_v4_robustness", "lumiere_v4_perm_validation", "lumiere_v4_altpairs",
         "lumiere_v4_classwise", "lumiere_v4_strat_perm"]
DATA_DIRS = ["data/lumiere/v4/reviewed", "data/lumiere/v4/facts", "data/lumiere/v4/measurements", "data/lumiere/v4/slices",
             "data/lumiere/v4/alt_pairs"]   # the released alternative donor-assignment identities (round-3 reviewer Q1)
DATA_FILES = ["data/lumiere/v4/selection_report.json", "data/lumiere/v4/counterfactual_pairs.json",
              "data/lumiere/tabular/LUMIERE-Demographics_Pathology.csv", "data/lumiere/tabular/LUMIERE-datacompleteness.csv",
              "data/lumiere/tabular/LUMIERE-ExpertRating-v202211.csv"]
RESULT_FILES = ["results/compute_budget.json",
                # post-hoc analyses shipped as precomputed inputs (paper_numbers loads them to emit the donor-validation,
                # robustness and permutation-validity macros; robustness required alternative-assignment model runs and
                # is not regenerated from scratch by reproduce.sh)
                "results/lumiere_v4_donor_validation.json", "results/lumiere_v4_perm_validation.json",
                "results/lumiere_v4_robustness_Llama-4-Scout.json", "results/lumiere_v4_robustness_Gemini-3.6-Flash.json",
                "results/lumiere_v4_classwise.json", "results/lumiere_v4_strat_perm.json"]
EXPECTED = ["results/lumiere_v4_stats.json", "results/lumiere_v4_stats.md", "results/lumiere_v4_supplement.json",
            "results/lumiere_v4_supplement.md", "results/lumiere_v4_baselines.json", "results/lumiere_v4_baselines.md"]
GENERATED = ["numbers.json", "numbers.tex", "tab_v4_e1.tex", "tab_v4_e2.tex", "tab_v4_e3.tex", "tab_v4_e3trans.tex",
             "tab_v4_e5.tex", "tab_v4_ctrl.tex", "tab_v4_handling.tex", "tab_v4_inputcheck.tex", "tab_v4_donorval.tex",
             "tab_v4_confusion.tex"]
# text that must not appear in shipped files (cluster, account, author and affiliation strings)
SCRUB = [r"ta117847", r"so589980", r"/blue/", r"/home/", r"\bucf\b", r"UCF", r"hipergator", r"HiPerGator", r"Song Wang",
         r"teeola", r"gmail", r"@\w+\.(edu|com)", r"ANTHROPIC_API_KEY=", r"sk-[A-Za-z0-9]{10,}"]
IMG_EXT = {".png", ".jpg", ".jpeg", ".gz", ".nii"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copytree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def stamp_of(d: str) -> str:
    return Path(d).name.split("_")[-2]


def ts_key(d: str) -> tuple[str, str]:
    """Run timestamp (date, time) parsed from the folder name, matching tools.lumiere_v4_stats.load_records."""
    parts = Path(d).name.split("_")
    return (parts[-2], parts[-1])


def folders_for(model: str) -> list[str]:
    return [d for d in sorted(glob.glob(f"results/lumiere_v4_{model}_*"), key=ts_key)
            if (Path(d) / "raw_results.json").exists() and stamp_of(d) >= st.MIN_STAMP]


def provenance(models: list[str]) -> tuple[dict, list[dict]]:
    """Replay tools.lumiere_v4_stats.load_records, recording which folder supplied each key and every replacement."""
    out, overrides = {}, []
    for m in models:
        supplier: dict[tuple, tuple[str, dict]] = {}
        info, replaced_by = [], Counter()
        for d in folders_for(m):
            recs = json.loads((Path(d) / "raw_results.json").read_text())
            kinds = Counter(r["condition"] for r in recs)
            for r in recs:
                key = (r["case_id"], r["phase"], r["condition"])
                if key in supplier:
                    old_d, old = supplier[key]
                    overrides.append({"model": m, "case_id": key[0], "phase": key[1], "condition": key[2], "replaced": old_d,
                                      "by": Path(d).name, "answer_changed": old.get("model_answer") != r.get("model_answer")})
                    replaced_by[old_d] += 1
                supplier[key] = (Path(d).name, r)
            info.append({"folder": Path(d).name, "stamp": stamp_of(d), "n_records": len(recs), "conditions": dict(sorted(kinds.items()))})
        used = Counter(v[0] for v in supplier.values())
        for row in info:
            row["n_used"] = used.get(row["folder"], 0)
            row["n_replaced_by_later_folder"] = replaced_by.get(row["folder"], 0)
        out[m] = {"folders_oldest_first": info, "n_keys": len(supplier), "n_replaced": int(sum(replaced_by.values()))}
    return out, overrides


def chain_provenance(models: list[str]) -> dict:
    """The chain analysis (E6 and the chain paragraph) reads only the newest folder of each arm; older folders are superseded."""
    out = {}
    for m in models:
        for arm, pat in (("image", f"results/lumiere_{m}_v4_nogate_noadapt_*"), ("text_only", f"results/lumiere_{m}_textonly_v4_nogate_noadapt_*")):
            ds = [d for d in sorted(glob.glob(pat)) if (Path(d) / "raw_results.json").exists()]
            out[f"{m}/{arm}"] = {"used": Path(ds[-1]).name if ds else None, "superseded": [Path(d).name for d in ds[:-1]]}
    return out


def used_folders(models: list[str]) -> list[str]:
    ds = set()
    for m in models:
        ds.update(folders_for(m))
    for m in st.MODELS:
        for pat in (f"results/lumiere_{m}_v4_nogate_noadapt_*", f"results/lumiere_{m}_textonly_v4_nogate_noadapt_*"):
            ds.update(d for d in glob.glob(pat) if stamp_of(d) >= st.MIN_STAMP and (Path(d) / "raw_results.json").exists())
    ds.update(d for d in glob.glob("results/lumiere_v4_inputcheck_*") if stamp_of(d) >= st.MIN_STAMP)
    return sorted(ds)


def pkg_versions() -> dict:
    out = {"python": platform.python_version()}
    for mod in ("numpy", "pandas", "scipy", "sklearn", "PIL", "matplotlib"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="release/anon_artifact")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for d in CODE_DIRS:
        copytree(ROOT / d, out / d)
    shutil.rmtree(out / "src" / "data", ignore_errors=True)      # the downloaded public benchmark (1.5 GB, gitignored), not used by the intervention study
    m = out / "config" / "models.py"      # a comment names the cluster
    m.write_text(m.read_text().replace("HiPerGator", "the compute cluster"))
    (out / "tools").mkdir()
    (out / "tools" / "__init__.py").touch()
    for t in TOOLS:
        shutil.copy(ROOT / "tools" / f"{t}.py", out / "tools" / f"{t}.py")
    for d in DATA_DIRS:
        copytree(ROOT / d, out / d)
    for f in DATA_FILES + RESULT_FILES:
        (out / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f, out / f)
    models = st.MODELS + st.CONTROLS
    prov, overrides = provenance(models)
    used = used_folders(models)
    for d in used:
        dst = out / d
        dst.mkdir(parents=True, exist_ok=True)
        for f in Path(d).iterdir():
            if f.is_file():
                shutil.copy(f, dst / f.name)
            elif f.is_dir():
                copytree(f, dst / f.name)
    (out / "expected").mkdir()
    for f in EXPECTED:
        shutil.copy(ROOT / f, out / "expected" / Path(f).name)
    (out / "expected" / "generated").mkdir()
    for f in GENERATED:
        shutil.copy(ROOT / "paper/latex/generated" / f, out / "expected" / "generated" / f)
    # the internal prespecified analysis plan and its amendment log (the 62->46 rebuild); not externally timestamped
    shutil.copy(ROOT / "paper/preregistration_v4.md", out / "analysis_plan.md")

    (out / "run_manifest.json").write_text(json.dumps({
        "loader_rule": "tools.lumiere_v4_stats.load_records: job folders of a model are merged oldest-first, sorted by the run timestamp "
                       "(the YYYYMMDD_HHMMSS at the end of the folder name); a later record with the same (case_id, phase, condition) replaces "
                       "the earlier one, so the newest run wins. Folders with a date before min_stamp ran on different items and are ignored.",
        "min_stamp": st.MIN_STAMP, "single_question_runs": prov, "chain_runs": chain_provenance(st.MODELS),
        "shipped_folders": [Path(d).name for d in used]}, indent=1))
    with (out / "overrides.jsonl").open("w") as f:
        for o in overrides:
            f.write(json.dumps(o) + "\n")
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = None
    (out / "analysis_versions.json").write_text(json.dumps({
        "source_commit": commit, "environment": pkg_versions(), "bootstrap_seed": st.SEED, "bootstrap_resamples": st.N_BOOT,
        "equivalence_margin_pp": st.MARGIN, "min_stamp": st.MIN_STAMP,
        "script_sha256": {t: sha256(out / "tools" / f"{t}.py") for t in TOOLS}}, indent=1))

    (out / "reproduce.sh").write_text("""#!/usr/bin/env bash
# Regenerate the statistics, macros and tables of the intervention study from the shipped model responses (CPU only, a few minutes).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p generated
python -m tools.lumiere_v4_stats
python -m tools.lumiere_v4_supplement
python -m tools.lumiere_v4_baselines
python -m tools.paper_numbers --v4-only --out generated
python - <<'PY'
import json, sys
from pathlib import Path
bad = 0
for name in ("lumiere_v4_stats", "lumiere_v4_supplement", "lumiere_v4_baselines"):
    a = json.loads(Path(f"results/{name}.json").read_text()); b = json.loads(Path(f"expected/{name}.json").read_text())
    ok = json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)
    print(f"{name}.json", "identical" if ok else "DIFFERS"); bad += not ok
new = json.loads(Path("generated/numbers.json").read_text()); ref = json.loads(Path("expected/generated/numbers.json").read_text())
v4 = {k: v for k, v in ref.items() if k.startswith("vfour")}
diff = [k for k, v in v4.items() if new.get(k) != v]
print(f"{len(v4)} v4 macros compared, {len(diff)} differ", diff[:10])
bad += bool(diff)
for t in sorted(Path("expected/generated").glob("tab_v4_*.tex")):
    same = (Path("generated") / t.name).exists() and (Path("generated") / t.name).read_text() == t.read_text()
    print(t.name, "identical" if same else "DIFFERS"); bad += not same
sys.exit(1 if bad else 0)
PY
""")
    (out / "reproduce.sh").chmod(0o755)
    (out / "README.md").write_text(README)

    # exact per-condition prompts (no model called; images shown as [IMAGE]) so the shipped artifact actually contains prompts.jsonl
    try:
        subprocess.run([sys.executable, "-m", "tools.export_release_prompts", "--out", str(out / "prompts.jsonl")],
                       check=True, capture_output=True, text=True)
        print(f"wrote prompts.jsonl ({sum(1 for _ in (out / 'prompts.jsonl').open())} prompts)")
    except Exception as e:
        print(f"WARNING: could not generate prompts.jsonl ({e}); remove it from the README if it is not shipped")

    # scrub check on every text file
    pat = re.compile("|".join(SCRUB))
    hits = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.suffix not in IMG_EXT:
            try:
                txt = p.read_text()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if pat.search(line):
                    hits.append(f"{p.relative_to(out)}:{i}: {line.strip()[:120]}")
    (out / "SHA256SUMS").write_text("".join(f"{sha256(p)}  {p.relative_to(out)}\n" for p in sorted(out.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"))
    print(f"artifact at {out}: {sum(1 for _ in out.rglob('*') if _.is_file())} files, {len(overrides)} replaced records, {len(hits)} scrub hits")
    for h in hits[:60]:
        print("  SCRUB", h)
    if hits:
        sys.exit(1)


README = """# Artifact: image interventions on brain-MRI questions (LUMIERE)

This artifact regenerates every number, table and macro the paper cites, from the saved model responses.
No model is ever called and no GPU is needed -- the model outputs are already here and are only re-analysed on CPU.

## 1. Quick start (about 5 minutes on a laptop)

Use a clean Python environment with just three packages. Python 3.12 or newer is required
(the analysis uses 3.12 syntax; 3.9-3.11 will not run it). You need internet access only for the `pip` step.

    python3.12 -m venv .venv
    . .venv/bin/activate
    pip install numpy==2.3.5 scipy==1.18.1 pandas==3.0.5
    bash reproduce.sh

Those are the exact versions in `analysis_versions.json`; newer compatible releases also work. These three
packages are the only dependencies on the reproduction path -- nothing else needs to be installed.

## 2. What success looks like

`reproduce.sh` recomputes the statistics from the shipped responses and diffs them against the paper's values in
`expected/`. It prints one line per artefact; a clean run looks like this and exits 0:

    lumiere_v4_stats.json identical
    lumiere_v4_supplement.json identical
    lumiere_v4_baselines.json identical
    1059 v4 macros compared, 0 differ []
    tab_v4_confusion.tex identical
    tab_v4_ctrl.tex identical
    ... (every tab_v4_*.tex) ... identical

Every line ends in `identical` and the macro line ends in `0 differ`. If any line says `DIFFERS`, or the count is
not `0 differ`, the script exits non-zero and names what changed. The freshly built files are written to `generated/`
(`numbers.json` holds the cited numbers; `tab_v4_*.tex` are the paper's tables).

## 3. What is where
| Path | Content |
|---|---|
| `data/lumiere/v4/reviewed/` | The 46-patient question items: stems, options, answer key, key origin |
| `data/lumiere/v4/slices/` | The images shown to the models (rendered from LUMIERE) |
| `data/lumiere/v4/counterfactual_pairs.json` | Donor image assigned to each patient for the swap test |
| `prompts.jsonl` | Exact system and user text of every single-question prompt (image bytes shown as `[IMAGE]`) |
| `results/` | Saved model responses, one folder per run (`raw_results.json`) |
| `run_manifest.json`, `overrides.jsonl` | Which run supplied each response, and which later responses replaced earlier ones |
| `expected/` | The paper's statistics and tables, which `reproduce.sh` compares against |
| `analysis_versions.json` | Package versions, random seeds, equivalence margin, script hashes, source commit |
| `analysis_plan.md` | The internal prespecified analysis plan and its amendment log (incl. the cohort rebuild from 62 to 46); written before the model runs, not externally timestamped |
| `SHA256SUMS` | Checksum of every file (`sha256sum -c SHA256SUMS` to verify) |
| `src/`, `tools/`, `config/`, `tests/` | The analysis code (`reproduce.sh` runs `tools/`) |

`prompts.jsonl` can be rebuilt from the items with `python -m tools.export_release_prompts --out prompts.jsonl`.
A sanity-test of the item construction is available with `python -m tests.test_lumiere_v4`.

## 4. How a response is chosen (provenance)
A model may have several run folders. The loader (`tools.lumiere_v4_stats.load_records`) merges them oldest-first,
sorted by the run timestamp (the `YYYYMMDD_HHMMSS` at the end of each folder name) and keeps the last record for each
`(case_id, phase, condition)`, so the newest run wins; folders with a date before `min_stamp` ran on an earlier item
set and are ignored. `run_manifest.json` lists, per model, every folder in timestamp order, how many of its records were
used, and how many were superseded by a later run; `overrides.jsonl` has one line per superseded record and whether the
answer letter changed. Every reported cell therefore traces to the single `paper_numbers` run that `reproduce.sh` reproduces.

## 5. Post-hoc analyses (shipped as precomputed inputs)
The donor-dependence analyses are loaded by `paper_numbers` as precomputed inputs, like `results/compute_budget.json`.
`results/lumiere_v4_robustness_*.json` depends on model runs under alternative donor assignments and is NOT regenerated
from scratch by `reproduce.sh`. The other two are CPU re-analyses of the shipped responses and can be rerun directly
(seeds in `analysis_versions.json`):

    python -m tools.lumiere_v4_donor_validation   # synthetic-predictor validation of the donor-tracking test
    python -m tools.lumiere_v4_perm_validation    # Type-I calibration of the conditional donor-label permutation

`data/lumiere/v4/alt_pairs/` holds the released alternative donor-assignment identities (5 constraint-valid assignments
+ `manifest.json`, from `tools/lumiere_v4_altpairs.py`); `tools/lumiere_v4_robustness.py` re-runs the gain and permutation
on each. The conditional permutation (`tools/lumiere_v4_strat_perm.py`) assigns constrained donor-key labels sequentially
in random block order; it is constraint-valid but not exactly uniform over admissible allocations, so it is reported as a
reference distribution for the synthetic nulls evaluated, not as a randomization test for the image assignment.

## 6. License
Slices and measurements are derived from the LUMIERE dataset (Suter et al., 2022, Scientific Data;
doi:10.6084/m9.figshare.c.5904905.v1), released for non-commercial use with attribution. They are shared here only for
non-commercial research evaluation; any reuse must cite LUMIERE.

## 7. Not included
Model weights, API keys, and the full LUMIERE imaging archive.
"""

if __name__ == "__main__":
    main()
