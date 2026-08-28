"""
Generates the self-contained LUMIERE expert-review page.

Reads all data/lumiere/drafts/<patient_id>.json + their slice PNGs, embeds
everything (base64 images, item data) into one standalone HTML file at
OUT_PATH — meant to be sent directly to the reviewer (email attachment,
shared-drive link for direct download, etc.) and opened locally in a
browser. NOT published as a claude.ai Artifact: an earlier version used the
`artifact` runtime capability (claude.use("artifact") -> publish()) to
persist decisions server-side, but that requires the viewer to be signed
into a Claude account to write — a non-starter for a non-technical external
reviewer with no such account (discovered when the actual reviewer hit a
login wall trying to save; one item was left in a half-edited "edited"
state with no reviewer name as a result). See paper/update.md's 2026-08-27
entry.

Persistence now works with no account and no server round-trip:
- every action (approve/edit/reject) autosaves the full state to the
  reviewer's own browser via `localStorage`, so progress survives reloads
  in that browser.
- a "Download review file" button saves a fresh, fully self-contained
  `.html` (same format, with current decisions embedded) that the reviewer
  sends back — that file is what tools/sync_lumiere_artifact_review.py
  reads. A "Load review file..." picker re-imports one too, in case they
  switch machines/browsers.

Self-reference note: the "Download review file" button needs to regenerate
a COMPLETE document (doctype/html/head/body) from inside the running page.
This script resolves that by keeping one static "inner content" template,
wrapping it in a doctype/html/head/body shell to compute a fixed base64
blob (TEMPLATE_B64, embedded once, unchanging), and having the page's own JS
decode+re-fill that blob on every download. See the two `@@LUMIERE_*@@`
placeholders below — there is no actual circularity: the b64 blob is
computed once from a string that still contains the placeholders literally,
before either substitution happens.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import config.lumiere as lcfg

DRAFTS_DIR = Path(lcfg.LUMIERE_DATA_DIR) / "drafts"
SLICES_DIR = Path(lcfg.LUMIERE_DATA_DIR) / "slices"
OUT_PATH = Path("tools/lumiere_review_artifact.html")

PHASE_ABBR = {
    "Anatomical and Imaging Assessment": "AIA",
    "Lesion Identification and Localization": "LIL",
    "Diagnostic Synthesis and Causal Reasoning": "DSCR",
    "Prognostic Judgment and Risk Forecasting": "PJRF",
    "Therapeutic Cycle Management": "TCM",
}
PHASE_ORDER = ["AIA", "LIL", "DSCR", "PJRF", "TCM"]


def _fmt_vol(mm3: float) -> str:
    return f"{mm3:,.0f} mm³"


def facts_summary(item: dict) -> str:
    """Plain-language summary of the item's grounding facts, for a clinician
    reviewer — not raw JSON. Field shapes are per-phase (see src/lumiere_facts.py)."""
    phase = PHASE_ABBR.get(item["clinical_phase"], "")
    facts = item.get("facts_used", {})

    if phase == "AIA":
        mods = ", ".join(m.upper() for m in facts.get("modalities_available", []))
        return f"Sequences available: {mods}. Segmentation: {facts.get('segmentation_source', '?')}."

    if phase == "LIL":
        b, f = facts.get("baseline", {}), facts.get("followup", {})
        pct = facts.get("volume_change_pct")
        pct_str = f"{'+' if (pct or 0) >= 0 else ''}{pct}%" if pct is not None else "n/a"
        b_region = next(iter(b.get("regions", {}).values()), "unspecified")
        f_region = next(iter(f.get("regions", {}).values()), "unspecified")
        return (
            f"Baseline ({b.get('timepoint_id', '?')}): {b_region}, {_fmt_vol(b.get('total_volume_mm3', 0))}. "
            f"Follow-up ({f.get('timepoint_id', '?')}): {f_region}, {_fmt_vol(f.get('total_volume_mm3', 0))} "
            f"({pct_str} change)."
        )

    if phase == "DSCR":
        rationale = facts.get("rationale") or "none recorded"
        return (
            f"RANO assessment at {facts.get('timepoint_id', '?')}: {facts.get('rating_label', '?')}. "
            f"Rationale: {rationale}."
        )

    if phase == "PJRF":
        wk = facts.get("survival_weeks")
        wk_str = f"{wk} weeks (~{wk / 52.1:.1f} yrs)" if wk else "not recorded"
        return (
            f"{(facts.get('sex') or '?').title()}, age {facts.get('age_at_surgery', '?')} at surgery. "
            f"MGMT: {facts.get('mgmt_status', '?')}. IDH: {facts.get('idh_status', '?')}. "
            f"Overall survival: {wk_str}."
        )

    if phase == "TCM":
        n = facts.get("progression_events_n", 0)
        pseudo = "yes" if facts.get("possible_pseudoprogression_flag") else "no"
        return (
            f"{facts.get('protocol_assumed', '?')} "
            f"Progression events recorded: {n}. Possible pseudoprogression flag: {pseudo}."
        )

    return json.dumps(facts)


def slice_timepoints_for(item: dict, patient_items: list[dict]) -> list[tuple[str, str | None]]:
    """Ported from tools/lumiere_review_app.py::_slice_timepoints_for — LIL
    and DSCR are baseline-vs-follow-up comparisons, show both slices; other
    phases are single-timepoint."""
    phase = item["clinical_phase"]
    if phase == "Lesion Identification and Localization":
        f = item.get("facts_used", {})
        return [("baseline", f.get("baseline", {}).get("timepoint_id")),
                ("follow-up", f.get("followup", {}).get("timepoint_id"))]
    if phase == "Diagnostic Synthesis and Causal Reasoning":
        lil = next((q for q in patient_items
                    if q["clinical_phase"] == "Lesion Identification and Localization"), None)
        if lil:
            f = lil.get("facts_used", {})
            return [("baseline", f.get("baseline", {}).get("timepoint_id")),
                    ("follow-up", f.get("followup", {}).get("timepoint_id"))]
    return [("timepoint", item.get("timepoint"))]


def build_state() -> dict:
    images: dict[str, str] = {}
    items: list[dict] = []

    patient_files = sorted(DRAFTS_DIR.glob("Patient-*.json"))
    for fpath in patient_files:
        pid = fpath.stem
        patient_items = json.loads(fpath.read_text())
        for it in patient_items:
            tps = slice_timepoints_for(it, patient_items)
            image_keys, image_labels = [], []
            for label, tp in tps:
                if not tp:
                    continue
                key = f"{pid}/{tp}"
                if key not in images:
                    png_path = SLICES_DIR / pid / f"{tp}.png"
                    if png_path.exists():
                        b64 = base64.b64encode(png_path.read_bytes()).decode()
                        images[key] = f"data:image/png;base64,{b64}"
                if key in images:
                    image_keys.append(key)
                    image_labels.append(label)

            items.append({
                "id": it["id"],
                "patient_id": pid,
                "phase_abbr": PHASE_ABBR.get(it["clinical_phase"], "?"),
                "clinical_phase": it["clinical_phase"],
                "task_label": it["task_label"],  # required by lumiere_loader.build_lumiere_cases()
                "question": it["question"],
                "options": it["options"],
                "correct_answer": it["correct_answer"],
                "original_question": it["question"],
                "original_options": it["options"],
                "original_answer": it["correct_answer"],
                "distractor_rationale": it.get("distractor_rationale", ""),
                "distractor_confidence": it.get("distractor_confidence", "high"),
                "needs_expert_judgment": bool(it.get("needs_expert_judgment", False)),
                "facts_summary": facts_summary(it),
                "image_keys": image_keys,
                "image_labels": image_labels,
                "review_status": "pending",
                "reviewer": "",
                "review_notes": "",
            })

    print(f"Prepared {len(items)} items across {len(patient_files)} patients, {len(images)} images.")
    return {"reviewerName": "", "images": images, "items": items}


# ---------------------------------------------------------------------------
# Page template (this is the entire visible/interactive artifact)
# ---------------------------------------------------------------------------

INNER_CONTENT = r'''<script id="lumiere-data" type="application/json">@@LUMIERE_DATA@@</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<title>LUMIERE Chain Review</title>
<style>
  :root {
    --bg: #F2F0EB; --surface: #FFFFFF; --surface-2: #F7F5F0;
    --text: #1C1D1F; --text-dim: #6B6D70; --border: #DEDAD1;
    --accent: #B8842E; --accent-text: #FFFFFF;
    --good: #2F8F5B; --danger: #C1443E; --warn: #B8842E;
    --viewer-bg: #0B0C0E; --viewer-label: #E3B04B;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #17181C; --surface: #1F2126; --surface-2: #24262C;
      --text: #ECE9E2; --text-dim: #9A9B9E; --border: #2C2E34;
      --accent: #E3B04B; --accent-text: #17181C;
      --good: #5FBE87; --danger: #E2726C; --warn: #E3B04B;
    }
  }
  :root[data-theme="dark"] {
    --bg: #17181C; --surface: #1F2126; --surface-2: #24262C;
    --text: #ECE9E2; --text-dim: #9A9B9E; --border: #2C2E34;
    --accent: #E3B04B; --accent-text: #17181C;
    --good: #5FBE87; --danger: #E2726C; --warn: #E3B04B;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: 'Archivo', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .mono { font-family: 'IBM Plex Mono', ui-monospace, monospace; }
  #app { max-width: 1180px; margin: 0 auto; padding: 20px 20px 64px; }

  .topbar {
    display: flex; flex-wrap: wrap; gap: 16px; align-items: center;
    justify-content: space-between; padding: 16px 20px; margin-bottom: 20px;
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  }
  .topbar h1 { font-size: 1.15rem; font-weight: 700; margin: 0; letter-spacing: -0.01em; }
  .topbar .sub { color: var(--text-dim); font-size: 0.82rem; margin-top: 2px; }
  .reviewer-field { display: flex; align-items: center; gap: 8px; }
  .reviewer-field label { font-size: 0.78rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.04em; }
  .reviewer-field input {
    font-family: inherit; font-size: 0.9rem; padding: 6px 10px;
    border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text);
    width: 160px;
  }

  .progress-block { display: flex; align-items: center; gap: 14px; min-width: 220px; }
  .progress-count {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; font-weight: 600;
    color: var(--text); white-space: nowrap; font-variant-numeric: tabular-nums;
  }
  .progress-count .of { color: var(--text-dim); font-weight: 500; font-size: 1rem; }
  .progress-track {
    flex: 1; height: 8px; border-radius: 999px; background: var(--surface-2);
    border: 1px solid var(--border); overflow: hidden; min-width: 100px;
  }
  .progress-fill { height: 100%; background: var(--accent); transition: width 0.2s ease; }

  .pills { display: flex; gap: 8px; flex-wrap: wrap; }
  .pill {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.76rem; font-weight: 500;
    padding: 4px 10px; border-radius: 999px; display: flex; align-items: center; gap: 6px;
    border: 1px solid var(--border); font-variant-numeric: tabular-nums;
  }
  .pill .dot { width: 7px; height: 7px; border-radius: 50%; }
  .pill.approved .dot { background: var(--good); }
  .pill.edited .dot { background: var(--accent); }
  .pill.rejected .dot { background: var(--danger); }
  .pill.pending .dot { background: var(--text-dim); }

  .stepper { display: flex; gap: 6px; margin: 0 0 20px; }
  .step {
    flex: 1; text-align: center; padding: 7px 4px; border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.03em; border: 1px solid var(--border); color: var(--text-dim);
    background: var(--surface);
  }
  .step.current { border-color: var(--accent); color: var(--accent); background: var(--surface-2); }
  .step.done-approved { color: var(--good); }
  .step.done-edited { color: var(--accent); }
  .step.done-rejected { color: var(--danger); text-decoration: line-through; }

  .grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: 20px; }
  @media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }

  .panel {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px; min-width: 0;
  }
  .panel h2 {
    font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--text-dim); margin: 0 0 12px; font-weight: 600;
  }

  .viewer { background: var(--viewer-bg); border-radius: 8px; padding: 14px; }
  .viewer-frames { display: flex; gap: 10px; flex-wrap: wrap; }
  .frame { flex: 1; min-width: 140px; }
  .frame img { width: 100%; border-radius: 4px; display: block; background: #000; }
  .frame .label {
    font-family: 'IBM Plex Mono', monospace; color: var(--viewer-label);
    font-size: 0.7rem; margin-top: 6px; letter-spacing: 0.03em; text-transform: uppercase;
  }
  .frame .none {
    color: #55575c; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
    padding: 30px 8px; text-align: center; border: 1px dashed #33353a; border-radius: 4px;
  }

  .facts-readout {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; line-height: 1.6;
    color: var(--text); background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 6px; padding: 12px 14px; margin-top: 12px;
  }

  .flag-banner {
    display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 600;
    color: var(--warn); background: color-mix(in srgb, var(--warn) 14%, transparent);
    border: 1px solid var(--warn); border-radius: 6px; padding: 8px 12px; margin-bottom: 14px;
  }

  .q-text {
    width: 100%; font-family: inherit; font-size: 0.98rem; line-height: 1.5;
    padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--surface-2); color: var(--text); resize: vertical; min-height: 64px;
    overflow-y: hidden;
  }
  .options { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
  .option-row { display: flex; align-items: center; gap: 8px; }
  .option-row input[type="radio"] { accent-color: var(--good); width: 16px; height: 16px; flex-shrink: 0; cursor: pointer; }
  .option-row input[type="text"] {
    flex: 1; font-family: inherit; font-size: 0.9rem; padding: 8px 10px;
    border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text);
  }
  .option-row.is-answer input[type="text"] { border-color: var(--good); }

  .rationale { font-size: 0.82rem; color: var(--text-dim); margin-top: 10px; line-height: 1.5; }
  .conf-badge {
    display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    padding: 2px 7px; border-radius: 4px; margin-left: 6px; text-transform: uppercase;
    letter-spacing: 0.03em; vertical-align: middle;
  }
  .conf-badge.low { background: color-mix(in srgb, var(--warn) 20%, transparent); color: var(--warn); }
  .conf-badge.high { background: color-mix(in srgb, var(--good) 16%, transparent); color: var(--good); }

  .notes {
    width: 100%; font-family: inherit; font-size: 0.85rem; margin-top: 12px;
    padding: 8px 10px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--surface-2); color: var(--text); resize: vertical; min-height: 44px;
  }

  .actions { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
  button {
    font-family: 'Archivo', inherit; font-weight: 600; font-size: 0.86rem;
    padding: 9px 16px; border-radius: 6px; border: 1px solid transparent; cursor: pointer;
  }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-approve { background: var(--good); color: #fff; }
  .btn-edit { background: var(--accent); color: var(--accent-text); }
  .btn-reject { background: transparent; color: var(--danger); border-color: var(--danger); }
  .btn-ghost { background: transparent; color: var(--text-dim); border-color: var(--border); }

  .navbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 20px; }
  .navbar select {
    font-family: inherit; font-size: 0.85rem; padding: 7px 10px; border-radius: 6px;
    border: 1px solid var(--border); background: var(--surface); color: var(--text); max-width: 320px;
  }
  .status-banner {
    position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 10px 18px; font-size: 0.84rem; box-shadow: 0 6px 20px rgba(0,0,0,0.18);
    display: none; z-index: 10;
  }
  .status-banner.show { display: block; }
  .status-banner.err { border-color: var(--danger); color: var(--danger); }
  .status-banner.ok { border-color: var(--good); color: var(--good); }

  a, button { font-variant-numeric: tabular-nums; }
  h1, h2 { text-wrap: balance; }
</style>
<div id="app"></div>
<div id="status-banner" class="status-banner"></div>
<script>
(function () {
  "use strict";

  const TEMPLATE_B64 = "@@LUMIERE_TEMPLATE@@";
  const RAW = document.getElementById("lumiere-data").textContent;
  const state = JSON.parse(RAW);

  const PHASE_ORDER = ["AIA", "LIL", "DSCR", "PJRF", "TCM"];
  const STORAGE_KEY = "lumiere_review_state_v1";
  let cursor = 0;

  function isFlagged(item) {
    return item.needs_expert_judgment || item.distractor_confidence === "low";
  }

  function sortedItems() {
    return state.items
      .map((it, idx) => ({ it, idx }))
      .sort((a, b) => (isFlagged(b.it) ? 1 : 0) - (isFlagged(a.it) ? 1 : 0))
      .map((x) => x.it);
  }

  function counts() {
    const c = { approved: 0, edited: 0, rejected: 0, pending: 0 };
    for (const it of state.items) c[it.review_status] = (c[it.review_status] || 0) + 1;
    return c;
  }

  function firstPendingIndex(list) {
    const i = list.findIndex((it) => it.review_status === "pending");
    return i === -1 ? 0 : i;
  }

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function showBanner(msg, kind) {
    const el = document.getElementById("status-banner");
    el.textContent = msg;
    el.className = "status-banner show" + (kind ? " " + kind : "");
    clearTimeout(showBanner._t);
    showBanner._t = setTimeout(() => el.classList.remove("show"), 3200);
  }

  function renderStepper(item) {
    const patientItems = state.items.filter((q) => q.patient_id === item.patient_id);
    return `<div class="stepper">${PHASE_ORDER.map((ph) => {
      const q = patientItems.find((x) => x.phase_abbr === ph);
      let cls = "step";
      if (!q) cls += "";
      else if (ph === item.phase_abbr) cls += " current";
      else if (q.review_status === "approved") cls += " done-approved";
      else if (q.review_status === "edited") cls += " done-edited";
      else if (q.review_status === "rejected") cls += " done-rejected";
      return `<div class="${cls}">${ph}</div>`;
    }).join("")}</div>`;
  }

  function renderFrames(item) {
    if (!item.image_keys.length) {
      return `<div class="viewer-frames"><div class="frame"><div class="none">no image rendered</div></div></div>`;
    }
    return `<div class="viewer-frames">${item.image_keys.map((key, i) => {
      const src = state.images[key];
      const label = item.image_labels[i] || "timepoint";
      if (!src) return `<div class="frame"><div class="none">missing: ${escapeHtml(key)}</div></div>`;
      return `<div class="frame"><img src="${src}" alt="${escapeHtml(label)}"><div class="label">${escapeHtml(label)} — ${escapeHtml(key.split("/")[1] || "")}</div></div>`;
    }).join("")}</div>`;
  }

  function render() {
    const list = sortedItems();
    if (cursor >= list.length) cursor = list.length - 1;
    if (cursor < 0) cursor = 0;
    const item = list[cursor];
    const c = counts();
    const letters = Object.keys(item.options);
    const actionsDisabled = false;

    const reviewed = c.approved + c.edited + c.rejected;
    const total = state.items.length;
    const pct = total ? Math.round((reviewed / total) * 100) : 0;

    const html = `
      <div class="topbar">
        <div>
          <h1>LUMIERE Chain Review</h1>
          <div class="sub">${escapeHtml(item.patient_id)} — queue position ${cursor + 1} of ${list.length} · progress autosaves in this browser — download when done</div>
        </div>
        <div class="progress-block">
          <div class="progress-count">${reviewed} <span class="of">/ ${total} reviewed</span></div>
          <div class="progress-track"><div class="progress-fill" style="width: ${pct}%"></div></div>
        </div>
        <div class="pills">
          <span class="pill approved"><span class="dot"></span>${c.approved} approved</span>
          <span class="pill edited"><span class="dot"></span>${c.edited} edited</span>
          <span class="pill rejected"><span class="dot"></span>${c.rejected} rejected</span>
          <span class="pill pending"><span class="dot"></span>${c.pending} pending</span>
        </div>
        <div class="reviewer-field">
          <label for="reviewer-name">Reviewer</label>
          <input id="reviewer-name" type="text" placeholder="your name" value="${escapeHtml(state.reviewerName)}">
        </div>
        <div class="reviewer-field">
          <button class="btn-ghost" id="download-btn" type="button">⬇ Download review file</button>
          <label class="btn-ghost" style="cursor:pointer; margin:0;">
            Load review file…
            <input id="load-file-input" type="file" accept=".html" style="display:none;">
          </label>
        </div>
      </div>

      ${renderStepper(item)}

      ${isFlagged(item) ? `<div class="flag-banner">⚠ ${item.needs_expert_judgment ? "Needs expert judgment" : ""}${item.needs_expert_judgment && item.distractor_confidence === "low" ? " · " : ""}${item.distractor_confidence === "low" ? "Low distractor confidence" : ""}</div>` : ""}

      <div class="grid">
        <div class="panel">
          <h2>${escapeHtml(item.clinical_phase)}</h2>
          <div class="viewer">${renderFrames(item)}</div>
          <div class="facts-readout">${escapeHtml(item.facts_summary)}</div>
        </div>

        <div class="panel">
          <h2>Drafted item</h2>
          <textarea class="q-text" id="q-input">${escapeHtml(item.question)}</textarea>
          <div class="options">
            ${letters.map((L) => `
              <div class="option-row ${item.correct_answer === L ? "is-answer" : ""}">
                <input type="radio" name="answer" value="${L}" ${item.correct_answer === L ? "checked" : ""} data-role="answer-radio">
                <input type="text" value="${escapeHtml(item.options[L])}" data-role="option-text" data-letter="${L}">
              </div>`).join("")}
          </div>
          <div class="rationale">
            ${escapeHtml(item.distractor_rationale)}
            <span class="conf-badge ${item.distractor_confidence}">${escapeHtml(item.distractor_confidence)} confidence</span>
          </div>
          <textarea class="notes" id="notes-input" placeholder="Review notes (required to reject)">${escapeHtml(item.review_notes)}</textarea>
          <div class="actions">
            <button class="btn-approve" data-action="approve" ${actionsDisabled ? "disabled" : ""}>Approve</button>
            <button class="btn-edit" data-action="edit-approve" ${actionsDisabled ? "disabled" : ""}>Save edits &amp; approve</button>
            <button class="btn-reject" data-action="reject" ${actionsDisabled ? "disabled" : ""}>Reject</button>
          </div>
        </div>
      </div>

      <div class="navbar">
        <button class="btn-ghost" id="prev-btn" ${cursor === 0 ? "disabled" : ""}>← Previous</button>
        <select id="jump-select">
          ${list.map((q, i) => `<option value="${i}" ${i === cursor ? "selected" : ""}>${escapeHtml(q.patient_id)} — ${escapeHtml(q.phase_abbr)} (${escapeHtml(q.review_status)})</option>`).join("")}
        </select>
        <button class="btn-ghost" id="next-btn" ${cursor === list.length - 1 ? "disabled" : ""}>Next →</button>
      </div>
    `;
    document.getElementById("app").innerHTML = html;
    wireEvents(item);
    autoSizeQuestion();
  }

  function autoSizeQuestion() {
    // The reviewer must see the FULL question with no internal scrolling —
    // a fixed min-height textarea can clip a long question behind a
    // scrollbar. Grow it to fit its content instead.
    const el = document.getElementById("q-input");
    if (!el) return;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }

  function wireEvents(item) {
    document.getElementById("reviewer-name").addEventListener("change", (e) => {
      state.reviewerName = e.target.value;
      saveLocalState();
    });
    document.getElementById("prev-btn").addEventListener("click", () => { cursor--; render(); });
    document.getElementById("next-btn").addEventListener("click", () => { cursor++; render(); });
    document.getElementById("jump-select").addEventListener("change", (e) => {
      cursor = parseInt(e.target.value, 10); render();
    });
    document.getElementById("q-input").addEventListener("input", autoSizeQuestion);
    document.querySelectorAll('[data-action]').forEach((btn) => {
      btn.addEventListener("click", () => handleAction(item, btn.dataset.action));
    });
    document.getElementById("download-btn").addEventListener("click", downloadReviewFile);
    document.getElementById("load-file-input").addEventListener("change", handleLoadFile);
  }

  function collectFieldValues(item) {
    const question = document.getElementById("q-input").value;
    const notes = document.getElementById("notes-input").value;
    const answerRadio = document.querySelector('[data-role="answer-radio"]:checked');
    const answer = answerRadio ? answerRadio.value : item.correct_answer;
    const options = {};
    document.querySelectorAll('[data-role="option-text"]').forEach((inp) => {
      options[inp.dataset.letter] = inp.value;
    });
    return { question, options, answer, notes };
  }

  function handleAction(item, action) {
    const { question, options, answer, notes } = collectFieldValues(item);

    if (action === "reject" && !notes.trim()) {
      showBanner("A reject reason is required — add a note first.", "err");
      return;
    }

    item.question = question;
    item.options = options;
    item.correct_answer = answer;
    item.review_notes = notes;
    item.reviewer = state.reviewerName;

    if (action === "approve") item.review_status = "approved";
    else if (action === "edit-approve") item.review_status = "edited";
    else if (action === "reject") item.review_status = "rejected";

    saveLocalState();
    render();
  }

  function buildFullHtml(newState) {
    // Structural regex replacement, NOT literal-placeholder-string matching:
    // the placeholder text itself must never appear as a JS string literal
    // in this function, or Python's one-time generation-time substitution
    // (a blanket .replace() over the whole page source) would corrupt this
    // very call site too, breaking every re-download after the first.
    const fullDoc = atob(TEMPLATE_B64);
    const safeData = JSON.stringify(newState).replace(/<\/script/gi, "<\\/script");
    const withData = fullDoc.replace(
      /(<script id="lumiere-data" type="application\/json">)[\s\S]*?(<\/script>)/,
      (_, open, close) => open + safeData + close
    );
    return withData.replace(
      /(const TEMPLATE_B64 = ")[^"]*(";)/,
      (_, open, close) => open + TEMPLATE_B64 + close
    );
  }

  function saveLocalState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // private-browsing / quota — progress just won't survive a reload;
      // downloading still works, so nothing is lost if they download often.
    }
  }

  function loadLocalState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (saved && Array.isArray(saved.items) && saved.items.length === state.items.length) {
        state.items = saved.items;
        state.reviewerName = saved.reviewerName || state.reviewerName;
      }
    } catch (e) {
      // corrupt/foreign localStorage value — ignore, start from the shipped state.
    }
  }

  function downloadReviewFile() {
    try {
      const html = buildFullHtml(state);
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "lumiere_chain_review.html";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 4000);
      showBanner("Downloaded — send this file back when you're done (or keep going; progress also autosaves in this browser).", "ok");
    } catch (e) {
      showBanner("Download failed: " + (e && e.message ? e.message : e), "err");
    }
  }

  function handleLoadFile(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const m = /<script id="lumiere-data" type="application\/json">([\s\S]*?)<\/script>/.exec(reader.result);
        if (!m) throw new Error("no review data found in that file");
        const loaded = JSON.parse(m[1]);
        if (!Array.isArray(loaded.items) || loaded.items.length !== state.items.length) {
          throw new Error("that file doesn't match this item set");
        }
        state.items = loaded.items;
        state.reviewerName = loaded.reviewerName || state.reviewerName;
        saveLocalState();
        cursor = firstPendingIndex(sortedItems());
        render();
        showBanner("Loaded review file.", "ok");
      } catch (err) {
        showBanner("Could not load that file: " + err.message, "err");
      }
    };
    reader.readAsText(file);
  }

  loadLocalState();
  cursor = firstPendingIndex(sortedItems());
  render();
})();
</script>
'''


def build() -> None:
    state = build_state()
    page_src = "<!doctype html>\n<html><head><meta charset=\"utf-8\"></head><body>\n" + INNER_CONTENT + "\n</body></html>"
    template_b64 = base64.b64encode(page_src.encode("utf-8")).decode("ascii")

    # Guard against "</script" appearing literally inside drafted text (e.g. a
    # question mentioning markup) — the HTML parser ends a <script> element at
    # that byte sequence regardless of JSON semantics. "\/" is a valid JSON
    # escape for "/", so this round-trips correctly through JSON.parse().
    data_json = json.dumps(state).replace("</script", "<\\/script").replace("</SCRIPT", "<\\/SCRIPT")

    # OUT_PATH is now a complete, standalone document — the reviewer opens it
    # directly (double-click / drag into a browser), no server or account
    # involved — so it must include the doctype/html/head/body wrapper, not
    # just the inner content (that bare-content shape was only needed for the
    # old claude.ai Artifact tool, which wrapped it itself).
    final_doc = (
        page_src
        .replace("@@LUMIERE_TEMPLATE@@", template_b64)
        .replace("@@LUMIERE_DATA@@", data_json)
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(final_doc, encoding="utf-8")
    size_mb = OUT_PATH.stat().st_size / 1e6
    print(f"Wrote {OUT_PATH} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    build()
