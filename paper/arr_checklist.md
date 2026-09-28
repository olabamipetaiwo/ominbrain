# ARR Responsible NLP Research checklist: draft answers (2026-09-25)

Questions from https://aclrollingreview.org/responsibleNLPresearch/ (fetched 2026-09-25). Section numbers refer to the current `paper/latex/acl_latex.tex`
(Sections 1-6; Limitations and Ethics Statement follow Section 6 unnumbered; Appendix A v3 item set, B KAB, C OmniBrainBench compatibility,
D evidence-audit details, E artifacts/licenses/compute, F worked v4 example, G worked v3 example, H output handling and input check).
ARR asks for a section number or a short justification for every "Yes", and a justification for every "No"; a bare "Yes" is a known problem.
Page limit (https://aclrollingreview.org/cfp): 8 pages of content; the Limitations section (required, after the Conclusion), an optional ethics section and
references do not count, and appendices do not count. The Conclusion ends on page 8.

## A. For every submission

**A1. Did you describe the limitations of your work?** Yes. Section "Limitations": no clinician validation of the keys, LIL/DSCR keys depend on
automated segmentation, TCM key is a stipulated rule, PJRF outcome unverified, power, single reference model, partial input-handling check. Sections 3.1 and 5
scope each claim to what was measured.

**A2. Did you discuss any potential risks of your work?** Yes. Ethics Statement and Appendix E ("Intended use"): results are not a clinical validation
and must not be read as evidence for or against clinical use of any model; the keys are unvalidated and PJRF/TCM are stipulated or unverified; no
patient-identifying data are added. Compute/environmental cost is reported in Appendix E (about 154 GPU-hours).

## B. Did you use or create scientific artifacts? Yes.

**B1. Cited the creators?** Yes for data and tools: LUMIERE (Suter et al. 2022), OmniBrainBench (Peng et al. 2026), RANO (Wen et al. 2010),
DeepBraTumIA/HD-GLIO-AUTO (Kickingereder et al. 2019), HD-BET (Isensee et al. 2019), RadLex, NCI Thesaurus. For the models, no: the reference list is
limited to peer-reviewed publications (project rule), so MedGemma, Gemma 3, Llama 4 and Gemini are identified by name, tag, digest and quantization (Appendix E,
Table 11) instead of by technical report. If ARR objects, cite the technical reports as arXiv/tech reports or drop the rule for models only.

**B2. Discussed the license or terms?** Yes, Appendix E. LUMIERE: "may only be used for non-commercial purposes" (dataset terms; a named license was NOT
verified: the Figshare page returned 403, and the paper's CC BY 4.0 statement is about the article). OmniBrainBench: CC BY-SA 3.0 (dataset card). MedGemma: Health AI
Developer Foundations terms of use. Gemma-3: Gemma Terms of Use and Prohibited Use Policy. Llama-4-Scout: Llama 4 Community License Agreement and Acceptable Use Policy.
Gemini: Google's Gemini API terms. We release no LUMIERE images. Not verified: RadLex and NCIt licence names (KAB appendix only), and whether the Llama 4 acceptable-use
policy has a geographic clause for multimodal models (we are US-based; check before submission if the authors are elsewhere).

**B3. Use consistent with intended use?** Yes, Appendix E: non-commercial research evaluation, matching LUMIERE's terms; models used for research evaluation only.
MedGemma's card says outputs are not for clinical decisions; we do not use them clinically.

**B4. Steps to check for identifying or offensive content?** Partly. We relied on the dataset authors' de-identification (skull-stripped images; dates as weeks
relative to the pre-operative scan; Bern ethics approval and consent waiver, as reported in the LUMIERE paper). We ran no separate identifier detection. The item text uses
age, sex, MGMT and IDH from the released table (quasi-identifiers, but already public). No free-text or offensive-content risk beyond model output. State this plainly
rather than answering a bare "Yes".

**B5. Documentation of the artifacts?** Partly. Sections 3-3.2 and Limitations give domain (glioblastoma MRI), single center, cohort selection, image processing,
item construction. There is no separate data statement or dataset card for the v4 item set yet; the LUMIERE paper reports scanners (95% Siemens), which we do not repeat.

**B6. Statistics such as number of examples and splits?** Yes. Table 1 and Section 3.2 (62 patients; n = 62 / 51 / 62 / 61 / 62 for AIA / LIL / DSCR / PJRF / TCM).
There are no train/dev/test splits: evaluation only, no training or tuning.

## C. Did you run computational experiments? Yes.

**C1. Parameters, compute budget, infrastructure?** Yes, Appendix E: 4.3B, 12.2B, 27.4B and 108.6B (17B active) parameters at 4-bit (Ollama Q4_K_M), Gemma-3-27B also in bf16 (vLLM);
one RTX PRO 6000 Blackwell GPU per job; about 154 GPU-hours for all LUMIERE work, about 56 for the v4 runs and input checks; 525 Gemini API calls, about 1.1M tokens
(`results/compute_budget.json`, `tools/compute_budget.py`).

**C2. Experimental setup, hyperparameter search?** Yes, Section 4 and Appendix E. No training and no hyperparameter search. Decoding is greedy (temperature 0), 800-token cap
(Gemini 16,384), 3 retries, prompts as in the code. The equivalence margin (+/-10 pp) was fixed in `paper/preregistration_v4.md` before the runs.

**C3. Descriptive statistics, single run or not?** Yes. Patient-bootstrap 95% intervals (10,000 resamples), Wilson intervals, exact McNemar tests, Holm correction over the 12 E1 tests
(Section 4; tables in Section 5). Each condition is one run; greedy decoding is deterministic, and a v3 repeat gave identical answers on 260 of 260 questions.

**C4. Existing packages, versions, settings?** Yes, Appendix E: Ollama 0.33.0, vLLM 0.27.1, PyTorch 2.13.0, Transformers 5.15.1, OpenAI client 2.54.0, Python 3.12.5, NumPy 2.3.5, SciPy 1.18.1,
pandas 3.0.5, Pillow 12.3.0. Model tags and digests in Table 11. LiteLLM was used only for the earlier v3 drafting, not for the reported v4 runs.

## D. Did you use human annotators or research with human participants? No.

We recruited no annotators or participants. The expert RANO ratings are part of the released LUMIERE data (one neuroradiologist, per its authors); items were drafted by an LLM (v3) or computed by rules (v4).
- **D1, D2, D5:** not applicable (no annotators recruited).
- **D3:** not applicable to us; the LUMIERE authors report a consent waiver by the Bern cantonal ethics committee (Ethics Statement).
- **D4:** we did not seek an ethics review: secondary use of a public, de-identified dataset. **Decision for the authors:** confirm with UCF (IRB/research office) whether a formal "not human subjects research" determination is needed, and answer accordingly.

## E. Did you use AI assistants? Yes.

**E1.** Yes, Ethics Statement: Claude 4.5 Sonnet drafted the v3 items (Appendix A); Claude Code helped write and run analysis code and edit the text; the authors are responsible for all content.

## Open items for the authors (not resolvable from the repo)
1. Code/data release plan: the paper says we do not release LUMIERE images and that derived items would carry non-commercial terms. Change if the plan differs.
2. IRB determination (D4).
3. Whether to cite model technical reports (B1).
4. Named license for LUMIERE (B2) if a stricter statement is wanted.
