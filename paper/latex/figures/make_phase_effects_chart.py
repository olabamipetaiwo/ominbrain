"""Per-phase paired effect of images (image minus text-only accuracy) with patient-clustered 95% CIs.

Data source: results/lumiere_reviewer_stats.json (written by `python -m tools.lumiere_reviewer_stats`;
v3 items, non-gated, 52 patients, 10,000 patient-level bootstrap resamples). Replaces the earlier
image-vs-text-only bar chart, which only duplicated the overall-accuracy table. Regenerate whenever
that JSON changes:  python paper/latex/figures/make_phase_effects_chart.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
stats = json.loads((ROOT / "results/lumiere_reviewer_stats.json").read_text())["accuracy"]

PHASES = ["AIA", "LIL", "DSCR", "PJRF", "TCM"]
MODELS = ["MedGemma-4B", "Gemma-3-12B", "Gemma-3-27B", "Llama-4-Scout"]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # categorical slots 1-4 (validated; contrast relief = legend + markers)
MARKERS = ["o", "s", "^", "D"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#dedcd6"

plt.rcParams.update({"font.family": "serif", "font.size": 8, "text.color": INK, "axes.edgecolor": INK2,
                     "xtick.color": INK, "ytick.color": INK})

fig, ax = plt.subplots(figsize=(3.3, 3.5))
n = len(MODELS)
offsets = [(i - (n - 1) / 2) * 0.16 for i in range(n)]
for j, ph in enumerate(PHASES):
    y0 = len(PHASES) - 1 - j
    for i, m in enumerate(MODELS):
        d = stats[m]["per_phase"][ph]
        y = y0 + offsets[i]
        ax.plot([100 * d["ci"][0], 100 * d["ci"][1]], [y, y], color=COLORS[i], lw=1.2, solid_capstyle="round", zorder=2)
        ax.plot(100 * d["diff"], y, MARKERS[i], color=COLORS[i], ms=4.5, mec="#fcfcfb", mew=0.8, zorder=3,
                label=m if j == 0 else None)
ax.axvline(0, color=INK2, lw=0.8, zorder=1)
ax.set_yticks(range(len(PHASES)))
ax.set_yticklabels(PHASES[::-1])
ax.set_ylim(-0.6, len(PHASES) - 0.4)
ax.set_xlabel("Image minus text-only accuracy (pp)\n(right = image helps)")
ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=7, handletextpad=0.3,
          columnspacing=1.0)
fig.tight_layout()
out = Path(__file__).with_name("phase_effects.pdf")
fig.savefig(out, bbox_inches="tight")
fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
print("saved", out)
