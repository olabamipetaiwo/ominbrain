# Final submission review — 6 October 2026

Reviewed `latex/acl_latex.tex`, its included tables/macros, bibliography, all 18 rendered PDF pages, the analysis-plan amendments, selected analysis implementations, the ARR checklist, and the local anonymous-release snapshot. No manuscript or results were changed. Venue remains unconfirmed; formatting findings provisionally assume ARR long-paper submission.

Recommendation: address findings 1–5 before uploading. The main contribution is understandable and the paper appropriately discloses absent clinician validation, the distinction between observable behavior and internal image use, and the limitations of the positive control. The remaining issues are mainly reporting consistency and submission readiness, not a reason to launch new model experiments tonight.

## 1. High: new analysis appears only in Limitations

Location: `latex/acl_latex.tex:546`, PDF page 9.

The new-lesion audit reports 46 disagreements partitioned into 22 newly measurable components, 8 pre-existing components, and 16 with no other measurable component. These results are introduced only in Limitations. ARR's author checklist explicitly excludes new experiments or analysis from that section. The main conclusion already ends at the bottom of page 8, so moving this paragraph into the main body could break the page limit.

Fix: move the numerical analysis and its interpretation into Appendix D; retain the limitation about tracking one lesion and omitting new-lesion criteria, with an appendix reference. This preserves the main-body length.

