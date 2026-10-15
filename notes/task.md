# Task list — address ICHI_REVIEW_REPORT.md before ICHI submission

Status: DONE (all fixes applied; paper compiles 10pp, 0 undefined, 0 overfull). No model reruns.

## References check (requested first; hallucinations = instant reject)
- [x] Verified all 21 cited refs are real + correctly attributed (14 web-verified incl. all DOIs/venues/pages for recent + clinical refs; 7 canonical classics). UniMod confirmed "Accepted to ACM MM 2026", authors/DOI exact. No fabrications.
- [ ] (nit, optional) Goyal 2017 CVPR page span sometimes cited 6904-6913 vs our 6325-6334 (paper real; page span worth a 10-sec check).

## Review fixes (ICHI_REVIEW_REPORT.md §11)
- [x] M1 disclose prespecified E2 rule met in 2 cells; label permutation + E2-Holm as post hoc (abstract, §V-d, Fig.2 caption/node, conclusion).
- [x] M2 own-image conditional association test added to tools/lumiere_v4_supplement.py (own_image_association, section I2) + Holm over 12 cells + text-only control; macros wired in paper_numbers. Reproduces reviewer exactly: Scout/DSCR kappa=0.19, p=.015, Holm=.177, text-control=.877; perm null mean=23pp. Fig.2 c1/verdict + Contribution 1 reframed "suggested but not established".
- [x] M3 prespecified DSCR sensitivity sentence in §V-b (Scout +57.7 [+34.6,+76.9], subset 80.8% PD, reference 0.0) via new macros.
- [x] M4 scope "significant throughout" -> AIA/LIL only.
- [x] M5 disclose DSCR rule tuned against expert agreement before item build (§III-A).
- [x] M6 split TCM (image-free) out of the image-dependence clause in abstract + conclusion.
- [x] M7 cite the two concurrent arXiv papers (Zafar 2603.03437; Zhu/Ask4VG 2606.01044) + Related Work sentence. Both verified real (user approved citing arXiv-only here). bib entries added.
- [x] m1 README (build_anon_artifact.py generator) notes which permutation file the paper uses.
- [x] m2 Table III (E1) caption footnote for Gemma-3-27B constant-answer DSCR cell.
- [x] m3 "none occurred" wording for empty API responses.

## Close-out
- [x] Regenerated paper_numbers (1237 macros); compiled on scratch copy (texlive 2023) -> 10pp, 0 undefined ctrl seq, 0 undefined refs/citations, 0 overfull. PDF copied to paper/latex/.
- [x] Page budget: review additions pushed to 11pp; recovered to 10pp by lossless prose tightening + moving \appendix before \bibliography (standard IEEEtran order; fixed float pileup). No em-dashes, no scare quotes introduced.
- [ ] Rebuild anon_artifact (release/anon_artifact/*) so it ships the updated supplement.py/paper_numbers + new own-image I2 results; regenerates README + SHA256SUMS. (Artifact is stale re: M2 until rebuilt.) — pending.
- [ ] Commit (main-repo working tree holds this session's edits, uncommitted for user review).
