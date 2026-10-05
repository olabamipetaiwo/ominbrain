"""
Worked v4 example for the paper appendix (paper/review.md concern 8; added 2026-09-25). Keys, the DSCR measurements, the model answers and the
donor pairs are read from the item files, the donor-pair file and the result records; nothing quantitative is typed by hand. Stems are abbreviated
to the question itself (the descriptive preamble, the RANO recitation and the full option lists duplicate the methods and live in the artifact).

The patient is the first, in id order, that has all five phases and a three-image DSCR item (a rule fixed before looking at any answer).
Writes paper/latex/figures/v4_example.png and paper/latex/generated/v4_example.tex (input by the appendix).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

from src.lumiere_loader import _shuffle_options
from tools.lumiere_v4_stats import load_records

V4 = Path("data/lumiere/v4")
OUT_TEX = Path("paper/latex/generated/v4_example.tex")
OUT_PNG = Path("paper/latex/figures/v4_example.png")
SHORT_LAB = {"T1-weighted, before contrast": "T1", "T1-weighted, after gadolinium contrast": "T1c", "T2-weighted": "T2",
             "FLAIR (fluid-attenuated inversion recovery)": "FLAIR",
             "Right hemisphere, anterior half": "R ant", "Right hemisphere, posterior half": "R post",
             "Left hemisphere, anterior half": "L ant", "Left hemisphere, posterior half": "L post",
             "Progressive disease": "PD", "Stable disease": "SD", "Partial response": "PR", "Complete response": "CR"}
MODELS = [("Gemini-3.6-Flash", "Gemini-3.6-Flash (reference)"), ("Llama-4-Scout", "Llama-4-Scout"), ("Gemma-3-27B", "Gemma-3-27B"),
          ("Gemma-3-12B", "Gemma-3-12B"), ("MedGemma-4B", "MedGemma-4B")]


def esc(s: str) -> str:
    t = (str(s).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
         .replace("#", r"\#").replace("$", r"\$"))
    return t.replace("->", r"$\rightarrow$").replace("<=", r"$\le$").replace(">=", r"$\ge$")


def load_items(pid: str) -> dict:
    return {it["id"].split("_")[-1]: it for it in json.loads((V4 / "reviewed" / f"{pid}.json").read_text())}


def shown_options(it: dict) -> tuple[dict, str]:
    """The options and key letter exactly as the model was shown them (the loader shuffles all but ordered items)."""
    o, c = it["options"], it["correct_answer"]
    return (o, c) if it.get("ordered_options") else _shuffle_options(o, c, it["id"])


def pick_patient() -> str:
    for f in sorted((V4 / "reviewed").glob("Patient-*.json")):
        items = {it["id"].split("_")[-1]: it for it in json.loads(f.read_text())}
        if all(p in items for p in ("AIA", "LIL", "DSCR", "PJRF", "TCM")) and len(items["DSCR"]["image_files"]) == 3:
            return f.stem
    raise SystemExit("no patient with all five phases and a three-image DSCR item")


def tile(path: Path, label: str, w: int = 330) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im = im.resize((w, int(im.size[1] * w / im.size[0])), Image.LANCZOS)
    canvas = Image.new("RGB", (w, im.size[1] + 22), (255, 255, 255))
    canvas.paste(im, (0, 22))
    ImageDraw.Draw(canvas).text((4, 4), label, fill=(0, 0, 0))
    return canvas


def figure(pid: str, items: dict, cf: dict) -> None:
    def img_of(p, ph, i=0):
        return V4 / "slices" / p / items_by_pid[p][ph]["image_files"][i]
    items_by_pid = {pid: items}
    for ph in ("AIA", "LIL"):
        items_by_pid[cf["detail"][ph]["partner"]] = load_items(cf["detail"][ph]["partner"])
    row1 = [tile(img_of(pid, "AIA"), f"AIA, {pid}"), tile(img_of(cf["detail"]["AIA"]["partner"], "AIA"), f"AIA donor, {cf['detail']['AIA']['partner']}"),
            tile(img_of(pid, "LIL"), f"LIL, {pid}"), tile(img_of(cf["detail"]["LIL"]["partner"], "LIL"), f"LIL donor, {cf['detail']['LIL']['partner']}")]
    labels = items["DSCR"]["image_labels"]
    row2 = [tile(V4 / "slices" / pid / f, f"DSCR image {i + 1}: {labels[i]}"[:46]) for i, f in enumerate(items["DSCR"]["image_files"])]
    width = 4 * 330 + 30
    h1, h2 = max(t.size[1] for t in row1), max(t.size[1] for t in row2)
    canvas = Image.new("RGB", (width, h1 + h2 + 10), (255, 255, 255))
    x = 0
    for t in row1:
        canvas.paste(t, (x, 0)); x += t.size[0] + 10
    x = 0
    for t in row2:
        canvas.paste(t, (x, h1 + 10)); x += t.size[0] + 10
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_PNG)


def main() -> None:
    pid = pick_patient()
    items = load_items(pid)
    cf = json.loads((V4 / "counterfactual_pairs.json").read_text())[pid]
    figure(pid, items, cf)
    lines = []

    def ask(q: str) -> str:
        """The question itself (last interrogative sentence); the descriptive preamble and the RANO recitation duplicate the methods and are dropped."""
        m = re.findall(r"[^.?!]*\?", q)
        return esc(m[-1].strip()) if m else esc(q)

    def block(ph: str, title: str) -> None:
        it = items[ph]
        o, c = shown_options(it)
        lines.append(r"\paragraph{%s.} %s \emph{Key:} %s) %s." % (title, ask(it["question"]), c, esc(o[c].rstrip("."))))

    lines.append(r"The patient is %s, the first in id order with all five phases and a three-image DSCR item (a rule fixed before any answer was inspected). "
                 r"Figure~\ref{fig:v4example} shows the images the models see and the donor images used in the swap; each item is four-way multiple choice, with the full stems and options in the reproducibility artifact." % esc(pid))
    block("AIA", "AIA (positive control)")
    block("LIL", "LIL")
    d = items["DSCR"]
    fu = d["facts_used"]
    block("DSCR", "DSCR")
    bpr, bpn, bpf = fu["bp_ref_mm2"], fu["bp_nadir_mm2"], fu["bp_followup_mm2"]
    if fu["rule_label"] == "progressive disease":
        why = (f"the follow-up product is {100 * bpf / bpn:.0f}\\% of the nadir's" if bpn >= 100 else
               "there is no measurable enhancing disease at the nadir and a measurable lesion at follow-up (a new measurable lesion)")
    elif fu["rule_label"] in ("partial response", "complete response"):
        why = f"the follow-up product is {100 * bpf / bpr:.0f}\\% of the baseline's"
    else:
        why = "the change is between the response and progression thresholds"
    agree = (r"The expert rating is %s (``%s''), the same category, so this is not an audit disagreement."
             if fu["concordant"] else
             r"The expert rating is %s (``%s''), a different category, so this is an audit disagreement.")
    lines.append((r"The key comes from the bidimensional products of the tracked lesion on the three slices (%.0f, %.0f and %.0f\,mm$^2$ at baseline, nadir and follow-up); "
                  r"%s, which the rule calls %s. " + agree)
                 % (bpr, bpn, bpf, why, esc(fu["rule_label"]), esc(fu["expert_rating"]), esc(fu["expert_rationale"])))
    block("TCM", "TCM")
    tr = items["TCM"]["tcm_rule"]
    lines.append(r"The stem states the patient facts (see the artifact) and the rule: %s. Here the category is %s and chemoradiotherapy ended %d weeks before the scan, so the class is %s; changing the stated timing across the 12-week window or the stated category changes the rule's answer (the fact flips of E3)."
                 % (esc(tr["rule"]), esc(tr["rano"]), tr["weeks_since_chemoradiotherapy"], esc(tr["class"])))
    outcome = "death" if items["PJRF"]["forecast"]["outcome"] == 1 else "survival"
    lines.append(r"\paragraph{PJRF (secondary).} Same patient facts as TCM; the model forecasts the probability of death within 52 weeks of the scan (recorded outcome: %s), scored by the Brier score." % outcome)
    d = cf["detail"]
    def sl(txt):
        return SHORT_LAB.get(txt, esc(txt))
    lines.append(r"\paragraph{Donor swap.} Each image is replaced by a donor's whose key differs (AIA %s, %s not %s; LIL %s, %s not %s; DSCR %s, %s not %s); the stem and options are unchanged, so the donor's answer is always an option."
                 % (esc(d["AIA"]["partner"]), sl(d["AIA"]["donor_key"]), sl(d["AIA"]["own_key"]),
                    esc(d["LIL"]["partner"]), sl(d["LIL"]["donor_key"]), sl(d["LIL"]["own_key"]),
                    esc(d["DSCR"]["partner"]), sl(d["DSCR"]["donor_key"]), sl(d["DSCR"]["own_key"])))
    # answers (own/text/swap) per model -- single-column table, not a full-width float, to save appendix space
    def lab(ph, rec):
        o, _ = shown_options(items[ph])
        return SHORT_LAB.get(o.get(rec["model_answer"], "?"), "?") if rec else "--"
    keyrow = []
    for ph in ("AIA", "LIL", "DSCR"):
        o, c = shown_options(items[ph])
        keyrow.append(f"{SHORT_LAB[o[c]]}/{SHORT_LAB[cf['detail'][ph]['donor_key']]}")
    rows = [r"Key/donor & " + " & ".join(keyrow) + r" \\", r"\midrule"]
    for m, nm in MODELS:
        recs = load_records(m)
        cells = ["/".join(lab(ph, recs.get((pid, ph, k))) for k in ("own", "text", "swap")) for ph in ("AIA", "LIL", "DSCR")]
        rows.append(f"{esc(m)} & " + " & ".join(cells) + r" \\")
    lines.append(r"""
\begin{table}[t]
\centering
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lccc}
\toprule
 & AIA & LIL & DSCR \\
\midrule
%s
\bottomrule
\end{tabular}
\caption{Answers for %s (own/text/swap in each cell), with the key and donor key; Gemini-3.6-Flash is the reference model. Labels: T1c is T1 after contrast; L/R hemisphere, ant/post half; PD, SD, PR, CR are RANO categories.}
\label{tab:v4example}
\end{table}
""" % ("\n".join(rows), esc(pid)))
    lines.append(r"""
\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{figures/v4_example}
\caption{Images for %s. Top: the AIA slice and its donor, the LIL slice and its donor. Bottom: the three DSCR slices (baseline, nadir, follow-up). Slices are atlas-space, skull-stripped, magnified 4$\times$, with a 20\,mm scale bar.}
\label{fig:v4example}
\end{figure*}
""" % esc(pid))
    OUT_TEX.write_text("\n\n".join(lines))
    print(f"wrote {OUT_TEX} and {OUT_PNG} for {pid}")


if __name__ == "__main__":
    main()