Source: [ARR author checklist](https://github.com/acl-org/aclrollingreview/blob/main/authorchecklist.md).

## 2. High: Table 10's stated formula is wrong for the updated transition definition

Locations: `latex/acl_latex.tex:659`; `latex/generated/tab_v4_e3trans.tex`; `tools/lumiere_v4_supplement.py:177`.

The text says the registered share equals “moved plus already there, over all items.” The code now correctly distinguishes starting at the target from staying there after the flip. The table's “Already there” column counts both those who stay and those who move away, but it does not expose that split.

- Gemma-3-27B label flip: displayed counts give `(25 + 3) / 46 = 60.9%`, while the registered share is 54.3%.
- Llama-4-Scout label flip: displayed counts give `(10 + 12) / 46 = 47.8%`, while the registered share is 41.3%.

The implementation computes `(moved_to_new + stayed_at_target) / n`; do not replace the reported percentages with the naive sums. Correct the prose and define “Already there” as “at target before flip.” Explain that the registered share counts only those ending at the target. Ideally expose the stayed/moved-away split in the appendix. Also replace “Only the first column shows an effect of the flip”: changing to another answer or leaving the target is also an effect, although not successful following of the new target.

Suggested prose: “The registered share is the proportion ending at the new target (moved to it plus remained at it). ‘Already there’ counts all answers at that target before the flip, including those that subsequently leave it, and is excluded from the informative denominator.”

## 3. High: the paper overstates how much of the final study was fixed before runs

Locations: `latex/acl_latex.tex:400`, `:415`, `:518`, `:532`; `preregistration_v4.md:114` and `:116`.

The dated amendments document correction of two construction errors after a first round of runs, reducing the cohort from 62 to 46 patients; all conditions were rerun. The next amendment changes the DSCR stem and reruns dependent conditions. The paper does not tell readers about this rebuilding while repeatedly emphasizing a control suite fixed in advance. The original hypotheses and correction family can still be described as prespecified, but that is different from saying the final item construction and all controls were prespecified.

Fix: add a short disclosure in Section 4, with details in the artifact or appendix. For example: “The hypotheses, margin and Holm family preceded the initial runs. After that round, we corrected measurability and lesion-tracking errors, rebuilt the cohort from 62 to 46 patients, and reran all conditions; a subsequent DSCR wording correction triggered reruns of dependent conditions. Only the corrected runs are reported.”

Figure 3 and the worked example also call their three checks “prespecified,” although the decisive donor permutation is post hoc. The caption partly discloses this, but the figure itself and surrounding prose should simply say “additional checks,” with the permutation explicitly labeled exploratory.

## 4. High: the local reproducibility package does not match the submitted paper

Locations: `latex/acl_latex.tex:580`; `release/anon_artifact/reproduce.sh`; `release/anon_artifact/expected/generated/numbers.json`.

The manuscript promises a command that regenerates every statistic and table. In this checkout:

- The local artifact contains neither `data/` nor `results/`, although its README describes both. These may exist in a separately uploaded package; this review cannot establish that.
- The artifact's expected numbers omit **47 macros cited by the current main TeX file**, covering donor validation, permutation validation, and alternative-assignment robustness.
- `vfourTransLabelInfGemmaTwentySeven` is **46** in the artifact snapshot versus **43** in the current paper.
- The release's `paper_numbers.py` does not contain the current donor-validation, permutation-validation and robustness macro generators; its reproduction command does not run those analyses.

Fix: rebuild the actual submission artifact from the current analysis revision and complete raw records, regenerate its expected outputs, then run reproduction from a clean unpacked copy. Verify the anonymous link in the submission form. Do not treat the current local snapshot as evidence that the latest paper reproduces. If the uploaded artifact is different, validate that exact package instead.

## 5. High: donor-tracking conclusions need to distinguish the original assignment from robustness runs

Locations: abstract (`latex/acl_latex.tex:154`), conclusion (`:532`), robustness paragraph (`:617`).

The conclusion says donor tracking is not separable from a random donor “in any case.” Appendix D reports one of five alternative Scout/DSCR assignments significant, with minimum p = .039. The results paragraph already uses the more accurate “not consistently detected.”

Fix the abstract and conclusion to say: “No open-model cell showed significant donor-key association on the original assignment; Scout/DSCR was significant in one of five alternative assignments, so tracking was not consistently detected.” This is compatible with the reported results and avoids implying every robustness result was null.

## 6. Medium: permutation validation language exceeds its evidence

Location: `latex/acl_latex.tex:615`, PDF page 14.

The paragraph says the samplers induce the “same” distribution, have “equal means,” and return the “same” p-value. The printed values are similar, not equal: DSCR means +23.2 versus +23.0; p = .250 versus .240; AIA p = .052 versus .050. The AIA result is especially close to the decision boundary. Type-I estimates are 3.3% and 3.4%, rather than literally the nominal 5%.

Fix: describe “similar empirical null distributions” and “conservative rejection rates in the two simulated settings.” Replace the general assertion that repair “controls the test's false-positive rate” with “showed no excess false positives in these simulations.” Preserve the important existing caveat that this conditional association test does not reconstruct the image-assignment mechanism. Simulation on two observed cells does not prove general calibration.

## 7. Medium: update submission metadata and reproducibility details

- `arr_checklist.md` still reports 62/51/62/61/62 items, obsolete appendix letters, old model-table numbering, and a deferred release plan. Current counts are 46/38/46/45/46; artifacts are Appendix B and input checks Table 8. Do not paste the old checklist into the submission form.
- `latex/acl_latex.tex:550` says the reference was evaluated once, and `:584` says each condition ran once; qualify these as the original fixed assignment, since Appendix D now reports five additional donor assignments.
- The reported 525 API calls, 1.1M tokens and GPU totals should be reconciled with the added robustness runs. They may describe an earlier scope; the necessary raw records are not local, so I could not independently update them.
- Section 4 promises model tags/digests in Appendix F, but Table 8 omits the API reference and Pixtral. Add their exact identifiers and evaluation dates; state if an immutable API version was unavailable.
- `custom.bib:206` prints the editorial note “proceedings entry not yet verified” in the bibliography. Keep a clean “To appear” if appropriate and remove the internal verification note. The authors' [UniMod repository](https://github.com/futurespyhi/UniMod#citation) corroborates the listed title, authors and DOI but says proceedings pages are pending. That is not independent verification by ACM.

## 8. Lower priority: presentation and scope wording

- Table 3 (page 7) and Table 6 (page 16) use very small text. No overlap was visible, but increasing readability would help; use the available width or move secondary interval columns to a supplementary table if necessary. This is a readability concern, not an asserted fixed minimum-font violation.
- Pages 17–18 each contain a single floating table with extensive whitespace. Consolidating appendix floats would improve polish without changing the main-body page count.
- Figure 3 says “the drop is the no-image arm collapsing,” whereas the body correctly says the accuracy gap does not identify its mechanism. Prefer “the text-only arm scores far below chance.”
- “Two bf16 reruns” suggests both models were already in the primary roster. Prefer “two bf16 controls”; only Gemma-3-27B is a matched rerun.
- Calling the answer prior a statistical “confound” of a matched ablation is stronger than necessary. It limits interpretation of accuracy gain as successful visual grounding; it does not erase an observed paired effect. The paper's narrower “does not establish correct image use” formulation is preferable.

## Checks completed and limits

- Inspected all 18 PDF pages. No obvious clipping, overlapping text, blank pages, or unresolved `??` references were found. Sparse appendix float pages are noted above.
- Conclusion ends on page 8; Limitations starts on page 9. Meets the provisional ARR long-paper body limit, subject to fixing the new-analysis placement. [ARR submission rules](https://aclrollingreview.org/cfp).
- A4 page size; all fonts embedded; anonymous author line and blank author metadata; review line numbers present.
- Abstract is approximately 190 whitespace-delimited words after macro substitution, below the 200-word guideline. [ACL formatting](https://acl-org.github.io/ACLPUB/formatting.html).
- Every direct source `ref` has a matching source label. Visible citations resolve in the supplied PDF. This was not an exhaustive verification of all bibliographic claims against primary publications.
- The main headline numbers agree with the displayed generated tables; transition-definition and artifact discrepancies are described above.
- No local `pdflatex`, `latexmk`, or `tectonic` executable was found. The saved log is older than the latest source/PDF, so a fresh clean compilation was not verified. Rebuild on the established TeX/Overleaf environment after corrections and recheck that the conclusion still ends on page 8.
- Raw v4 items and model outputs are absent from this checkout. Statistical recomputation and uploaded artifact/link verification were therefore not possible; no claim of full empirical reproduction is made.
