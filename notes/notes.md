The round-3 (lumiv4) results show three solid findings: accuracy falls sharply after the first phase, no model beats a trivial baseline on response assessment, and labeling the LIL images helped every model. Everything else is inconclusive so far. These results come from the 54 LLM-drafted items, which the expert still hasn't reviewed, so they are preliminary.

Accuracy without gating (every question scored):

┌───────────────┬─────┬─────┬──────┬──────┬─────┬─────────┬────────────────────┐
│     Model     │ AIA │ LIL │ DSCR │ PJRF │ TCM │ Overall │ Full chain correct │
├───────────────┼─────┼─────┼──────┼──────┼─────┼─────────┼────────────────────┤
│ Llama-4-Scout │ 96% │ 50% │ 59%  │ 54%  │ 74% │ 67%     │ 15%                │
├───────────────┼─────┼─────┼──────┼──────┼─────┼─────────┼────────────────────┤
│ Gemma-3-27B   │ 80% │ 59% │ 61%  │ 39%  │ 72% │ 62%     │ 4%                 │
├───────────────┼─────┼─────┼──────┼──────┼─────┼─────────┼────────────────────┤
│ Gemma-3-12B   │ 89% │ 48% │ 63%  │ 35%  │ 65% │ 60%     │ 2%                 │
├───────────────┼─────┼─────┼──────┼──────┼─────┼─────────┼────────────────────┤
│ MedGemma-4B   │ 54% │ 52% │ 39%  │ 33%  │ 46% │ 45%     │ 4%                 │
└───────────────┴─────┴─────┴──────┴──────┴─────┴─────────┴────────────────────┘

What holds up:
1. Accuracy drops after AIA: 80–96% on AIA, then about 50–59% on LIL. Almost no pati2–15%), and Llama-4-Scout does best.
2. Labeling the images for LIL helped every model. Compared with round 2, LIL rose by 17 points for Scout, 9 for Gemma-12B, 5 for Gemma-27B and 6 for MedGemma. The other phases stayed about the
   same. So part of the earlier LIL weakness was how the images were presented, not
3. On DSCR, every model is at or below the 65% majority baseline. Always answering "progressive disease" does as well or better, so nothing here shows real response-assessment skill.
4. MedGemma-4B, the only medical-tuned model, comes last. Medical tuning at 4B doesn27B.

What we can't claim yet:
- AIA is inflated. The correct answer is the same for all 54 patients, so the phase tests whether a model avoids naming a wrong imaging sequence, not whether it can read the scan.
- Gating gives mixed results. Among questions whose earlier phases were answered corPJRF and TCM, but Gemma-12B's PJRF drops from 35% to 8%. The gated question countsare 1–15, so the confidence intervals overlap heavily.
- "Right answer for wrong reasons" has almost no support here. There are only 0–3 ca
- With 54 patients, confidence intervals are about ±13 points, so most differences between models aren't significant. Scout's lead is suggestive, not established.

--------------


Our results don't show that the finding is absent. They show that neither of our metrics can detect it, so the claim is untested rather than refuted.

Why the counts are near zero:
- The self-check can't catch it by design. The "unfaithful" flag works by having the same model read its own reasoning and guess which answer it picked. In 72% of answers (781 of 1,078), the reasoning already restates the chosen option, so the model nearly always guesses right. It flagged 4 of roughly 1,000 correct answers. This measures whether the model is consistent with itself, not whether its reasoning is correct.
- The knowledge-base vocabulary check measures word choice, not reasoning. It flags 25–47 correct answers per model in AIA, where the answer is a fixed list of MRI sequence names. It flags 0–6 in LIL and 0–1 in every later phase.

Ways forward, in the order I'd do them:
1. Fact-check the reasoning against the patient facts (no GPU needed). LUMIERE already gives us ground truth per patient in data/lumiere/facts/: which hemisphere and region the tumor is in, its volumes, whether it grew or shrank, and the response rating. A case counts as "right for wrong reasons" if the answer is correct but the reasoning contradicts those facts, such as naming the wrong hemisphere or saying the tumor shrank when it grew. This is the direct test of the claim, and it runs on the results we already have.

2. Run the models without images. run_lumiere.py --text-only already exists. If accuracy stays up without the images, those correct answers weren't coming from the scans. Reviewers find this kind of blind baseline hard to dispute, and it costs about 4 non-gated GPU jobs.

