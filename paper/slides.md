# Omnibrain / KAB — Progress Update for Prof. Wang
Content outline for slides (design pass to follow separately)

---

## Slide 1 — Title

**Knowledge Alignment Benchmarking (KAB) for Multimodal Clinical Reasoning**
Causal-chain evaluation of MLLMs on brain-MRI diagnostic reasoning

Taiwo Olabamipe | Prof. Song Wang, UCF | Progress update — 2026-09-07

---

## Slide 2 — Background

- Multimodal LLMs (MLLMs) are increasingly being evaluated on medical imaging tasks.
- Almost every existing benchmark only scores **final-answer accuracy** — right option vs. wrong option.
- Accuracy alone can't tell the difference between three very different (and clinically distinct) behaviors:
  1. The model reasoned correctly.
  2. The model pattern-matched the question text.
  3. The model guessed, or produced reasoning that contradicts its own answer.
- In a clinical setting, (2) and (3) are dangerous even when the model happens to be "right" — they don't generalize to novel cases.
- **Our question:** can we measure whether a model's reasoning is trustworthy, not just whether its final answer is correct?

---

## Slide 3 — Problem Setting: OmniBrainBench

- Dataset: **OmniBrainBench** (HuggingFace: `FrankPN/OmniBrainBench`) — 6,823 MCQs on real brain-MRI cases.
- Questions are organized into **5 clinical phases**, mirroring how a radiologist actually works through a scan, in a fixed causal order:

  **AIA → LIL → DSCR → PJRF → TCM**

| Phase | Meaning | Clinical Question | # Questions |
|---|---|---|---|
| AIA | Anatomical & Imaging Assessment | What scan is this? What anatomy is visible? | 2,048 |
| LIL | Lesion Identification & Localization | Is there a lesion? Where, and what does it look like? | 2,797 |
| DSCR | Diagnostic Synthesis & Causal Reasoning | What's the diagnosis? What caused these findings? | 1,845 |
| PJRF | Prognostic Judgment & Risk Forecasting | How will this progress? What's the risk? | 64 |
| TCM | Therapeutic Cycle Management | What's the treatment plan? | 51 |

- **Design intuition:** a model that nails the diagnosis (DSCR) but described the wrong anatomy in AIA isn't reasoning — it's guessing or pattern-matching. The phase structure is built to catch exactly that.
- Note: PJRF and TCM are <1% of the dataset each — reported separately with confidence intervals, not pooled with the larger phases (pooling would hide the degradation signal we care about).

---

## Slide 4 — The KAB Framework: What We Add on Top of Accuracy

KAB evaluates three dimensions beyond right/wrong:

1. **Faithfulness** — does the model's stated reasoning actually support its answer, and is it grounded in real clinical vocabulary?
2. **Feedback-Adaptation** — when shown the clinical concepts it missed, can the model self-correct?
3. **Soft Gating** — does the causal chain hold together? A model that fails an early phase is blocked from later ones (mirrors real diagnostic dependency).

---

## Slide 5 — Evaluation Metrics (1/2): Faithfulness

**Local Faithfulness**
- After the model answers, we run a *second* call — the "faithfulness probe" — showing the model **only its own reasoning text** (no image, no question, no options) and ask which answer that reasoning supports.
- Match → locally faithful. Mismatch → the model's stated justification doesn't reflect why it actually answered that way.
- **"Correct-but-unfaithful"** is tracked as its own flag — right answer, wrong/disconnected reasoning. This is the most clinically dangerous category: it won't generalize to a case that's even slightly different.

**KB Alignment Score** (central KAB metric)
- Checks whether the clinical terms a model uses are real terms from the *phase-appropriate* knowledge base:
  - AIA / LIL → **RadLex** (radiology anatomy & imaging descriptors)
  - DSCR / PJRF / TCM → **NCIt** (tumor biology, grading, staging, treatment)
- Pipeline: tokenize model output → greedy longest-match scan against the KB (tries 4-grams down to 1-grams, no token reuse) → `kb_alignment_score = matched_concepts / extracted_concepts`.
- Low score = model isn't using the vocabulary appropriate to the current diagnostic phase (e.g. still describing anatomy at the diagnosis phase).

**Concept Precision Score**
- Of the KB terms the model correctly used, how many are actually *on-target* for this specific case (i.e., appear in the correct answer)?
- Distinguishes "used real medical language" from "used the *right* real medical language."

---

## Slide 6 — Evaluation Metrics (2/2): Adaptation & Gating

**Chain Faithfulness**
- Cross-phase reasoning continuity — does the reasoning at phase *N* stay consistent with what was established at phase *N–1*?

**Feedback-Adaptation Rate**
- Triggered when a response is KB-unfaithful *and* has missed concepts.
- We inject the missed clinical concepts and re-run the question.
- Adaptation rate = how often that correction actually fixes the answer.
- Tests whether a model can be steered with targeted feedback, not just whether it's right the first time.

**Soft Gating**
- A phase is blocked ("gated out") unless every upstream phase met a minimum threshold.
- AIA is always unlocked (no upstream). Blocked phases show as `GateBlk` in reports.
- Operationalizes the idea that diagnosis without correct anatomy/lesion localization isn't real reasoning — it's disqualified from being scored as if it were.

**Failure Taxonomy** (per response, for qualitative analysis)
- Perception failure / Reasoning failure / Decision-making failure / Correct-but-unfaithful.

---

## Slide 7 — Model Running Setup

**10 models, 3 categories:**

