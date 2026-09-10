#Project Update

## 2026-09-07 — Llava-Med-7B guided-JSON re-test: still degenerates, stronger finding now

Ran the guided-JSON re-test flagged 2026-08-25 as required before reporting
Llava-Med-7B's near-zero score as a finding. Added `--guided-json` to
`run_omnibrain.py`/`src/evaluator.py` (passes `extra_body={"guided_json":
schema}` to vLLM's OpenAI-compatible endpoint, forcing token-level structured
output; new `ANSWER_RESPONSE_SCHEMA`/`FAITHFULNESS_RESPONSE_SCHEMA` in
`src/prompts.py`). Ran on `hpg-turin` (SLURM job 41296339, ~3 min) against
the same AIA-phase question set as the original 2026-08-21 run.

**Result: 0/25 AIA questions answered — same as unconstrained decoding.**
All 25 requests returned `200 OK` from the vLLM server (confirmed in
`.scratch/vllm_serve_Llava-Med-7B.log` — no server-side errors, no rejected
requests), but every response body was an empty string. This is a cleaner
result than the original test: it's not a malformed-JSON parsing failure,
it's the model producing zero content even when the server is enforcing
valid JSON at the decoding level. Ruled out MAX_TOKENS (800, plenty) and
temperature (0.0, greedy) as the cause.

**This lands on the stronger of the two anticipated outcomes** (see
2026-08-25 entry): "not fixable via output-format constraints — no coherent
answer to extract even when forced into valid syntax." The near-zero score
can now be reported as a genuine capability/robustness finding, not an
artifact of prompt/parsing mismatch. Results saved to
`results/Llava-Med-7B-guided-json_20260907_042950/`.

**Not yet done:** re-frame the write-up as a deployment-readiness/robustness
point (per the 2026-08-25 note) rather than a reasoning-quality point when
this goes into the paper draft.

## Target venue: NAACL 2027 (https://2027.naacl.org/)
Confirmed 2026-08-27. CFP details (deadline, page limits, formatting/anonymity
rules) not yet looked up — check the site directly once planning the writing
timeline.

## 2026-08-27 — fixed review-mechanism login wall; reviewer needs no Claude account now

Found a real blocker in the review mechanism built 2026-08-26: it persisted
decisions via the claude.ai `artifact` runtime capability
(`claude.use("artifact") -> publish()`), which requires the *viewer* to be
signed into a Claude account to write. The actual reviewer (radiologist/
neuro-oncologist collaborator) doesn't have one — they hit a login wall
trying to save. Evidence in the artifact's saved state: one item
(Patient-091_DSCR) was left `"review_status": "edited"` with an empty
`reviewer` field — a save that started but couldn't complete.

**Fix:** `tools/build_lumiere_review_artifact.py` now generates a fully
standalone `.html` file with no server/account dependency at all — every
approve/edit/reject autosaves to the reviewer's own browser via
`localStorage`, and a "Download review file" button produces an updated,
self-contained `.html` they email back (or a "Load review file…" picker to
resume from a previously downloaded one on another machine). Rebuilt and
verified: valid standalone document, no leftover `window.claude` references,
`tools/sync_lumiere_artifact_review.py` round-trips against it unchanged
(that script never actually needed the Artifact tool — it only ever
regex-parsed the `lumiere-data` script tag out of whatever HTML file it's
pointed at).

**Next step:** send `tools/lumiere_review_artifact.html` directly to the
reviewer (email attachment or a shared-drive direct-download link — NOT the
old claude.ai Artifact link, which is now superseded/stale) and have them
open it locally. Once they send back a completed download, sync with:
`python -m tools.sync_lumiere_artifact_review --html-file <path>` ->
`tools/lumiere_merge_reviewed.py` -> `run_lumiere.py` smoke test. No agent/
Claude Code session needs to be involved in the sync step anymore.

## ✅ DECIDED (2026-08-26) — professor approved LUMIERE + hybrid LLM/expert build

