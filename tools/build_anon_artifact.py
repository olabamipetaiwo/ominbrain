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
         "paper_v4_example", "lumiere_gating_stats", "export_release_prompts", "compute_budget"]
DATA_DIRS = ["data/lumiere/v4/reviewed", "data/lumiere/v4/facts", "data/lumiere/v4/measurements", "data/lumiere/v4/slices"]
DATA_FILES = ["data/lumiere/v4/selection_report.json", "data/lumiere/v4/counterfactual_pairs.json",
              "data/lumiere/tabular/LUMIERE-Demographics_Pathology.csv", "data/lumiere/tabular/LUMIERE-datacompleteness.csv",
              "data/lumiere/tabular/LUMIERE-ExpertRating-v202211.csv"]
RESULT_FILES = ["results/compute_budget.json"]
EXPECTED = ["results/lumiere_v4_stats.json", "results/lumiere_v4_stats.md", "results/lumiere_v4_supplement.json",
            "results/lumiere_v4_supplement.md", "results/lumiere_v4_baselines.json", "results/lumiere_v4_baselines.md"]
GENERATED = ["numbers.json", "numbers.tex", "tab_v4_e1.tex", "tab_v4_e2.tex", "tab_v4_e3.tex", "tab_v4_e3trans.tex",
             "tab_v4_e5.tex", "tab_v4_ctrl.tex", "tab_v4_handling.tex", "tab_v4_inputcheck.tex"]
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


def folders_for(model: str) -> list[str]:
    return [d for d in sorted(glob.glob(f"results/lumiere_v4_{model}_*"))
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

    (out / "run_manifest.json").write_text(json.dumps({
        "loader_rule": "tools.lumiere_v4_stats.load_records: job folders of a model sorted by name (= by timestamp); a later record with the same "
                       "(case_id, phase, condition) silently replaces the earlier one. Folders with a stamp before min_stamp ran on different items and are ignored.",
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


README = """# Anonymous reproducibility artifact

Regenerates every statistic, macro and table of the intervention study from the shipped model responses. No model is called.

## Layout
- `src/ config/ tools/ tests/` code, same layout as the repository, so `python -m tools.<name>` runs from this directory.
- `data/lumiere/v4/` the item set: `reviewed/` items with answer keys, options and key origin; `facts/` per-patient facts;
  `measurements/` cached lesion measurements from the public segmentation masks; `slices/` the rendered slice images the models saw (derived from LUMIERE; see License); `selection_report.json` cohort and exclusion counts; `counterfactual_pairs.json` donor assignment for the swap condition.
- `results/` the raw model records (`raw_results.json` per job folder), one folder per job. Folder names end in `<date>_<time>`.
- `prompts.jsonl` the exact system and user text of every single-question prompt (image bytes replaced by `[IMAGE]`).
  Chain-run prompts paste the model's own earlier answers into later prompts, so they are built at run time
  (`src/prompts.py::build_main_prompt`); their responses are in the chain job folders (`raw_response` per question).
- `run_manifest.json`, `overrides.jsonl` which job folder supplied each record and which records replaced earlier ones.
  The loader keeps the last record per (case, phase, condition) over job folders sorted by timestamp; a rerun of the
  image-and-context conditions with a reworded DSCR stem relied on this. The manifest lists every replacement and whether the answer changed.
- `analysis_versions.json` package versions, seeds (bootstrap seed, 10,000 resamples), margin, first admitted job stamp, script hashes.
- `expected/` the statistics and generated tables shipped with the paper.

## Reproduce
    python -m venv .venv && . .venv/bin/activate && pip install numpy pandas scipy scikit-learn pillow matplotlib
    bash reproduce.sh

`reproduce.sh` reruns the statistics, supplement, baselines and table generation, then reports whether each output is identical to
`expected/`. To regenerate the prompt file: `python -m tools.export_release_prompts --out prompts.jsonl`.

## License and attribution
The slice images and measurements are derived from the LUMIERE dataset (Suter et al., 2022, Scientific Data; Figshare DOI
10.6084/m9.figshare.c.5904905.v1), which is released for non-commercial use with attribution. They are shared here for
non-commercial research evaluation only, under the same terms; any reuse must cite LUMIERE. The images are skull-stripped and
de-identified by the dataset's authors. Code in this artifact is provided for review and reproduction.

## Not included
Model weights, API keys and the full LUMIERE imaging archive. Segmentation masks are automated (not manually verified);
response ratings come from the public dataset. The answer keys are not clinician-validated.
"""

if __name__ == "__main__":
    main()