3. Swap or flip the images. Give each question another patient's scans, or mirror them left to right. If the answer doesn't change when it should, the model isn't using the image. This is the strongest test and the most work.

If all three come up empty, drop the claim and build the paper around what the data does show. No model beats a trivial "always answer the most common option" baseline on DSCR, and there's no sign that errors carry forward along the chain. That's an honest paper about whether this kind of benchmark measures what it claims to, not about unsafe models, and it needs collaborator agreement. 

-----

### Plan

#### Question: When a model gets a LUMIERE question right, is the answer supported by the image, by the question text, or by neither?

#### Step 1: Audit what the question text gives away (no GPU, about an hour)
- For all 269 items, check whether the stem contains the facts that decide the answer: hemisphere or region, volume change, measurements, response rating, earlier answers.
- Result: a per-phase table of how many stems give the answer away. This explains the missing error propagation, and we'd want it for the paper either way.

#### Step 2: Run the 4 models without images (GPU, about 2.5h wall time)
- run_lumiere.py --text-only, non-gated only, all 4 models run in parallel.
- Compare accuracy per phase: with images vs text only vs the most-common-answer baseline.
- A correct answer that still comes out without the image doesn't depend on the image.

#### Step 3: Check the reasoning against the patient facts (no GPU)
- Check each correct answer's visual_grounding and reasoning against data/lumiere/facts/: hemisphere and region, grew or shrank, volumes, response rating.
- Sort each claim three ways: copied from the stem, contradicts the facts, or correct and not in the stem. Only the last one is real image evidence.
- The main focus is LIL, where the image is actually needed. DSCR, PJRF and TCM mostly restate the stem.
- Method: simple rules for hemisphere, direction and numbers, which can be reproduced. A model-as-judge is used only if the rules miss too much, and we'd then spot-check it by hand.

#### Step 4: Test with swapped or flipped images 
- Only if Steps 2–3 leave it unclear: give LIL another patient's scans, or mirror thther the answer changes.

What would count as each outcome (agreed before we look at results):

** Text-only accuracy within the CI of with-image accuracy, and many "correct" answers cite image evidence that  was copied or wrong -  Supported: the models are right because of the text, not the image. This is the safety angle.

** Accuracy drops clearly without images, and the image claims check out against the facts - Not supported: drop the claim and reframe around the validity findings

** Stems give away most later phases -  The benchmark needs stems rewritten before any propagation claim. Need collaborator review

----

What KAB is, mechanically: a phased eval harness (AIA→LIL→DSCR→PJRF→TCM) plus three add-ons layered on top of raw accuracy — faithfulness probing, KB-alignment/grounding checks, and soft-gating/chain-completion tracking. The causal-degradation hypothesis was one thing you could point that machinery at. It wasn't the machinery itself.

What that machinery has actually demonstrated it can do, independent of whether degradation shows up:

