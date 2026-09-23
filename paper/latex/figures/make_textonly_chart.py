"""Generate the text-only-vs-image accuracy chart for the paper's Results section.

Data source: results/lumiere_summary_all.md (v3, non-gated overall accuracy),
identical to Table 1 (tab:textonly) in paper/latex/acl_latex.tex. Regenerate this
if those numbers ever change.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

models = ["Llama-4-Scout", "Gemma-3-27B", "Gemma-3-12B", "MedGemma-4B"]
models_wrapped = ["Llama-4-\nScout", "Gemma-3-\n27B", "Gemma-3-\n12B", "MedGemma-\n4B"]
image = [49, 54, 48, 33]
textonly = [52, 50, 51, 36]

BLUE = "#2a78d6"
ORANGE = "#eb6834"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#dedcd6"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "text.color": TEXT_PRIMARY,
    "axes.edgecolor": TEXT_SECONDARY,
    "axes.labelcolor": TEXT_PRIMARY,
    "xtick.color": TEXT_PRIMARY,
    "ytick.color": TEXT_PRIMARY,
})

fig, ax = plt.subplots(figsize=(3.35, 2.55))

x = np.arange(len(models))
w = 0.36

b1 = ax.bar(x - w / 2, image, width=w, color=BLUE, label="Image", zorder=3)
b2 = ax.bar(x + w / 2, textonly, width=w, color=ORANGE, hatch="///",
            edgecolor="white", linewidth=0.6, label="Text-only", zorder=3)

for bars in (b1, b2):
    for rect in bars:
        h = rect.get_height()
        ax.annotate(f"{h:.0f}", (rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 2), textcoords="offset points",
                    ha="center", va="bottom", fontsize=7.3, color=TEXT_PRIMARY)

ax.set_ylim(0, 100)
ax.set_ylabel("Non-gated overall accuracy (%)")
ax.set_xticks(x)
ax.set_xticklabels(models_wrapped, fontsize=7.3, linespacing=1.3)
ax.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color(TEXT_SECONDARY)
ax.tick_params(axis="both", length=0)

ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=2,
          frameon=False, handlelength=1.4, columnspacing=1.2, fontsize=8)

fig.tight_layout()
fig.savefig("text_only_ablation.pdf", bbox_inches="tight", pad_inches=0.02)
print("wrote text_only_ablation.pdf")
