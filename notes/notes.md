Tsks

Pending:

1. ARR submission mechanics, unconfirmed part: submission-portal specifics (double-blind anonymization already fixed 2026-09-28 — see done list).
2. Code/data release plan — deferred to camera-ready, not urgent now.




---DO NOT TOUCH THIS -------

------MAIN------

1. Two of four open models fail their own positive control on AIA. By the paper's own preregistered rule, that means you can't claim anything about image-use for Gemma-3-12B/27B's LIL/DSCR — not "weak use," genuinely uninterpretable. That's a design/power problem, not a validation problem.
2. Nothing survives the Holm correction. Every per-model, per-phase result is, strictly, a null result after multiplicity adjustment. The "weak and inconsistent" story is real but statistically it's "we couldn't reject the null anywhere."
3. n=51-62 per cell is why both of the above happen — the intervals are just wide.

-----

The bottom line: you asked "can we get more data to make the results stronger?" I checked, and the answer is: not by adding more patients — that pool is basically used up already (62 of 64 possible). The only way to get more data is to squeeze more questions out of the same patients (each patient actually has ~3 usable timepoints, but the paper currently only uses 1). That's possible, but it's a real chunk of new work (redoing the data build, rerunning all 5 models), not a quick fix.

So really there are just two paths from here:

1. Do the extra work — pull more timepoints per patient, rerun everything, try to get stronger/more conclusive numbers before submitting.
2. Don't — keep the data as-is, and just be more modest about what the paper claims, sticking to the results that are already solid (like the Gemini control clearly using the image, or Scout's donor-tracking result) instead of leaning on the results that are weak/inconclusive.

---
Paper submission Link - https://2027.naacl.org/calls/main_conference_papers/

https://anonymous.4open.science/r/image-dependence-3D25/README.md
