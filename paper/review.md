# Manuscript review for NAACL 2027
Review — "Do Medical MLLMs Use the Image?" (v. compiled 2026-09-29)

Recommendation: borderline — accept as an honest methods/negative-result paper; reject if judged as a benchmark contribution. This is a careful, unusually transparent paper. Since the Sept-28 external review it has materially improved: I verified in the code that the two blocking mismatches are genuinely fixed, not just reworded (src/lumiere_measure.py:187 now enforces both diameters ≥10 mm; src/v4_conditions.py:191 injects the real rule text into the prompt for the explicit_rule condition). The numbers are macro-generated and internally consistent — I hand-checked the audit arithmetic (75/197 = 38 %; 59+13+2+1 = 75; 122 disagreements; the 46 CR-vs-PD split 22/8/16) and every phase count (AIA 46, LIL 38, DSCR 46 / 42-donor, TCM 46, PJRF 45). That discipline is paying off.

The remaining concerns are not fixable by more hedging — they are structural.

Major concerns

1. The load-bearing "feasibility" claim rests on a single, non-reproducible API model. Everything that establishes the tasks are answerable-from-the-image runs through Gemini-3.6-Flash: added post hoc, run once, unknown size/precision, "can change without notice." If a reviewer discounts that one endpoint, the empirical core reduces to 3 of 4 open models failing the AIA positive control at near-chance, one test surviving correction (and then explained away). A benchmark's validity should not hinge on an artifact a reader cannot rerun. Highest-value fix: add at least one reproducible reference model that reads the image (a strong open VLM in bf16 via vLLM). One more feasibility point hardens the single most important claim in the paper.

2. Near-chance sequence identification by 3/4 open models is a pipeline red flag the paper cannot rule out. "Which sequence is this?" is the easiest visual task in the set, yet MedGemma-4B, Gemma-3-12B and Gemma-3-27B all sit at ~26 %. The input check (token counts rise, probes pass) excludes a dropped-image bug but, as you state, cannot exclude that the encoder loses MRI contrast. So "open models gain little from the image" is still confounded with "4-bit Ollama serving degrades the image for these models." The one bf16 rerun (Gemma-3-27B) stayed at chance but confounds precision with serving stack, so it doesn't resolve it. This is the biggest threat to the open-model conclusion. Tie it off with concern 1: a bf16/vLLM open model that clears chance on AIA would attribute the gap to serving; one that stays at chance would make "genuine" much more defensible.

3. Novelty vs. existing perturbation protocols is asserted, not demonstrated. The real contribution — separating accuracy benefit / output sensitivity / donor tracking, and reading ablation against the answer prior — is sound and the Llama-4-Scout worked example illustrates it well. But the differentiation from HEAL-MedVQA and the VQA balancing line is "by design, not measured" (you did not run their protocol). A competitive reviewer will want the delta shown, not stated. The worked example is the right vehicle; consider making explicit "protocol X would score this as image-use; ours does not, because."

4. Clinician validation is still entirely outstanding, and this is the crux for anything called a medical benchmark. Neither the expert RANO labels (38 % reproducible) nor your automated keys are clinician-validated, so the "explicit key origin" contribution is really "explicit provenance of unvalidated automated keys." That is fine for an evaluation-methods paper and not fine for a benchmark paper. The current framing mostly stays on the right side of this line — keep it strictly there, and don't let DSCR/label-provenance language drift toward benchmark claims.

5. Power. 38–46/phase, one Holm-surviving test. Honestly reported, but the reader leaves with very few positive claims. Acceptable for an honest-negative paper if the abstract and title set that expectation — which brings up:

6. Title tension. "Do Medical MLLMs Use the Image?" asks a yes/no question the paper deliberately declines to answer ("we claim neither non-use nor learned shortcuts"). The title promises an internal-mechanism verdict the paper is careful never to give. A reviewer's "title overclaims" reflex is easy to trip here. Consider foregrounding the methodological question (e.g., "When Does an Image Ablation Measure Visual Tracking?") so scope and title agree.

Minor / writing

- Abstract is still one ~230-word block, 5 acronyms, takeaway last — the prior reviewer asked to compress and it largely wasn't. Lead with the method question + the one-sentence finding.
- The E1 results paragraph (p. 6) re-narrates Table 3 number-by-number; cut to interpretation.
- body_main.tex is still in the repo — the prior reviewer flagged the risk of accidentally submitting the stale narrative. Archive or delete before submission.
- Double-check no unqualified "tracks" language survives for open models (the reference-model "tracks swapped images" in the abstract is fine; the open-model donor results are correctly hedged as "interval above zero … not separable from a random donor").

Bottom line

The paper is now honest, internally consistent, and methodologically careful — a real turnaround from the Sept-28 version. Its ceiling at a competitive venue is set by two things it cannot hedge away: the feasibility claim depends on one irreproducible model, and the open-model null is confounded with the serving pipeline. If you can add one reproducible image-reading model (addressing 1 and 2 at once) before the Oct 12 ARR deadline, that single experiment does more for acceptance than any amount of rewriting. If you can't, lean fully into the honest-methods framing, fix the title, and compress the front matter.

---

Want me to (a) draft the specific reference-model experiment (which model + shell/lumiere/lumiere_v4.sbatch MODE=image, staying within the 2-GPU cap), (b) log this review into paper/update.md, or (c) start on the abstract/title compression? I'd prioritize (a) given the deadline.
