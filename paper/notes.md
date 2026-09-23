## Built and Working End-to-End

### Implementation

The following components are complete and working:

- `config/lumiere.py`
- `src/lumiere_downloader.py`
- `src/lumiere_facts.py`
- `src/lumiere_prompts.py`
- `src/lumiere_drafter.py`
- `src/lumiere_loader.py`
- `tools/lumiere_review_app.py`
- `tools/lumiere_merge_reviewed.py`
- `run_lumiere.py`

### Dataset and Fact Extraction

- **29/30 target patients** have verified, provenance-tracked facts.
- Facts are sourced from:
  - AIA
  - LIL
  - DSCR
  - PJRF
  - TCM
- Each case represents a genuine **same-patient longitudinal chain**.

### MCQ Generation

- **144/145 MCQ items** have been drafted using **Claude 4.5 Sonnet**.
- All drafted items are schema-valid:
  - 3–5 answer options
  - Correct answer is present among the options

### Bugs Found and Fixed

Two substantive bugs were identified and corrected:

1. **DSCR timepoint sampling bug**
   - The pipeline was always selecting the final timepoint.
   - This caused every DSCR answer to be `"progressive disease"`.
   - Fixed by introducing random timepoint sampling.
   - Current distribution:
     - PD: 20
     - SD: 6
     - CR: 2
     - PR: 1

2. **DSCR/LIL timepoint mismatch**
   - The DSCR rating and LIL imaging facts could silently refer to different dates.
   - Fixed by constraining selection to timepoints that contain both:
     - a DSCR rating, and
     - complete LIL imaging facts.

### Image Rendering

- **58 slice PNGs** have been rendered.
- These bridge the source **3D NIfTI volumes** to the evaluator's existing **2D image loader**.

---

## Remaining Work

### 1. Expert Review

The generated cases require review by an actual domain expert, ideally a:

- Radiologist, or
- Neuro-oncologist

The reviewer should inspect the cases through:

```bash
tools/lumiere_review_app.py