**Decision made.** Professor has approved option 3: build a real same-patient chain
dataset on LUMIERE (91 real GBM patients) using the hybrid LLM-draft +
domain-expert-review pipeline described below. This resolves the
chain-validity/construct-validity issue that was blocking the paper's core causal-
degradation claim (see investigation detail below for the original problem).

**Immediate next steps now unblocked:**
- Confirm radiologist/neuro-oncologist collaborator availability for the review step
  (still open — materially affects timeline).
- Pull LUMIERE's actual data dictionary/access process to confirm exact available
  fields before designing the phase-to-field extraction pipeline.
- Design the per-phase MCQ generation pipeline (fact extraction -> LLM draft -> expert
  review) and the review interface/format for the domain expert.

Full investigation, feasibility breakdown, and other options considered are preserved
below for context.

**Phase-by-phase feasibility (LLM-draftable vs. needs expert review), candidate = LUMIERE:**
- AIA / LIL — near-programmatic: LUMIERE ships per-timepoint tumor segmentation
  masks, so location/volume/volume-change facts are computable directly (atlas
  registration + voxel counts), not really "annotation."
- DSCR — LUMIERE already includes expert-assigned RANO response labels
  (progression/stable/partial/complete response) per follow-up scan — existing
  expert ground truth, not new annotation.
- PJRF (prognosis) — survival data is structured, but plausible-but-wrong distractors
  need someone who knows GBM prognostic literature; LLM-only distractors risk being
  trivially or misleadingly wrong.
- TCM (treatment) — Stupp protocol is templatable, but real judgment questions
  (progression vs. pseudoprogression, a well-known confound even for radiologists)
  need expert review of the answer key, not just LLM drafting.

**Rough effort estimate:** ~20–30 chains (patients) × 5 phases ≈ 100–150 items;
~10–15 min expert review per item (checking answer key + distractor plausibility,
esp. PJRF/TCM) ≈ **20–35 hours of expert time** for a first pass. Full 91-patient
LUMIERE cohort would scale to roughly 90–150 hours.

**Open sub-question, not yet resolved:** whether Prof. Wang's group already has a
radiologist/neuro-oncologist collaborator lined up for the review step, or whether
that access still needs to be arranged — materially affects timeline, not yet answered.

---

## Investigation detail (raised 2026-08-21/22, discussion ongoing above)

**Problem: OmniBrainBench does not actually support the causal-chain premise the KAB
framework is built on.** The framework evaluates a model through 5 sequential phases
(AIA → LIL → DSCR → PJRF → TCM) for *the same patient*, gating later phases on earlier
ones. Investigated the real dataset structure directly and found:

- Checked whether any image is shared across questions tagged with different clinical
  phases — the only way "same patient, multiple phases" could be genuinely true.
- Out of 6,823 total questions across 15 source sub-corpora (PubMedVision, MedXpert,
  RSNA, BraTS2021, ISLES2022, RadImageNet, VQA_RAD, NOVA, NEJMIC, Br35h, baby_brain,
  BraTS2023-MEN/MET, fastMRI, TCP, NOVA), only **2 questions** genuinely share a
  same-patient image across two different phases (both from VQA_RAD, AIA+LIL only).
- Re-verified with a second, more rigorous method: extracted real per-patient case IDs
  by stripping known modality/view/slice suffixes from filenames per corpus (e.g.
  `BraTS2021_00006_flair/t1/t1ce/t2` → case `BraTS2021_00006`; `ID_xxx_original/lung/
  bone` → case `ID_xxx`; `sub-strokecase0001_ses-0001_adc/dwi/FLAIR` → same case).
  Result: still only **2 genuine multi-phase same-patient cases in the entire
  dataset**, 2 phases each. Zero span 3+ phases. Zero span all 5.
- Root cause: each of the 15 source sub-corpora was built for one specific clinical
  task (BraTS → tumor characterization, RSNA → hemorrhage classification, ISLES →
  stroke, etc.), so a given real patient in that corpus is essentially only ever asked
  *one* phase-type of question, never a full multi-phase battery.