1. It caught a non-grounding problem that plain accuracy would have hidden. If you'd only run standard per-question MCQ accuracy on LUMIERE, everything would look fine — models score 33-67% on hard clinical reasoning questions, looks like a normal capability paper. It took KAB's specific machinery (faithfulness probes → forced the "is the reasoning even checkable" question → led to the text-only ablation and evidence fact-check) to reveal that the accuracy numbers don't mean what they look like they mean. That's the pitch: KAB is a diagnostic instrument for detecting when a benchmark's accuracy is not measuring what it claims to measure. That's a more general and arguably more publishable contribution than "chains degrade," because it's a methodology problem that applies beyond this one dataset — anyone building multimodal medical MCQs is at risk of exactly this leak-and-shortcut failure mode, and KAB's audit trail (stem-leakage rule, text-only arm, evidence-vs-facts checker) is a reusable recipe for catching it.
2. The chain-completion collapse is still a real, still causally-flavored finding — just a different mechanism. No error propagation (upstream-wrong doesn't predict downstream-wrong), but chain completion is still terrible (1-15% of patients get all 5 phases right). Models aren't failing because errors compound — they're failing because each phase independently has a decent chance of going wrong, and getting 5-for-5 is unlikely under any independence assumption. That's a legitimate "sustained multi-step clinical reasoning is hard" finding, just not the specific causal-chain story. Worth keeping, reframed.
3. DSCR sitting at/below its own majority baseline (found via KAB's new MajBase reporting) is a finding standard accuracy reporting would have completely missed and misrepresented as "the model shows some RANO skill." That's KAB's grounding/baseline-hygiene layer doing real work.
4. The two datasets triangulate the same story. OmniBrainBench couldn't even test the causal-chain claim properly (2/6823 real chains) — that's why LUMIERE got built. LUMIERE, built specifically to test it properly, still doesn't show degradation. That consistency (built better, still null) is itself informative: it's not an artifact of bad chain data, it's a real property of these models on this task.

So the reframed pitch, concretely: KAB isn't "the framework that proves multimodal LLMs degrade across causal chains" — it's "a phased evaluation framework whose faithfulness/grounding/completion layers surface why raw accuracy on clinical MCQs is misleading: not because reasoning degrades downstream, but because models often aren't using the images at all, and even correct chains rarely sustain across all 5 phases." That's the safety-signal reframe your notes already flagged as needed — this LUMIERE work is what actually earns it, rather than asserting it on the OmniBrainBench "right for wrong reasons" 4-count that was too weak to support.

This is a real pivot in the paper's central claim, though, not a wording tweak


-----

feedback adaptation loop -Why nothing's been written up about it: it only fires when a phase's output fails the faithfulness check — and faithfulness failures are rare by design (recall: local_faithful flagged ~4 of ~1,000 correct answers project-wide; kb_alignment_faithful mostly only trips on AIA). So out of 52 questions per phase, it's triggering 0-6 times per full run. At n=1 you get "100%" or "0%" — that's not a rate, it's a coin flip's worth of data. It's technically present in the machinery, but there's currently nowhere near enough signal to report a real adaptation-rate finding.

To make it usable, the options are:
1. Pool across all rounds/item-sets/models we've already run (v2 round1-3 + v3, all 4 models) to get a bigger combined N of triggered questions and see if a real rate emerges — cheap, no new compute, just an aggregation script.
2. Deliberately construct a test that forces more unfaithful outputs (e.g., a harder or adversarial item subset) so the adaptation loop actually gets exercised enough times to say something — more work, and changes what's being measured.

Given it's a named contribution of KAB (per the framework description above), I'd lean toward doing #1 first since it's just aggregation over data we already have — want me to write that pooling script and see what N we can get?

------

- Repeated-run control: MedGemma-4B and Gemma-3-12B.
- Gating-causality: MedGemma-4B (3h25m) and Gemma-3-12B (5h09m).
- All four counterfactual (lumicf_*) runs.

What's left
- Once the two Llama-4-Scout jobs finish, all four models will have both experiments.
- I still need to write the small compile script for rep1-vs-rep2 flip rates. It isn't written yet, so the repeated-run results aren't analyzed.
- The gating-causality results also aren't in the paper yet. Sec. 7 has design text only (sec:gating-causality).
- Earlier today's work on the round-2 review is already in the paper. update.md records two headline results that changed:
  - Substitution test: the "below chance" claim is reversed. It's now +11.9pp above an item-spec

-----

The paper is moving from a benchmark that measures causal degradation across the chain to a measurement-validity paper. It now asks whether these benchmarks and their metrics show that models use the image and the earlier phases at all. 
The results so far support that framing and don't support the original one.

The original claim
- Claim: reasoning degrades across the five phases for the same patient, and KB-grounded faithfulness and feedback adaptation measure this.
- Why LUMIERE: OmniBrainBench only has 2 real cross-phase links out of 6,823 questions, so we built a real same-patient chain dataset from LUMIERE.
- Where it's weakened: the results no longer show clean degradation. Your professor's expectation and the title, "Evaluating Causal Clinical Reasoning", still assume that claim.

What the results now say
- Image dependence is weak.
  - Text-only accuracy is within about ±8pp of image-present accuracy, and no per-phase cell is clearly above zero.
  - Stated evidence mostly repeats text the model was shown.
  - Answers that flip under a swapped image match the donor patient only modestly above item-specific chance (34% vs 22%). That reversed our earlier "below chance" claim.
- Context dependence is confined to one phase. In the gating-causality runs, the wrong-context effect shows up at TCM in both models so far, with no detectable effect at LIL or PJRF. Gemma-12B at DSCR goes the wrong way: correct context hurts, with a paired p of .008 (uncorrected). Errors don't propagate down the chain in any simple way.
- Decoding is deterministic. Rep1 and rep2 give identical answers for the two finished models, so the flips we see come from the input.

Where this leaves the contributions
- Still standing: the LUMIERE chain dataset (the first same-patient chain dataset we know of), the construction method, and the finding that OmniBrainBench can't support same-patient chains.
- Weaker: the KAB framework. The abstract already flags adaptation and gating as exploratory and calls the metric "vocabulary and consistency" instead of faithfulness.
- Weakest: "causal degradation" as a headline result.

Open decisions
- Framing: the reviewer's proposal to reframe around continuity, leakage and image dependence is listed in paper/review.md as a decision for Prof. Wang. I'd take it, because it fits what the data says. It's a change from what she approved, so she has to sign off.
- Clinician validation: the paper's remaining weak point is that the answer keys and single-slice answerability aren't clinician-validated. That blocks several fixes and is the same bottleneck as the expert review of the LUMIERE items. Nothing we run on the cluster will fix it.
- TCM leakage: TCM is our clearest context effect, but it may be leakage, not reasoning. Someone should check whether the true upstream answers give away the treatment answer before we call it context dependence.
- Venue: NAACL 2027 is the target, and I haven't looked up the deadline.

Next steps on our side
1. Wait for the 27B and Scout jobs, then re-run lumiere_gating_stats.py.
2. Check the TCM leakage question.
3. Bring the reframing proposal to Prof. Wang, with the gating-causality table as the evidence.


--------

What the data shows

The TCM effect is partly, but not fully, a lookup on the DSCR label.

1. The TCM key follows from the DSCR key by construction. The drafter prompt says the correct management "follows from this patient's actual disease course". I classified each correct TCM option as escalate, continue or stop with a keyword regex, so it's approximate. The DSCR key predicts that class for 48 of 52 patients. Progressive disease maps to escalate for 31 of 35 patients, and stable disease, partial response and complete response map to continue for all 17.
2. The label doesn't always fix the letter. In 30 of 52 items a distractor is in the same class as the key. So the label alone is a strong hint
3. Gemma-3-12B follows the injected label. On the 35 patients whose DSCR key is progressive disease, it picks an escalate-class option:
   - 25 of 35 with correct context;
   - 15 of 35 when the DSCR label is forced wrong (the alphabetically-first wrong option, which for these patients is "Stable disease");
   - 13 of 35 with no context.
4. MedGemma-4B doesn't follow it. It picks escalate 8 of 35 times under both correct and wrong context, and mostly picks "continue" regardless. Yet its correct-vs-wrong TCM gap has 9 items right only under correct context and 0 the other way. The class shift doesn't explain that gap, so I don't have an explanation
   for it yet.

What it means

- Not leakage in the cheating sense: by design, TCM depends on the prior disease state. The DSCR answer is supposed to inform treatment.
- Not evidence of chain reasoning either: in Gemma-12B, "TCM depends on upstream context" mostly reduces to "the model reads the RANO label and maps it to a treatment". That is a lookup, not a causal chain built from the images.

What's left to check

- Ablation on the GPU: rerun TCM with only the DSCR entry in the injected context, then with everything except DSCR. If DSCR-only recovers the full effect, it's the label. If the other phases matter, it's broader. This needs a small change to src/gating_causality.py, and I'd add a --context-subset flag.
- Label-only version: inject the bare label with no reasoning text, to separate the label from any wording overlap with the options. This may ex
- A real tool: replace my regex classifier with one that reads the class from the drafter's structured output or the review file. The current numbers come from an ad hoc script and aren't reproducible from the repo yet.
- Expert view: ask the clinician whether the TCM options really turn on the RANO category. That also feeds the blocked prognosis and TCM key val

Under the cap, the ablation runs as two extra jobs after the current chains finish

------

Next steps
1. Wait for the running and queued jobs, then run lumiere_gating_stats.py and add an options-only section to it.
2. Rewrite the title, abstract, contributions and intro around shortcut learning, using the finished numbers.
3. Rebuild the figures so the shortcut evidence is the centre: a per-phase decomposition of options, then stem, then image, then context.



-----
Steps after the run


1. Check that every job finished cleanly, including the group-limited lumirep_Llama-4-Scout (43091110), which may run last.
2. Run python -m tools.lumiere_gating_stats for the complete repeated-run, gating-causality and TCM ablation tables.
3. Add an options-only section to that tool, since it isn't compiled yet, and run it.
4. Report what the four-model results say for the shortcut framing before we touch the paper text.