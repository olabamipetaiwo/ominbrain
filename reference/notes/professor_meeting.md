# Professor Meeting — Knowledge Alignment Benchmarking
**Date:** 2026-06-23

---

## 1. What We Are Doing

We are reframing our evaluation methodology as **Knowledge Alignment Benchmarking (KAB)**.

Instead of just checking whether a model answers correctly, we evaluate whether its **multimodal reasoning chain strictly aligns with established medical knowledge bases** at every phase of the clinical pipeline.

Two dimensions:
- **Faithfulness** — Does the model's causal chain (AIA → LIL → DSCR → PJRF → TCM) map to verified medical facts?
- **Feedback-based Adaptation** — When a clinical knowledge correction is injected after a failure, does the agent self-correct its reasoning path?

---

## 2. The Two Knowledge Bases We Selected

### KB 1 — RadLex (Radiology Lexicon)
| | |
|--|--|
| **Source** | RSNA (Radiological Society of North America) |
| **License** | Free, registration at radlex.org |
| **Size** | ~46,000 radiology-specific terms |
| **Format** | OWL ontology + CSV |
| **Covers** | Anatomy, imaging modalities, signal descriptors, lesion characteristics |
| **Phases** | AIA, LIL |

**Why RadLex:**
- It is the only knowledge base built exclusively for radiology
- 71% of OmniBrainBench questions are in AIA and LIL phases (4,845 of 6,823 questions)
- When the model says "FLAIR hyperintensity in the left temporal lobe," RadLex is the authoritative source for validating that observation
- No other KB owns the imaging-specific vocabulary space

---

### KB 2 — NCI Thesaurus (NCIt)
| | |
|--|--|
| **Source** | National Cancer Institute (NCI), U.S. NIH |
| **License** | Public domain — no registration, direct download |
| **Size** | ~170,000 concepts |
| **Format** | OWL + flat files |
| **Covers** | Cancer types, tumor grading, staging, chemotherapy, surgical procedures, outcomes |
| **Phases** | DSCR, PJRF, TCM |

**Why NCI Thesaurus over UMLS:**
- OmniBrainBench is predominantly a **brain tumor dataset** — glioma, glioblastoma, meningioma dominate the DSCR questions
- NCIt has the deepest and most precise coverage of brain tumor biology, WHO grading (Grade I–IV), and treatment protocols of any free KB
- UMLS is broader but less specific to the tumor cases that actually appear in the dataset
- NCIt is **public domain with a direct download** — no account or API key required, which removes a reproducibility barrier reviewers may flag
- PJRF and TCM phases have only 115 total questions (2% of data), so we do not need the full clinical breadth of UMLS

---

## 3. How the Two KBs Map to the Framework

```
AIA  ──────────────────────► RadLex
  Anatomical & Imaging Assessment
  (anatomy terms, modality, signal descriptors)

LIL  ──────────────────────► RadLex
  Lesion Identification & Localization
  (lesion features, location, enhancement pattern)

DSCR ──────────────────────► NCI Thesaurus
  Diagnostic Synthesis & Causal Reasoning
  (tumor type, WHO grade, differential diagnosis)

PJRF ──────────────────────► NCI Thesaurus
  Prognostic Judgment & Risk Forecasting
  (staging, recurrence risk, survival outcomes)

TCM  ──────────────────────► NCI Thesaurus
  Therapeutic Cycle Management
  (surgical resection, radiation, chemotherapy, TMZ)
```

The boundary between RadLex and NCIt falls exactly on the perception/reasoning boundary already built into the framework.

---

## 4. What This Replaces in the Current System

The current grounding metric in the evaluator is **vocabulary matching** — checking whether a hardcoded word list appears in the model's `visual_grounding` text. 

The problem: "lesion" appearing in the output does not mean the model used clinically valid reasoning. Reviewers rightly flag this.

**Knowledge Alignment Benchmarking replaces this with:**
- Concept extraction from the model's `reasoning` and `visual_grounding` fields
- Cross-reference against RadLex (AIA/LIL) or NCIt (DSCR/PJRF/TCM)
- A **KB Alignment Score**: proportion of the model's stated clinical concepts that are valid entries in the appropriate KB
- A **Concept Precision Score**: are the KB concepts used actually consistent with the correct answer?

---

## 5. The Feedback-based Adaptation Loop (New)

When a phase produces unfaithful output (correct answer, wrong reasoning) or a gate failure:

1. Retrieve the relevant KB concept(s) the model missed or misused
2. Inject them as a structured clinical knowledge correction into the prompt
3. Re-run the phase
4. Measure whether the model self-corrects — **Adaptation Rate**

This operationalises the "self-adaptive agent" vision and gives the paper a second novel contribution beyond faithfulness scoring.

---

## 6. Why This Strengthens the Paper

| Weakness (current) | How KAB addresses it |
|--------------------|----------------------|
| Grounding metric is vocabulary matching — easy to dismiss | Replaced with real KB concept alignment |
| "Correct-but-unfaithful" finding is not new | Now grounded in medical KB validation — clinically specific claim |
| Only 10 multi-phase cases | KB alignment works on single-phase questions too — all 6,823 questions get a faithfulness signal |
| No adaptation mechanism | Feedback-adaptation loop is a direct second contribution |

---

## 7. Immediate Next Steps

1. Download RadLex OWL from radlex.org
2. Download NCIt OWL/flat file from evs.nci.nih.gov
3. Build `src/kb_aligner.py` — concept extraction + phase-aware KB lookup
4. Replace `_grounding_score()` in `src/evaluator.py` with KB alignment score
5. Add feedback-adaptation loop as a new phase re-run triggered by unfaithful output
6. Re-run evaluation on existing cases to compare old vs. new grounding metric

---

## 8. Open Questions for the Professor

- Should the feedback injection include the full KB concept definition, or just the concept label?
- Do we report KB Alignment Score as a replacement for grounding faithfulness, or alongside it?
- Is there a preference for UMLS over NCIt if the research scope expands beyond brain tumors?