- What the current pipeline calls a "case" (`source_file` grouping, only 10 usable
  under `min-phases=2`) is really **one whole origin sub-corpus** standing in for one
  patient — the "chain" evaluated is stitched from *different real patients'*
  questions within that corpus, not one patient's actual journey. When a model gets
  "gated out" of DSCR after failing AIA, that's an artifact of this aggregation, not a
  demonstration of causal degradation for one patient.

**Searched for a replacement/supplementary dataset with genuine same-patient,
multi-phase continuity — none exists ready-to-use:**

| Dataset | Real same-patient continuity? | Covers prognosis/treatment? | Ready-made QA layer? |
|---|---|---|---|
| OmniBrainBench (current) | No (2 cases in 6,823 questions) | Nominally yes, not linked to real chains | Yes |
| [NeuroQA](https://neuroqa.stanford.edu) (56,953 QA / 12,977 subjects, incl. BraTS-GLI/MEN) | Partial (a "Longitudinal" category = 2 timepoints, not a full chain) | **Explicitly excluded by design** — paper states it's "not intended to support claims about...treatment planning" | Yes |
| [UCSF-PDGM-VQA](https://arxiv.org/abs/2605.17140) (2,387 QA / 473 studies) | No — single timepoint only | No | Yes |
| [LUMIERE](https://www.nature.com/articles/s41597-022-01881-7) (91 real GBM patients) | **Yes** — real longitudinal MRI, RANO response assessment, survival, Stupp-protocol treatment | **Yes** | **No** — raw imaging + clinical data only, no questions |
| [MU-Glioma-Post](https://www.cancerimagingarchive.net/collection/mu-glioma-post/) (203 patients, 617 post-treatment timepoints) | **Yes** | **Yes** (treatment + genomic data) | **No** — segmentation/clinical data, no questions |

**The honest conclusion:** no published benchmark currently provides genuine
same-patient continuity across a full imaging → diagnosis → prognosis → treatment
arc. The datasets with real clinical continuity (LUMIERE, MU-Glioma-Post) have no
question layer; the datasets with questions (OmniBrainBench, NeuroQA) don't have the
continuity, and NeuroQA's authors explicitly disclaim prognosis/treatment support.

**Options on the table, not yet decided:**
1. Build a modest MCQ layer on top of LUMIERE ourselves (~91 real patients available;
   even 20-30 annotated chains would be a genuine, defensible causal-chain dataset —
   something that doesn't currently exist elsewhere). More work, but produces a real
   contribution instead of working around a construct-validity gap.
2. Drop the full 5-phase same-patient chain claim; pivot to per-phase KAB evaluation
   at much larger scale (NeuroQA for AIA/LIL/DSCR-equivalent phases, existing sources
   for whatever prognosis/treatment questions exist standalone) — keeps the KB-
   alignment and feedback-adaptation contributions, loses the causal-chain narrative.
3. Keep researching other TCIA collections (TCGA-GBM/LGG, etc.) for something closer
   to ready-to-use before committing to option 1's build effort.

**User's call (2026-08-21): flag this to the professor before proceeding further —
this affects the paper's core framing, not just an implementation detail.**

---

## What Was Presented

In the meeting, I walked the professor through two things I had worked out since the last discussion:

### 1. Knowledge Base Selection (RadLex + NCIt)

I explained why I chose **RadLex** and the **NCI Thesaurus (NCIt)** as the two knowledge bases for the Knowledge Alignment Benchmarking framework — and specifically why I did not go with UMLS.

**RadLex** (RSNA, ~46k radiology-specific terms, OWL + CSV):
- The only KB built exclusively for radiology
- 71% of OmniBrainBench questions sit in AIA and LIL phases — imaging observation and lesion localization — which is exactly what RadLex covers
- When the model describes something like "FLAIR hyperintensity in the left temporal lobe," RadLex is the authoritative source to validate that claim

**NCI Thesaurus / NCIt** (NIH NCI, ~170k concepts, public domain):
- OmniBrainBench is predominantly a brain tumor dataset (glioma, glioblastoma, meningioma dominate)
- NCIt has the deepest coverage of brain tumor biology, WHO grading (Grade I–IV), staging, and treatment protocols of any freely available KB
- Preferred over UMLS because NCIt is more specific to the tumor cases that actually appear in the dataset, and it is public domain with a direct download — no account or API key required, which removes a reproducibility barrier for reviewers

The two KBs divide cleanly along the perception/reasoning boundary already in the framework:
- AIA + LIL → RadLex
- DSCR + PJRF + TCM → NCIt

### 2. Knowledge Alignment Benchmarking (KAB) and Feedback-based Adaptation Loop

I explained how I understand the KAB framework:

**KAB** replaces the current vocabulary-matching grounding metric with real KB concept alignment. Instead of checking whether a hardcoded word like "lesion" appears in the output, we:
1. Extract clinical concepts from the model's `reasoning` and `visual_grounding` fields
2. Cross-reference those concepts against the appropriate KB for that phase
3. Compute a **KB Alignment Score** (proportion of stated concepts that are valid KB entries) and a **Concept Precision Score** (are the KB concepts consistent with the correct answer?)

**Feedback-based Adaptation Loop** — what happens when a phase produces unfaithful output:
1. Retrieve the KB concept(s) the model missed or misused
2. Inject them as a structured clinical knowledge correction into the prompt
3. Re-run the phase
4. Measure whether the model self-corrects — **Adaptation Rate**

---




# Status Log

This section is a running log of project status, kept current so the project can be
picked back up cold after any gap. Newest entry on top.

## 2026-08-26 (latest) — full 55-patient batch drafted; expert-review artifact live

Since the previous entry: expanded from the initial 30-patient target to the
**full 55-patient eligible cohort** (54 successfully extracted/drafted — one,
Patient-025, has no timepoint with both a real RANO rating and complete
imaging) so the expert reviews everything in one pass. Added idempotency
guards to `lumiere_facts.extract_all()`/`lumiere_drafter.draft_all()` so
re-running against the expanded list doesn't redo the original 29 patients'
work or re-spend API credit — confirmed working (a mid-run LiteLLM proxy
outage caused one bad batch of empty drafts for the 25 new patients; the
guard correctly detected empty `[]` files as "not actually done" and retried
only those on the next run, not the whole set).

**Result: 269 MCQ items across 54 patients, all schema-valid.**

**Review mechanism changed from the Streamlit app to a published Artifact**,
since the actual reviewer (a radiologist/neuro-oncologist collaborator) is
not technical — SSH port-forwarding into a HiPerGator login node was a
non-starter. Built `tools/build_lumiere_review_artifact.py`, which bundles
all 269 items + 108 slice images (base64-embedded, ~2.5MB total) into one
self-contained page using the `artifact` runtime capability (reviewer
actions call `publish()`, persisting decisions server-side, readable back
later — no cluster/terminal access needed at all for the reviewer).

**Review link (durable — works independently of any Claude Code session
being open; check by re-reading this URL from any future session):**
https://claude.ai/code/artifact/af930975-d647-4f59-89f1-df1840384877

Self-tested in a real browser (not just static validation) — confirmed
`publish()` actually persists across reloads (4 test approvals landed and
were readable back). Iterated once on UX feedback: added a prominent
"N / 269 reviewed" progress counter + bar (was previously buried in small
text) and a "Saving…" disabled-button state during publish (previously no
loading feedback at all).

**Update (same day, later):** built and tested `tools/sync_lumiere_artifact_review.py`
end-to-end (Artifact `read` -> sync -> `merge_reviewed()` -> `build_lumiere_cases()`,
simulated a fully-approved patient to confirm a complete 5-phase case builds
correctly). Also caught and fixed a schema gap: the artifact's item data was
missing `task_label` (required by `build_lumiere_cases()`) — fixed in
`tools/build_lumiere_review_artifact.py`, artifact republished with the fix
(same link, resets to all-269-pending — no real review data existed yet, so
nothing lost).

**Current state: fully built and ready for the actual expert reviewer.**
Nothing left to do until they complete their pass — then:
`python -m tools.sync_lumiere_artifact_review --html-file <path from Artifact
read>` -> `tools/lumiere_merge_reviewed.py` -> `run_lumiere.py` smoke test.

## 2026-08-26 (later) — LUMIERE pipeline built through fact extraction; blocked on API key for drafting

Built the full LUMIERE ingestion pipeline (config/lumiere.py,
src/lumiere_downloader.py, src/lumiere_facts.py, src/lumiere_prompts.py,
src/lumiere_drafter.py, src/lumiere_loader.py, tools/lumiere_review_app.py,
tools/lumiere_merge_reviewed.py, run_lumiere.py — see CLAUDE.md's new LUMIERE
section for the technical detail). Verified real access via the Figshare API
(collection DOI 10.6084/m9.figshare.c.5904905.v1) and confirmed the actual
per-patient folder layout from the readme PDF and a live zip listing.

**Progress so far:**
- Selected 30 target patients by real multi-timepoint RANO coverage (>=3
  response-rated follow-ups); 29 had complete-enough data to extract.
- Extracted per-patient facts (AIA/LIL/DSCR/PJRF/TCM) with full provenance —
  no registration step needed (DeepBraTumIA's atlas-space masks are already
  MNI-aligned; precomputed volume JSONs ship with the dataset).
- **Caught and fixed a real bug during build**: picking each patient's LAST
  RANO-rated timepoint made every DSCR answer "progressive disease" (GBM
  patients almost always end on PD before their final scan) — would have
  made the DSCR phase trivially guessable. Fixed by sampling a random
  eligible timepoint per patient; real distribution now PD 20 / SD 6 / CR 2 / PR 1.
- Spot-checked chain coherence across all 29: volume-change direction vs.
  RANO label, and survival-week vs. followup-week ordering, both consistent
  except one flagged case (Patient-073, survival predates its sampled
  followup timepoint) — left flagged for expert attention, not silently fixed.
- Rendering slice PNGs (bridges LUMIERE's 3D NIfTI to the evaluator's 2D image
  loader) — in progress as of this entry.

**Blocked:** `OPENAI_API_KEY` (or another proprietary model's credentials) is
not set in this environment — needed for the LLM-drafting step
(src/lumiere_drafter.py) before expert review can start.

**Not yet done:** LLM drafting, expert review (radiologist/neuro-oncologist
collaborator availability still unconfirmed — see below), final merge, and
the run_lumiere.py smoke test against the existing evaluator.

## 2026-08-26 — professor approved LUMIERE + hybrid LLM/expert build

Professor's decision is in: proceed with option 3 — build a real same-patient causal
chain dataset on LUMIERE (91 real GBM patients) using the hybrid LLM-draft +
domain-expert-review pipeline (see feasibility breakdown at top of file). This
resolves the chain-validity issue flagged 2026-08-21/22 and unblocks the paper's core
causal-degradation claim. Next: confirm radiologist/neuro-oncologist collaborator
availability, pull LUMIERE's actual data dictionary, and design the per-phase MCQ
generation pipeline + expert review interface.

## 2026-08-25 — chain-validity issue: discussing hybrid LLM+expert build with professor (not yet decided)

Professor is asking, in-meeting, about the feasibility of the chain-validity open
issue's option 3: build a real same-patient chain dataset ourselves (candidate:
LUMIERE, 91 real GBM patients, genuine longitudinal imaging + RANO response +
survival + Stupp-protocol treatment), using a hybrid LLM + domain-expert pipeline.
User confirmed the approach shape is hybrid (LLM drafts, expert reviews/corrects) —
**this is the professor's live question, not a finalized decision.** See top of file
for the full feasibility breakdown prepared to answer it (phase-by-phase LLM vs.
expert-review split, ~20-35 expert hours estimated for a first pass of ~20-30 chains,
~90-150 hours for the full cohort).

**Not yet done / next steps:**
- ~~Get the professor's actual decision on whether to proceed with LUMIERE + this
  approach, or a different direction.~~ **DONE (2026-08-26): approved, see top of file.**
- Confirm whether a radiologist/neuro-oncologist collaborator is already available
  for the expert-review step, or needs to be arranged — blocks timeline planning.
- Pull LUMIERE's actual data dictionary/access process to confirm exact available
  fields (segmentation format, RANO label schema, survival/treatment fields) before
  designing the phase-to-field extraction pipeline.
- Design the per-phase MCQ generation pipeline (fact extraction -> LLM draft -> expert
  review) and a review interface/format for the domain expert, once approved.
- Decide on adding Qwen2.5-VL-3B (Ollama `qwen2.5vl:3b`) to `config/models.py` /
  `shell/run_opensource.sh` — gives MedGemma-4B a matched-scale general-model pair.
  Not yet added, pending go-ahead.
- **Before reporting Llava-Med-7B's near-zero score as a finding**: re-test it with
  vLLM's guided/structured-output decoding (`guided_json`) enabled. Currently the
  "cannot produce valid JSON under instruction" claim is only tested at greedy
  decoding with the standard prompt — a reviewer will ask whether constrained
  decoding fixes it. Two outcomes both usable: still degenerates under guided
  decoding -> stronger claim ("not fixable, no coherent answer to extract even when
  forced into valid syntax"); works under guided decoding -> different, still-useful
  finding ("needs structured-output tooling most deployment pipelines don't
  provide") — but then the near-zero number must be updated, not kept as-is. Also
  reframe the write-up as a deployment-readiness/robustness point, not a
  reasoning-quality point, when this goes into the paper.




## POSSIBLE CONTRIBUTION


1. A new benchmark that doesn't currently exist. No published dataset has both genuine same-patient continuity and a full imaging→diagnosis→prognosis→treatment question layer — we confirmed this by process of elimination across every candidate (OmniBrainBench, NeuroQA, LUMIERE, MU-Glioma-Post, UCSF-ALPTDG, UCSD-PTGBM). Building the LUMIERE-based chain set makes us the first to have one. That's a standalone contributable artifact, independent of anything else in the paper.

2. The causal-degradation finding becomes real, not artifactual. This is the important one. The paper's most novel claim — that model reasoning degrades across clinical phases for the same patient — was previously undermined by the fact that OmniBrainBench's "chains" were stitched from different real patients (2 of 6,823 questions were genuine). Once the chain is built on LUMIERE, that finding is no longer vulnerable to the obvious reviewer objection; it's now measuring what we always claimed it measures.

3. The KAB framework itself — KB-grounded faithfulness + feedback-adaptation. RadLex/NCIt concept-alignment scoring and the feedback-adaptation loop (does the model self-correct when given a structured knowledge correction) were already planned contributions, unaffected by the dataset problem — but they become more meaningful measured on a real causal chain: "did correcting the model at phase 2 actually help phase 4" is only a meaningful question if phase 4 genuinely follows from phase 2 for the same patient.

4. A reusable construction method. The hybrid LLM-draft + targeted-expert-review pipeline (~20–35 expert hours to turn a raw longitudinal clinical dataset into 20–30 validated causal-reasoning chains) is itself worth stating as a methods contribution — it's a cheap, repeatable way to build this kind of benchmark elsewhere, not just a one-off dataset.

<!-- - Professor's decision on LUMIERE + hybrid build — APPROVED 2026-08-26
- Whether a radiologist/neuro-oncologist collaborator is available
- Pull LUMIERE's actual data dictionary before designing the extraction pipeline
- Qwen2.5-VL-3B addition to config/models.py — awaiting go-ahead
- Guided-JSON re-test on Llava-Med-7B before that finding goes in the paper -->