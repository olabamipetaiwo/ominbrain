# OmniBrainBench — Project Documentation

---

## Part 1: What We Are Doing

### Background

Large multimodal language models (MLLMs) are being tested on medical imaging tasks with increasing frequency. Almost every existing benchmark measures only final answer accuracy — it tells you whether the model picked the right option, but not whether it reasoned correctly to get there. A model can select the right answer by pattern-matching the question text, by guessing, or by producing reasoning that is internally inconsistent with its answer. In a clinical setting, all three of these are dangerous.

**OmniBrainBench** is a publicly available benchmark (HuggingFace: `FrankPN/OmniBrainBench`) containing 6,823 multiple-choice questions drawn from real brain MRI cases. Questions are structured into five clinical phases that mirror the actual decision-making workflow of a radiologist or neurologist working through a brain scan.

This project builds an evaluation framework on top of OmniBrainBench — called **Knowledge Alignment Benchmarking (KAB)** — that measures not just whether a model got the right answer, but whether it used the right clinical reasoning to get there, whether it grounded its reasoning in real medical knowledge, and whether it can self-correct when given targeted clinical feedback.

---

### The Five Phases (Causal Chain)

Every case in OmniBrainBench is structured as a causal chain. Questions follow a fixed clinical order and each phase depends on the conclusions from the phases before it:

```
AIA → LIL → DSCR → PJRF → TCM
```

| Abbreviation | Full Name | Clinical Meaning |
|---|---|---|
| AIA | Anatomical and Imaging Assessment | What type of scan is this? What anatomy is visible? Which brain structures are present? |
| LIL | Lesion Identification and Localization | Is there a lesion? Where exactly is it? What are its imaging features? |
| DSCR | Diagnostic Synthesis and Causal Reasoning | What is the diagnosis? What pathological process caused the findings? |
| PJRF | Prognostic Judgment and Risk Forecasting | How will this progress? What is the patient's risk profile? |
| TCM | Therapeutic Cycle Management | What is the treatment plan? Which intervention is most appropriate? |

The causal ordering is deliberate and clinically meaningful. A model cannot reliably answer a DSCR question (diagnosis) without first correctly completing AIA (what anatomy is visible) and LIL (is there a lesion and where). A model that correctly diagnoses glioblastoma in DSCR but described the wrong anatomy in AIA is not actually reasoning — it is pattern-matching or guessing. This is exactly what the framework is designed to detect.

**Phase distribution in the dataset:**

| Phase | Questions |
|---|---|
| AIA | 2,048 |
| LIL | 2,797 |
| DSCR | 1,845 |
| PJRF | 64 |
| TCM | 51 |

---

### Framework Overview: Knowledge Alignment Benchmarking (KAB)

KAB evaluates models on three dimensions beyond accuracy:

1. **Faithfulness** — does the model's reasoning actually support its answer, and does it use real clinical vocabulary?
2. **Feedback-based Adaptation** — when given the clinical concepts it missed, can the model self-correct?
3. **Soft Gating** — does the causal chain hold? A model that fails early phases is blocked from later ones.

---

### Dimension 1: Faithfulness

#### 1a. Local Faithfulness

After the model answers a question, we run a second API call — the **faithfulness probe** — where we show the model only its own reasoning text (no image, no question, no answer choices) and ask: which answer does this reasoning support?

If the predicted answer from the probe matches the model's original answer, the response is **locally faithful** — the reasoning genuinely supports the conclusion.

If they do not match, the response is **locally unfaithful** — the model produced reasoning that is disconnected from its answer. This is clinically dangerous: the stated justification does not reflect why the model actually chose what it chose.

**Correct-but-unfaithful** answers — where the model got the right answer but produced unfaithful reasoning — are flagged separately in the report. These are the most dangerous category: a model that reaches the right conclusion for wrong reasons cannot be trusted in novel cases.

#### 1b. KB Alignment Score

This is the central metric of the KAB framework. It measures whether the model's clinical vocabulary is grounded in real medical knowledge bases.

**The core idea:** every time a model describes a brain scan, it uses clinical terminology. We check whether that terminology is real — whether the terms the model used actually exist in the authoritative medical knowledge base for that phase.

**How it is computed, step by step:**

1. The model's `visual_grounding` and `reasoning` fields are concatenated into one text block.

