#!/usr/bin/env bash
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
