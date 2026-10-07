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


---

Answering the actual question: yes, a second reference model is doable right now, no big lift.

- Most feasible choice: Claude-sonnet-4-5. It's already a configured reference slot, and the ANTHROPIC_API_KEY is present in .env. It's a different vendor from Gemini, which is the whole point — it de-confounds "maybe Gemini's success is a one-model quirk."
- GPT-5 is also slotted but we have no OPENAI_API_KEY, so that one's blocked without a key.
- Cost/effort: it's an API eval (no GPU) — roughly one run of E1+E2 on AIA/LIL/DSCR (~a few hundred image calls), maybe 30–60 min and a modest amount of API credit. Then regenerate macros/table and change "a reference model" → "two reference models" (and drop the "second reference model remains outstanding" caveat).
- What it buys: a second independent positive control (replicates task feasibility / items answerable from the slices; strengthens the reference-vs-open gap). What it doesn't buy: key validity — that's still clinician review only.
- Not required: the reviewer explicitly said they wouldn't demand a bigger model roster.

So: cheap-ish, genuinely strengthens the positive control, optional. If you decide you want it, say the word and I'll run Claude-sonnet-4-5 as the second reference. Not doing anything until then.