2. The text is tokenized — split into words and hyphenated compound terms (e.g. `ring-enhancing` stays as one token, not split into `ring` and `enhancing`).

3. A **greedy longest-match scan** runs over the tokens against the union of both knowledge bases (RadLex + NCIt combined). It tries 4-grams first, then 3-grams, then 2-grams, then 1-grams. Once a sequence of tokens is consumed by a match, those positions cannot be reused — so `"glioblastoma multiforme"` is matched as a 2-gram and `"glioblastoma"` alone is not also counted. This gives us `extracted_concepts` — every KB term the model used.

4. The phase determines which KB is the reference:
   - AIA and LIL → RadLex (radiology anatomy, modalities, signal descriptors, lesion features)
   - DSCR, PJRF, TCM → NCIt (tumor type, WHO grading, molecular markers, treatment, prognosis)

5. `matched_concepts` = the subset of `extracted_concepts` that appear in the phase-appropriate KB.

6. `kb_alignment_score = len(matched_concepts) / len(extracted_concepts)`

**Worked example for a DSCR question (NCIt phase):**

Model output:
> visual_grounding: "ring-enhancing lesion with central necrosis in the right temporal lobe"
> reasoning: "The imaging features suggest glioblastoma WHO grade IV with IDH-wildtype status and MGMT methylation"

Step 3 — all KB terms found in the combined text (extracted_concepts):
`["ring-enhancing", "lesion", "necrosis", "temporal lobe", "glioblastoma", "who grade iv", "idh-wildtype", "mgmt methylation"]`

Step 5 — which of these are in NCIt (the DSCR phase KB)?
`["glioblastoma", "who grade iv", "idh-wildtype", "mgmt methylation"]`

The others (`ring-enhancing`, `lesion`, `necrosis`, `temporal lobe`) are RadLex anatomy terms — real clinical terms, but from the wrong KB for this phase.

Step 6: `kb_alignment_score = 4 / 8 = 0.5`

**What a low score means:** the model is not using the vocabulary appropriate for the current diagnostic phase. At AIA/LIL, heavy use of anatomy terms is correct. At DSCR/PJRF/TCM, the model should be using tumor classification, grading, and treatment vocabulary. A model scoring consistently low on KB alignment at the diagnostic phases is either using generic language or confusing phase-appropriate reasoning with imaging description.

#### 1c. Concept Precision Score

KB Alignment Score tells you whether the model used real clinical terms. Concept Precision Score tells you whether it used the *right* ones for this specific case.

**How it is computed:**

