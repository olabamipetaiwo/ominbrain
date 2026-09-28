Shared/administrative (needed regardless, but relevant now)

2. Close the 4 open ARR checklist items: code/data release plan, IRB determination, whether to cite arXiv-only model reports, a named LUMIERE license.
3. Decide PJRF: keep as secondary appendix result, or drop it entirely — this decision shapes how much of the rewrite touches PJRF.
4. Confirm ARR 2026-10-12 deadline mechanics (submission portal, anonymization/double-blind requirements, whether Limitations/appendices count toward the page limit).

The narrowing itself

5. Identify exactly which results are solid enough to be load-bearing:
   - Gemini control's E1 (AIA/LIL image effect) and E2 (donor tracking) — both reported outside the Holm family, so not weakened by multiple-comparison correction.
   - Llama-4-Scout's donor-tracking result (LIL +23.5, AIA +12.9) — the one open-model result whose CI clears 0.
   - Everything else (the other 3 open models' E1/E2, all of E3/E4/E6, PJRF) gets explicitly downgraded to "inconclusive" or "secondary," not reframed as weak-positive findings.
6. Rewrite the Abstract around that narrower claim: the method (positive control + donor-swap design) works and detects real image-use when it's present (Gemini); applied to open models, it mostly could not detect reliable image-dependence, with one exception (Scout).
7. Rewrite the Results section paragraph-by-paragraph, removing any sentence whose evidence doesn't clear the bar from step 5 — this is the biggest chunk of work, since several paragraphs currently describe "weak but present" effects for models that fail their own positive control.
8. Rewrite the Introduction/contributions bullets to match — drop any framing that implies a substantive finding about the 3 non-Scout open models beyond "no evidence detected."
9. Rewrite the Conclusion to state the narrowed claim plainly, without hedging language that implies more than the data support.
10. Tighten Limitations to foreground: small n (51–62), 2 of 4 open models fail their own positive control (so nothing can be claimed about them at all under the preregistered rule), nothing survives Holm among the open models, no clinician validation of the audit.
11. Sweep the rest of the paper (worked example, appendix tables, any remaining hand-written sentences) for leftover claims that assume the results being cut in step 5 — this is exactly the kind of drift a claim-audit pass would catch, so probably worth one more full audit pass over acl_latex.tex before calling it done.
12. Recompile and recheck the page count (cutting weak claims may shrink it, which could free up room for the input-handling / reviewer-point-7 detail that's currently thin).
13. Update paper/update.md with a change-log entry describing the narrowing and why.



------MAIN------

1. Two of four open models fail their own positive control on AIA. By the paper's own preregistered rule, that means you can't claim anything about image-use for Gemma-3-12B/27B's LIL/DSCR — not "weak use," genuinely uninterpretable. That's a design/power problem, not a validation problem.
2. Nothing survives the Holm correction. Every per-model, per-phase result is, strictly, a null result after multiplicity adjustment. The "weak and inconsistent" story is real but statistically it's "we couldn't reject the null anywhere."
3. n=51-62 per cell is why both of the above happen — the intervals are just wide.

-----

The bottom line: you asked "can we get more data to make the results stronger?" I checked, and the answer is: not by adding more patients — that pool is basically used up already (62 of 64 possible). The only way to get more data is to squeeze more questions out of the same patients (each patient actually has ~3 usable timepoints, but the paper currently only uses 1). That's possible, but it's a real chunk of new work (redoing the data build, rerunning all 5 models), not a quick fix.

So really there are just two paths from here:

1. Do the extra work — pull more timepoints per patient, rerun everything, try to get stronger/more conclusive numbers before submitting.
2. Don't — keep the data as-is, and just be more modest about what the paper claims, sticking to the results that are already solid (like the Gemini control clearly using the image, or Scout's donor-tracking result) instead of leaning on the results that are weak/inconclusive.
