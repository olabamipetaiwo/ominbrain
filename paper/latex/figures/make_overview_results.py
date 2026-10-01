"""E1 image effect (image minus text-only accuracy) per model, by phase, with 95% CIs.

Data source: paper/latex/generated/numbers.json -- the SAME generated macros the
manuscript cites (written by `python -m tools.paper_numbers`). Reading the numbers
file, not a results/ JSON, locks this figure to the paper's cited values so it can
never drift from Table E1. Regenerate whenever the macros change:
    python paper/latex/figures/make_overview_results.py

Shows the four open-weight models against the Gemini reference. The reference extracts
image content (large positive effect on AIA/LIL); the open models hug zero. Precision/
stack controls (Gemma-3-27B-bf16, Pixtral-12B) are reported in the paper tables, not
plotted here, to keep the contrast legible.
"""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[3]
NUM = json.loads((ROOT / "paper/latex/generated/numbers.json").read_text())


def val(macro):
    """Parse a generated numeric macro (strips $-$, +, \\%, whitespace) to float."""
    s = NUM[macro]
    s = s.replace("$-$", "-").replace("−", "-").replace("\\%", "").replace("+", "").strip()
    return float(s)


PHASES = ["AIA", "LIL", "DSCR"]
# (display name, macro tag, is-reference)
MODELS = [
    ("Gemini-3.6-Flash (ref.)", "Gemini", True),
    ("MedGemma-4B", "MedGemma", False),
    ("Gemma-3-12B", "GemmaTwelve", False),
    ("Gemma-3-27B", "GemmaTwentySeven", False),
    ("Llama-4-Scout", "Scout", False),
]
# validated categorical slots (matches make_phase_effects_chart.py); reference is charcoal.
COLORS = {"Gemini": "#0b0b0b", "MedGemma": "#2a78d6", "GemmaTwelve": "#eb6834",
          "GemmaTwentySeven": "#1baf7a", "Scout": "#eda100"}
MARKERS = {"Gemini": "*", "MedGemma": "o", "GemmaTwelve": "s",
           "GemmaTwentySeven": "^", "Scout": "D"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#dedcd6"

plt.rcParams.update({"font.family": "serif", "font.size": 8, "text.color": INK,
                     "axes.edgecolor": INK2, "xtick.color": INK, "ytick.color": INK})

fig, ax = plt.subplots(figsize=(3.3, 3.2))
n = len(MODELS)
offsets = [(i - (n - 1) / 2) * 0.15 for i in range(n)]

ax.axhline(0, color=INK2, lw=0.8, zorder=1)
for i, (name, tag, is_ref) in enumerate(MODELS):
    xs, ys, lo, hi = [], [], [], []
    for j, ph in enumerate(PHASES):
        d = val(f"vfourEoneDiff{ph}{tag}")
        l = val(f"vfourEoneLo{ph}{tag}")
        h = val(f"vfourEoneHi{ph}{tag}")
        xs.append(j + offsets[i])
        ys.append(d)
        lo.append(d - l)
        hi.append(h - d)
    ms = 7 if is_ref else 4.5
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt=MARKERS[tag], color=COLORS[tag],
                ms=ms, mec=COLORS[tag], mfc=("none" if not is_ref else COLORS[tag]),
                mew=1.1, elinewidth=1.0, capsize=2.0, zorder=3 + (2 if is_ref else 0))

ax.set_xticks(range(len(PHASES)))
ax.set_xticklabels(PHASES)
ax.set_xlim(-0.5, len(PHASES) - 0.5)
ax.set_ylabel("Image $-$ text-only accuracy (pp)")
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)

handles = [Line2D([0], [0], marker=MARKERS[t], color="none", mec=COLORS[t],
                  mfc=(COLORS[t] if r else "none"), mew=1.1,
                  ms=(7 if r else 4.5), label=nm)
           for nm, t, r in MODELS]
ax.legend(handles=handles, fontsize=6.3, loc="upper right", frameon=False,
          handletextpad=0.3, labelspacing=0.25, borderaxespad=0.1)

fig.tight_layout(pad=0.4)
out = ROOT / "paper/latex/figures/overview_results.pdf"
fig.savefig(out, bbox_inches="tight")
print("wrote", out)