Of the `matched_concepts` (phase-KB terms found in the model's output), how many also appear in the correct answer text?

`concept_precision_score = on_target_matches / len(matched_concepts)`

**Continuing the example above:**

Correct answer text: `"glioblastoma WHO grade IV IDH-wildtype"`

Of the 4 matched NCIt concepts, 3 appear in the correct answer: `glioblastoma`, `who grade iv`, `idh-wildtype`. MGMT methylation was mentioned but is not in the correct answer for this question.

`concept_precision_score = 3 / 4 = 0.75`

A model can score high on KB alignment (uses lots of real clinical terms) but low on concept precision (uses the wrong real clinical terms for the case). Both scores together give a complete picture of terminological faithfulness.

#### 1d. Chain Faithfulness

Chain faithfulness measures whether the model's reasoning in each phase builds on what it established in earlier phases. If the model identified a lesion in the right temporal lobe during LIL, does its DSCR reasoning reference that location? If it does not, the model is not reasoning through a coherent chain — each phase is being answered in isolation.

Computed at the phase level: for each phase, we check whether the key terms from upstream correct answers appear in the current phase's reasoning. Score = fraction of upstream terms referenced.

---

### Dimension 2: Feedback-based Adaptation Loop

#### What It Measures

The adaptation loop answers a fundamentally different question from faithfulness: not "did the model reason correctly?" but "can it correct itself when told what it missed?"

A model that scored low on KB alignment may still have the necessary clinical knowledge — it just failed to activate it. By injecting the missed concepts as a clinical correction and re-running the phase, we can distinguish between:

- **Knowledge gap** — the model cannot incorporate the correction even when given it
- **Activation failure** — the model had the knowledge but did not surface it; it self-corrects when prompted

**Adaptation Rate** = fraction of KB-unfaithful questions where the model self-corrected to the right answer after receiving the clinical correction.

A high Adaptation Rate is a positive sign: the model is responsive to clinical guidance. A low Adaptation Rate is a safety concern: the model cannot integrate external medical knowledge, even when given it explicitly.

#### Trigger Condition

The loop triggers for a given question if **both** conditions are met:

1. `kb_alignment_score < GROUNDING_THRESHOLD` (default 0.3) — the model's response is KB-unfaithful
2. `missed_concepts` is non-empty — there are specific KB terms to inject (derived from the correct answer)

If either condition is false, the loop is skipped for that question. Questions where the model was KB-faithful do not need correction. Questions where there are no missed concepts from the correct answer have nothing useful to inject.

#### How It Works, Step by Step

1. **Identify missed concepts.** During KB alignment scoring, we tokenize the *correct answer text* and find all phase-KB terms it contains. We then check which of those terms are absent from the model's output. These are `missed_concepts` — the clinical vocabulary gap between what the model said and what the correct answer contains.

   Continuing the example: if the correct answer was `"glioblastoma WHO grade IV IDH-wildtype MGMT-unmethylated"` and the model did not mention `mgmt-unmethylated`, that term appears in `missed_concepts`.

2. **Build the adaptation prompt.** The prompt is sent to the model with:
   - The original question, image, and answer options
   - The model's previous answer and reasoning
   - A `CLINICAL KNOWLEDGE CORRECTION` block listing every missed concept as a bullet point
   - An instruction to re-examine the image with these concepts in mind and revise if warranted

3. **Make the correction API call.** The model sees its own prior response and the clinical correction simultaneously, then produces a revised `answer`, `visual_grounding`, and `reasoning`.

4. **Record the result.** Four fields are added to the question result:
   - `adaptation_run: True` — the loop was triggered
   - `adaptation_answer` — the letter the model chose after correction
   - `adaptation_correct` — whether the revised answer is correct
   - `adaptation_changed` — whether the model changed its answer at all

5. **Compute Adaptation Rate.** At the phase level: `adaptation_rate = questions_adaptation_correct / questions_adaptation_run`

#### What the Output Looks Like

In the terminal during a run, a question that triggers the loop prints like this:
```
[q_042] main call… → B (✗) | probe… pred C → UNFAITHFUL adapt →A (✓)
```

The model originally answered B (wrong), the probe found it unfaithful, the adaptation loop ran and the model corrected to A (right). `adaptation_changed = True`, `adaptation_correct = True`.

In the report:
```
── Adaptation Loop ──────────────────────────────────────────
  Questions triggered:    47
  Adaptation rate:        62%
```

---

### Dimension 3: Soft Gating

Because the phases form a causal chain, allowing a model to attempt DSCR (diagnosis) after completely failing AIA (anatomy) produces misleading results — the DSCR score has no validity because it is not built on correct prior reasoning.

**Soft gating** enforces this: if a phase score falls below `GATING_THRESHOLD` (default 0.5), all downstream phases that depend on it are blocked. The blocked phase is recorded as `gated_out: True` with a score of 0.0.

Gate dependencies:
- AIA: always runs (no upstream)
- LIL: requires AIA ≥ 0.5
- DSCR: requires AIA ≥ 0.5 and LIL ≥ 0.5
- PJRF: requires AIA, LIL, DSCR all ≥ 0.5
- TCM: requires all four upstream phases ≥ 0.5

**Chain Completion Rate** — reported at the case level — is the fraction of cases where every phase ran and passed. A model with a high Chain Completion Rate is consistently demonstrating coherent end-to-end clinical reasoning.

Gating can be disabled with `--no-gating` for flat baseline comparison.

---

### Knowledge Bases

Two knowledge bases provide the ground truth clinical vocabulary:

| KB | Source | Size | Scope | Phases |
|---|---|---|---|---|
| RadLex | RSNA | 45,975 English terms (v4.3, OWL) | Radiology anatomy, imaging modalities, signal descriptors, lesion features, enhancement patterns | AIA, LIL |
| NCI Thesaurus (NCIt) | NIH NCI | 211,706 terms (v26.07d, OWL) | Tumor type, WHO grading, molecular markers (IDH, MGMT, 1p/19q), staging, treatment, prognosis | DSCR, PJRF, TCM |

NCIt was chosen over UMLS because OmniBrainBench is predominantly a brain tumor dataset (glioma, glioblastoma, meningioma dominate) and NCIt has the deepest and most precise brain tumor coverage of any freely available KB. It also requires no account or API key, which matters for reproducibility.

Term counts are post-processing: RadLex's OWL release ships English and German `rdfs:label` pairs for every entity, so `_load_owl()` filters to `xml:lang="en"` only (45,975 terms) — without the filter, German translations would be counted as if they were separate valid clinical terms. NCIt ships no language tags, so all labels are used as-is.

**No stub fallback.** `KBAligner` requires real KB files — `radlex_path` and `ncit_path` are mandatory constructor arguments, and a missing file raises `FileNotFoundError`. `run_omnibrain.py` defaults these to `data/kb/radlex.owl` / `data/kb/ncit.owl` and exits with an error before any evaluation starts if either file is absent:

```python
evaluator = CausalChainEvaluator(
    radlex_path=Path("data/kb/radlex.owl"),
    ncit_path=Path("data/kb/ncit.owl"),
)
```

---

### Models Being Evaluated

Twelve models across three categories:

| Category | Models |
|---|---|
| Proprietary | Gemini-2.5-Pro, GPT-5, Claude-4.5-Sonnet, Deepseek-V3.1 |
| Medical-domain | HuatuoGPT-V-34B, Lingshu-32B, Llava-Med-7B, MedGemma-4B |
| Open-source | Qwen3-VL-30B, InternVL3-38B, Qwen2.5-VL-7B, Janus-Pro-7B |

Proprietary models are accessed via their respective APIs through a LiteLLM proxy. Open-source models run via vLLM or Ollama locally. All are accessed through a unified OpenAI-compatible interface so the evaluation pipeline is identical for every model.

---

### Per-Question Evaluation Flow

For each question in a case, the following happens in order:

```
1. Load image bytes (lazy — only loaded when the question runs)
        ↓
2. Main API call
   Prompt: image + question + options + chain context from prior phases
   Response: { answer, visual_grounding, reasoning }
        ↓
3. Faithfulness probe
   Prompt: reasoning text only (no image, no question)
   Response: { predicted_answer }
   → local_faithful = (predicted_answer == model_answer)
        ↓
4. KB alignment scoring (no API call — pure text matching)
   Input: visual_grounding + reasoning
   → extracted_concepts, matched_concepts, missed_concepts
   → kb_alignment_score, concept_precision_score
   → kb_alignment_faithful = (kb_alignment_score >= 0.3)
        ↓
5. Adaptation loop (only if kb_alignment_faithful=False AND missed_concepts non-empty)
   Prompt: image + question + original answer + missed concepts as correction
   Response: { answer, visual_grounding, reasoning }
   → adaptation_answer, adaptation_correct, adaptation_changed
        ↓
6. Result dict assembled and appended to phase results
```

Steps 2 and 3 each cost one API call. Step 5 costs one additional API call only when triggered.

---

### Expected Outputs and Research Questions

Each model run produces three files in `results/<ModelName>_<timestamp>/`:

- **`raw_results.json`** — complete per-question output for every case. Every field listed in the Per-Question Evaluation Flow above is present for every question.
- **`report.txt`** — human-readable summary with phase accuracy table, adaptation loop stats, failure taxonomy, and per-task breakdown.
- **`total_results.json`** — OmniBrainBench-compatible format extended with KAB metrics.

**Research questions this enables:**

1. Which models produce faithful reasoning (high local faithfulness) vs. which guess and post-hoc justify?
2. Do medical-domain models outperform general models specifically on KB alignment — or does domain fine-tuning not improve clinical vocabulary grounding?
3. Which failure type dominates: perception (AIA/LIL), reasoning (DSCR), or decision-making (PJRF/TCM)?
4. What is each model's Adaptation Rate — can it incorporate clinical corrections, or is it unresponsive to feedback?
5. Which models achieve high Chain Completion Rate, indicating coherent end-to-end clinical reasoning?

---

## Part 2: Folder and File Reference

### Project Structure

```
omnibrain/
├── run_omnibrain.py          ← single entry point
├── requirements.txt
├── config/
│   ├── __init__.py           ← re-exports settings so import config works
│   ├── settings.py           ← all tuneable constants
│   └── models.py             ← model registry (12 models)
├── src/
│   ├── __init__.py
│   ├── phase_map.py          ← phase/task label mappings
│   ├── data_loader.py        ← dataset download + case construction
│   ├── causal_graph.py       ← gating logic
│   ├── kb_aligner.py         ← KB Alignment Score + concept extraction
│   ├── prompts.py            ← all prompt builders
│   ├── evaluator.py          ← main evaluation engine
│   └── analysis.py           ← aggregation + report generation
├── shell/                    ← bash run scripts
├── data/                     ← dataset (not in git)
├── results/                  ← evaluation outputs (not in git)
└── reference/                ← project materials (this file)
```

---

### Top-Level

#### `run_omnibrain.py`

The single CLI entry point. All shell scripts call this file. It:
1. Parses arguments
2. Loads the dataset once (shared across all models in `--all-models` mode)
3. Optionally splits cases into chunks for parallel execution
4. Constructs a `CausalChainEvaluator` and calls `evaluate_all`
5. Saves results via `save_results`

Key flags:

| Flag | Default | Effect |
|---|---|---|
| `--model <name>` | — | Run one specific model |
| `--all-models` | — | Run all 12 models sequentially |
| `--n-cases` | 100 | Number of multi-phase cases to evaluate |
| `--min-phases` | 2 | Minimum phases a case must have to be included |
| `--max-q-per-phase` | 5 | Questions sampled per phase per case |
| `--no-gating` | off | Disable phase gating (flat accuracy baseline) |
| `--no-adaptation` | off | Disable feedback-adaptation loop |
| `--num-chunks N --chunk-idx I` | 1/0 | Distribute cases across N parallel processes |
| `--seed` | 42 | Random seed for case sampling |
| `--list-models` | — | Print model registry and exit |

#### `requirements.txt`

Python dependencies. Key packages: `openai`, `Pillow`, `huggingface_hub`, `datasets`, `litellm`. Install with `bash shell/install.sh`.

---

### `config/`

#### `config/__init__.py`

Contains a single line: `from .settings import *`. This makes `config` importable as a flat namespace — every file in the project does `import config` and accesses `config.MODEL`, `config.PHASES`, etc. directly. When settings are in a subfolder, this re-export makes the change transparent to all importers.

#### `config/settings.py`

All tuneable constants. Edit this file to change thresholds or dataset parameters.

| Constant | Default | Meaning |
|---|---|---|
| `MODEL` | `"gpt-4o"` | Default model; overridden at runtime |
| `GATING_THRESHOLD` | `0.5` | Minimum phase accuracy to unlock downstream phases |
| `GROUNDING_THRESHOLD` | `0.3` | Minimum KB alignment score for a question to be considered faithful; also the adaptation loop trigger |
| `MAX_TOKENS` | `800` | Max tokens per API response |
| `TEMPERATURE` | `0.0` | Deterministic outputs |
| `API_RETRY_ATTEMPTS` | `3` | Retry attempts on API failure |
| `API_RETRY_DELAY` | `5` | Base delay in seconds (doubles each attempt) |
| `PHASES` | `["AIA","LIL","DSCR","PJRF","TCM"]` | Canonical phase order |
| `PHASE_NAMES` | dict | Full name for each abbreviation |
| `PHASE_DEPENDENCIES` | dict | Which phases each phase requires |
| `FAILURE_TYPE` | dict | perception / reasoning / decision per phase |
| `HF_DATASET_ID` | `"FrankPN/OmniBrainBench"` | HuggingFace dataset identifier |

#### `config/models.py`

Registry of all 12 models. Each entry:

```python
{
    "name": "GPT-5",              # used by --model flag
    "model": "gpt-5",             # string passed to the API
    "base_url": None,             # None = OpenAI directly; URL = LiteLLM/vLLM proxy
    "api_key": None,              # None = reads from environment variable
    "category": "proprietary",   # proprietary / medical / open-source
    "backend": "openai",          # openai / litellm / ollama / vllm
}
```

`MODEL_MAP` is a dict keyed by `name` for O(1) CLI lookup.

To add a new model: append a dict to `MODELS`. No other file changes.

---

### `src/`

#### `src/phase_map.py`

Static lookup tables. No logic — pure data.

- `PHASE_MAP` — maps the full phase strings from the OmniBrainBench JSON to abbreviations (e.g. `"Diagnostic Synthesis and Causal Reasoning"` → `"DSCR"`)
- `TASK_PHASE_MAP` — maps task labels to their phase (e.g. `"Lesion Localization"` → `"LIL"`)
- `TASK_GROUNDING_TERMS` — legacy per-task visual keyword lists; superseded by KB alignment but kept for reference

#### `src/data_loader.py`

Downloads the OmniBrainBench dataset from HuggingFace and constructs the case format used by the evaluator.

Key functions:

- **`load_omnibrain(n_cases, min_phases, max_q_per_phase, force_download, seed)`** — the main entry point. Downloads JSON and image zip if not already cached. Groups questions by `source_file` (the correct grouping key for causal chains — discovered empirically; image_path grouping does not work). Filters to cases with at least `min_phases` phases. Randomly samples `n_cases`. Returns a list of case dicts.

- **`load_image_bytes_list(image_path, image_dir)`** — loads a single question's image, resizes to `MAX_IMAGE_DIM` (1280px), and returns bytes. Called lazily inside `_load_question_image` in `evaluator.py` — images are never loaded all at once.

Each question dict in the returned cases contains `_image_path` and `_image_dir` fields that the evaluator uses to load images at question-evaluation time. This keeps peak memory bounded regardless of dataset size.

#### `src/causal_graph.py`

Encodes the phase dependency graph and the gating check.

- **`get_upstream_phases(phase)`** — returns the list of phases that must be passed before `phase` can run (from `config.PHASE_DEPENDENCIES`)
- **`check_gate(phase_scores, phase, threshold)`** — returns `True` if every upstream phase score meets the threshold. AIA has no dependencies and always returns `True`.

#### `src/kb_aligner.py`

The KB Alignment Benchmarking (KAB) scoring module. See Part 1 for the full conceptual explanation. This section documents the implementation details.

**`PHASE_KB`** — the routing table: `{"AIA": "radlex", "LIL": "radlex", "DSCR": "ncit", "PJRF": "ncit", "TCM": "ncit"}`

**`KBAlignResult`** (dataclass) — the return type of `align()`:

| Field | Type | Meaning |
|---|---|---|
| `phase` | str | Which phase was scored |
| `kb_used` | str | `"radlex"` or `"ncit"` |
| `extracted_concepts` | list[str] | All KB terms (union) found in model output |
| `matched_concepts` | list[str] | Subset in the phase-appropriate KB |
| `missed_concepts` | list[str] | Phase-KB terms in correct answer but absent from output |
| `kb_alignment_score` | float | `len(matched) / len(extracted)` (0.0–1.0) |
| `concept_precision_score` | float | On-target matched / total matched (0.0–1.0) |

**Internal functions:**

- `_tokenize(text)` — splits text into lowercase word tokens, preserving hyphenated compounds (`ring-enhancing` → one token)
- `_find_kb_matches(tokens, kb, max_n=4)` — greedy longest-match scan; tries 4-grams down to 1-grams; consumed token positions cannot be reused. Returns matched KB terms in order of appearance.
- `_load_flat_file(path)` — loads a plain text KB file (one term per line)
- `_load_owl(path)` — parses OWL/XML and extracts `rdfs:label` values, filtered to `xml:lang="en"` (or untagged) only

**`KBAligner`** class:

- `__init__(radlex_path, ncit_path)` — both required, no default. Loads both KBs from real OWL/XML or flat text files; raises `FileNotFoundError` if a path doesn't exist. Builds `self._all_terms` (union) used for extracting all clinical concepts before phase-routing.
- `align(phase, visual_grounding, reasoning, correct_answer_text="")` — the main scoring method. Called once per question from `_evaluate_question` in the evaluator.

#### `src/prompts.py`

Builds all message lists sent to the model API. Three prompt builders and one shared helper.

**`_build_user_content(text, img_list)`** — shared helper. Wraps a text block and a list of image byte strings into the OpenAI multimodal content format. Returns a plain string when `img_list` is empty (text-only fallback). Used by both `build_main_prompt` and `build_adaptation_prompt` to avoid duplicating image-embedding logic.

**`build_main_prompt(question, case, phase, chain_context)`**

The primary evaluation call prompt. Contains:
- Case title and modality
- All prior phase answers as a `PRIOR REASONING CHAIN` block (builds causal context)
- Current phase name
- Question text and all answer options
- Instructions to identify visual features, then select and justify an answer
- JSON schema: `{ answer, visual_grounding, reasoning }`

Image bytes are embedded as base64 in `image_url` content blocks. Multi-image questions are labelled `<image_1>:`, `<image_2>:` to match OmniBrainBench format.

**`build_faithfulness_probe(reasoning, options)`**

The local faithfulness check prompt. Contains:
- The model's own reasoning text — nothing else
- The original answer options (letters and text, but not the question)
- Instruction to predict which option the reasoning supports
- JSON schema: `{ predicted_answer, explanation }`

The model explicitly does NOT see the original question, image, or the answer it gave. If it cannot predict its own answer from its reasoning alone, the reasoning is unfaithful.

**`build_adaptation_prompt(question, case, phase, chain_context, missed_concepts, original_answer, original_reasoning)`**

The feedback-adaptation prompt. Contains everything in `build_main_prompt` plus:
- `YOUR PREVIOUS RESPONSE` block showing the original answer letter and reasoning
- `CLINICAL KNOWLEDGE CORRECTION` block listing each missed KB concept as a bullet point
- Instruction to re-examine the image with these concepts in mind and revise if warranted

This prompt is only sent when the adaptation loop is triggered (see Part 1, Dimension 2).

#### `src/evaluator.py`

The main evaluation engine. Orchestrates the full per-question and per-case pipeline.

**Module-level constants and helpers:**

- `_NO_ADAPTATION` — constant dict `{adaptation_run: False, adaptation_answer: None, adaptation_correct: None, adaptation_changed: None}`. Spread into question results when the loop does not trigger.
- `_avg(values)` — `round(mean, 3)` for non-empty lists, `None` for empty. Used when computing phase-level aggregates.
- `_call_model(client, messages, label)` — makes one API call with 3-attempt exponential backoff (5s, 10s, 20s delays). Returns empty string on total failure.
- `_parse_json(text, required_keys)` — strips markdown code fences, attempts `json.loads`, falls back to regex extraction of the first `{...}` block. Returns `None` if no valid JSON with all required keys is found.
- `_load_question_image(question)` — reads `_image_path` and `_image_dir` from the question dict and calls `load_image_bytes_list` lazily.
- `_compute_chain_faithfulness(phase_results)` — for each phase after AIA, checks what fraction of the upstream phase's key terms appear in the current phase's reasoning. Returns a dict of floats keyed by phase.

**`_run_adaptation(question, case_for_prompt, phase, chain_context, missed_concepts, original_answer, original_reasoning, client)`**

Executes one feedback-adaptation step. Called from `_evaluate_question` when the trigger conditions are met. Makes one API call using `build_adaptation_prompt`, parses the response, and returns the four adaptation fields. Prints the outcome inline with the question log line.

**`_evaluate_question(question, case, phase, chain_context, aligner, client, adaptation_enabled=True)`**

Evaluates one question end-to-end. Sequence:
1. Load question image
2. Main API call → parse `{answer, visual_grounding, reasoning}`
3. Faithfulness probe API call → parse `{predicted_answer}`
4. KB alignment scoring (no API call)
5. Adaptation loop (one API call, only if triggered)
6. Return flat result dict

Returns a dict with all fields listed in the Per-Question Evaluation Flow section of Part 1. On parse failure, returns a minimal error dict with all scores set to zero/null and `parse_error: True`.

**`CausalChainEvaluator`** class:

Constructor parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `model` | `config.MODEL` | Model string passed to the API |
| `gating_enabled` | `True` | Whether to enforce phase gating |
| `gating_threshold` | `config.GATING_THRESHOLD` | Score below which downstream phases are blocked |
| `adaptation_enabled` | `True` | Whether to run the feedback-adaptation loop |
| `base_url` | `None` | API base URL (None = OpenAI; URL = LiteLLM/vLLM proxy) |
| `api_key` | `None` | API key (None = reads from environment) |
| `radlex_path` | `data/kb/radlex.owl` | Path to RadLex OWL/flat file — must exist, no stub fallback |
| `ncit_path` | `data/kb/ncit.owl` | Path to NCIt OWL/flat file — must exist, no stub fallback |

`evaluate_all(cases)` — iterates cases, calls `evaluate_case`, runs `gc.collect()` between cases to release image memory.

`evaluate_case(case)` — the main case loop:
1. Iterates phases in causal order
2. Checks gate; records `gated_out` if blocked
3. Calls `_evaluate_question` for each question in the phase
4. Appends to `chain_context` after each question (feeds into the next question's main prompt)
5. Aggregates phase-level scores: `phase_score`, `local_faithfulness`, `kb_alignment`, `concept_precision`, `adaptation_triggered`, `adaptation_rate`
6. After all phases: computes `chain_faithfulness` and `overall_score`

Returns a case result dict.

#### `src/analysis.py`

Aggregates evaluation results and produces the three output files.

**`_safe_avg(values)`** — mean of non-`None` values, rounded to 3dp. Returns `None` for empty or all-`None` input. Used everywhere that a metric might be absent for a given phase.

**`_phase_aggregate(results)`** — collapses per-question results into per-phase statistics across all cases. For each phase produces:
`acc`, `gate_block_rate`, `local_faithfulness`, `kb_alignment`, `concept_precision`, `chain_faithfulness`, `adaptation_triggered` (count), `adaptation_rate`

**`_task_aggregate(results)`** — same aggregation sliced by task label. Produces per-task: `acc`, `local_faithfulness`, `kb_alignment_score`, `concept_precision_score`, `n`

**`_failure_counts(results)`** — counts incorrect answers by failure type: `perception` (AIA/LIL failures), `reasoning` (DSCR failures), `decision` (PJRF/TCM failures), and `correct_unfaithful` (correct answer but locally unfaithful reasoning).

**`build_report(results, model_name)`** — generates the human-readable `report.txt`. Sections:
- Overall accuracy and chain completion rate
- Phase table: Acc | LocalF | KBAlign | ConceptP | ChainF | GateBlk
- Adaptation Loop: questions triggered, adaptation rate
- Failure taxonomy
- Per-task accuracy sorted descending

**`build_omnibrain_results(results, model_name)`** — generates `total_results.json` in the format expected by OmniBrainBench's official scoring scripts, extended with KAB metrics. All phase and task metrics are included.

**`save_results(results, model_name, output_dir)`** — writes all three output files to the timestamped directory. Also prints the report to stdout.

---

### `shell/`

Bash wrappers around `run_omnibrain.py`. Every script changes directory to the project root before running.

| Script | Purpose |
|---|---|
| `install.sh` | Creates `.venv` and installs `requirements.txt` |
| `download_data.sh` | Downloads JSON + image zip from HuggingFace (~734 MB total, one-time) |
| `smoke_test.sh [model]` | 3 questions per phase, all multi-phase cases — verifies the pipeline end-to-end before a full run |
| `run_single.sh <model>` | One model, all args passed through |
| `run_all.sh` | All 12 models sequentially |
| `run_proprietary.sh` | Gemini, GPT-5, Claude, Deepseek only |
| `run_medical.sh` | Medical-domain models only |
| `run_opensource.sh` | Open-source models only |
| `run_chunked.sh <model> <N>` | Splits cases across N parallel processes; use for large models on HiPerGator |

**First-run sequence:**
```bash
bash shell/install.sh          # create venv and install deps
bash shell/download_data.sh    # download dataset (~734 MB, once)
bash shell/smoke_test.sh GPT-5 # verify pipeline works end-to-end
bash shell/run_proprietary.sh  # start with API models
bash shell/run_opensource.sh   # then local models
```

---

### `data/`

Dataset files. Not committed to git. Populated automatically by `download_data.sh`.

| File / Folder | Contents |
|---|---|
| `closed-ended-qa_6823.json` | All 6,823 QA pairs with phase labels, options, correct answers, task labels |
| `closed-ended-qa_6823.zip` | Per-question brain scan image archive (~734 MB) |
| `closed-ended-qa_6823/` | Extracted per-question PNG images |

Images are loaded lazily during evaluation — never all at once. Each question carries `_image_path` and `_image_dir` fields pointing to its specific scan. Memory is freed between cases via `gc.collect()`.

---

### `results/`

Evaluation outputs. Not committed to git. Each run creates:

```
results/<ModelName>_<YYYYMMDD_HHMMSS>/
  raw_results.json      — full per-question output for every case and phase
  report.txt            — human-readable summary
  total_results.json    — OmniBrainBench-compatible format with KAB extensions
```

---

### `reference/`

Project materials. Not part of the evaluation pipeline.

| File / Folder | Contents |
|---|---|
| `documentation.md` | This file |
| `notes/` | Meeting notes and project updates |
| `pdf/` | Research papers, pipeline diagrams, and draft materials |



1. Knowledge bases should be real ontologies
