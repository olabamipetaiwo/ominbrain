"""GPU-hours and API usage behind the paper's numbers (ARR Responsible NLP checklist C1). Run on the cluster:
  python -m tools.compute_budget          # writes results/compute_budget.json, read by tools/paper_numbers.py
GPU-hours = elapsed wall time x GPUs allocated, over every SLURM job of this user whose name contains 'lumi' since 2026-08-01 (all LUMIERE work,
including failed and cancelled jobs); the v4 family (intervention runs, ordinary v4 chain runs, input checks) is reported separately."""

import glob
import json
import re
import subprocess
from pathlib import Path


def main() -> None:
    out = subprocess.run(["sacct", "-u", subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip(), "-S", "2026-08-01", "-E", "now",
                          "-X", "-n", "-P", "--format=JobName,AllocTRES,ElapsedRaw"], capture_output=True, text=True).stdout
    tot = v4 = 0.0
    n = nv4 = 0
    for line in out.splitlines():
        name, tres, el = line.split("|")
        if "lumi" not in name.lower() or not el.isdigit():
            continue
        m = re.search(r"gres/gpu=(\d+)", tres)
        h = int(el) / 3600 * (int(m.group(1)) if m else 1)
        tot += h
        n += 1
        if any(k in name.lower() for k in ("v4", "inputcheck", "gemini")):
            v4 += h
            nv4 += 1
    api = {"calls": 0, "prompt_tokens": 0, "total_tokens": 0}
    for f in glob.glob("results/lumiere_v4_Gemini-3.6-Flash_*/usage.json"):
        u = json.loads(Path(f).read_text())
        for k in api:
            api[k] += u.get(k, 0)
    res = {"gpu_hours_all": round(tot, 1), "jobs_all": n, "gpu_hours_v4_family": round(v4, 1), "jobs_v4_family": nv4, "gemini_api": api}
    Path("results/compute_budget.json").write_text(json.dumps(res, indent=2))
    print(res)


if __name__ == "__main__":
    main()
