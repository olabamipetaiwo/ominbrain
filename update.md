# Meeting Update — 2026-06-23

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

## Professor's Response

The professor accepted the approach. Both the KB selection rationale and the KAB framework (including the feedback-adaptation loop) were approved as the direction to move forward with.

---

## Outstanding Ask

Access to the **HiPerGator** platform (University of Florida) is needed to run the full experiments. HiPerGator provides the compute resources required to evaluate all 6,823 OmniBrainBench questions at scale. This access has been requested from the professor and is currently pending.