| Category | Models | Serving |
|---|---|---|
| Proprietary | GPT-5, Claude-4.5-Sonnet, Gemini-2.5-Pro | Direct API / LiteLLM proxy |
| Medical-domain | HuatuoGPT-V-34B, Lingshu-32B, Llava-Med-7B, MedGemma-4B | Ollama (small) / vLLM (large) |
| Open-source general | Qwen3-VL-30B, InternVL3-38B, Qwen2.5-VL-7B | Ollama / vLLM |

*(DeepSeek and Janus-Pro-7B dropped — DeepSeek not permitted on our institutional cluster, as API or open-weight source.)*

**Infrastructure:** UF HiPerGator (`hpg-turin`, L4 GPUs; `hpg-b200` for the largest models)
- All serving/inference goes through SLURM — nothing runs on login nodes.
- Large open-weight models (30B–38B) need vLLM tensor-parallelism; a single 22.5GB L4 isn't enough — **still an open hardware problem** for the biggest models (Qwen3-VL-30B, InternVL3-38B, HuatuoGPT-V-34B, Lingshu-32B).
- Storage: model weights, HF cache, and Python venv all redirected to group `/blue` storage (home quota is only 40GB).
- Pipeline status: 7 of 10 models have been smoke-tested end-to-end on HiPerGator (main call → faithfulness probe → KB alignment → soft gating → adaptation loop all producing valid output). Proprietary models (GPT-5, Claude, Gemini) not yet run. No results are being reported yet — see next slide for why.

---

## Slide 8 — Known Issue: Chain Validity

- The 5-phase structure implies each case is one **patient's journey** through AIA → TCM.
- **Problem found:** OmniBrainBench's phase-to-case grouping (`source_file`) does not actually track same-patient identity — only **2 of 6,823** questions form a genuine same-patient multi-phase pair.
- This undermines the paper's central claim (reasoning degrades across a patient's causal chain) — the phase-linked "chains" the pipeline currently scores are largely *not* real chains.
- Flagged to Prof. Wang 2026-08-21/22; **discussed and a fix approved 2026-08-26.**

---

## Slide 9 — Fix in Progress: LUMIERE Chain Dataset

- Building a **genuine same-patient longitudinal chain dataset** from **LUMIERE** (91 real longitudinal GBM patients — real multi-timepoint imaging, RANO response, survival, Stupp-protocol treatment).
- Approach: **hybrid LLM-draft + domain-expert review**
  - Facts extracted per patient per phase (imaging, lesion, diagnosis, prognosis, treatment) directly from LUMIERE's data, with full provenance — no manual registration needed (segmentations already MNI-aligned; volumes precomputed).
  - Claude-4.5-Sonnet drafts MCQ items per phase from those facts.
  - A radiologist/neuro-oncologist collaborator reviews and corrects every item before it's used.
- **Status:** 54/55 eligible patients extracted, **269 MCQ items drafted, all schema-valid.** Review interface built and tested (standalone HTML file — no cluster or Claude account needed on the reviewer's side). **Currently waiting on the expert's actual review pass** — pipeline has nothing left to build until that's done.
- Two real bugs caught and fixed during construction (both would have silently biased the dataset):
  - Naive "last timepoint" sampling made almost every DSCR answer "progressive disease" (GBM patients trend toward PD) — fixed with random eligible-timepoint sampling. Real spread: PD 37 / SD 9 / PR 4 / CR 4.
  - A timepoint could have a RANO rating without matching imaging, silently describing two different dates — fixed by constraining to timepoints with both.

**This also strengthens the paper's contribution:** once chains are real, we're (to our knowledge) the first benchmark combining genuine same-patient continuity with a full imaging→diagnosis→prognosis→treatment question layer — checked against every candidate dataset we could find (OmniBrainBench, NeuroQA, LUMIERE, MU-Glioma-Post, UCSF-ALPTDG, UCSD-PTGBM).

---

## Slide 10 — Current Status Summary

**Done**
- KAB framework fully implemented (faithfulness, KB-alignment, adaptation, soft-gating) and running end-to-end.
- 10-model eval config built; 7 of 10 models smoke-tested successfully on HiPerGator.
- LUMIERE chain-dataset pipeline built and validated; 269 real-chain MCQ items drafted and awaiting expert review.

**Not yet done**
- Full-scale evaluation run (all 10 models × full dataset) — blocked on: (a) expert review completing the LUMIERE chain set, since that's what we want to report on; (b) hardware plan for 30B+ models.
- Proprietary models (GPT-5/Claude/Gemini) not yet run through the pipeline.
- Guided-JSON re-test for Llava-Med-7B before its near-zero score is reported as a finding.

**Open problems to flag to Prof. Wang**
- 30B+ model hardware: single L4 (22.5GB) insufficient even with tensor-parallel=2; needs `hpg-b200` and/or quantization plan — unsolved.
- KB-vocabulary-matching is a blunt grounding metric (string/n-gram match, not semantic) — anticipate reviewer pushback; worth discussing whether to strengthen it before submission.
- Target venue: NAACL 2027 (tentative) — CFP details not yet reviewed.

---

## Slide 11 — Next Steps

1. Get expert review pass on the 269 LUMIERE items back → merge → re-run smoke test on the real chain data.
2. Resolve 30B+ model hardware plan (b200 / quantization).
3. Run proprietary models (GPT-5, Claude, Gemini) through the pipeline.
4. Guided-JSON re-test on Llava-Med-7B.
5. Full-scale run across all 10 models on the LUMIERE chain set once available.
