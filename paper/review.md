# Manuscript review for NAACL 2027

Review date: September 28, 2026. Perspective: a rigorous CS/NLP faculty reviewer; this is an independent assessment, not an institutional endorsement or an official ARR review.

**Recommendation: major revision; lean reject in the current form.** There is a useful empirical evaluation paper here, especially in distinguishing accuracy benefit, output sensitivity, and correct donor tracking. However, two implementation-to-manuscript mismatches undermine interpretation, and the main answerability premise still needs independent evidence. More qualifications alone will not resolve these issues.

## Scope and confidence

Reviewed the active manuscript `paper/latex/acl_latex.tex`, its generated tables and worked example, the preregistration and checklist, and relevant item-construction, prompting, measurement, and statistics code. `body_main.tex` contains an older narrative and is not included by the active manuscript. I did not edit the manuscript or analysis code.

The local `results/` directory does not contain the v4 raw runs or aggregate statistics referenced by the paper. The v4 measurement caches and item records were also unavailable in the inspected checkout. Therefore, the generated tables are reported evidence, not independently reproduced evidence. I can verify code-level mismatches but cannot count their affected patients. There is no current compiled manuscript PDF in `paper/latex`; its compilation log is dated September 23 and predates the reported September 25 runs. I cannot certify layout or the eight-page content limit from those artifacts.

The official [NAACL 2027 call](https://2027.naacl.org/calls/main_conference_papers/) confirms ARR submission and author reviewer registration on **October 12, 2026, 23:59 AoE**, followed by NAACL commitment on December 23. Long submissions have an eight-page content limit. The topic fits clinical NLP, multimodality, and evaluation; venue fit is not the main problem.

## What works

1. The three-outcome distinction is valuable. A model can change its answer without improving accuracy, and accuracy can improve without proving the intended reasoning mechanism. The current manuscript generally respects this distinction.
2. Donor swaps with a different available answer are stronger than arbitrary image substitutions. Subtracting the text-only donor-key hit rate is a sensible way to expose the prior's contribution.
3. The reference-model results give the study a concrete positive finding: reported AIA accuracy is 93.5% versus 24.2% without images; LIL is 100% versus 33.3%. This supports feasibility for those tasks, although it does not independently validate the labels.
4. The manuscript discloses exploratory analyses, quantization/serving confounds, unsupported clinical interpretations, and changes to the initial analysis plan. Preserve that transparency.

## Major concerns, in priority order

### 1. The DSCR key does not implement the measurability condition given to models

**Evidence:** `src/lumiere_measure.py:151–168`, especially line 161, determines measurability from `bidimensional_product >= 100`. The DSCR question in `src/lumiere_v4.py:311–316` tells models that a lesion must measure at least 10 mm by 10 mm. The manuscript repeats the latter condition.

These are not equivalent. A lesion measuring 20 by 6 mm has product 120 mm² and passes the implementation while failing the stated two-diameter criterion. The function receives only products, so it cannot recover whether both diameters meet the threshold. This can affect inclusion, response categories, disagreement with the expert, downstream management keys, cohort selection, and donor matching.

There is a second, distinct clinical-definition issue: the implementation calls any follow-up below its measurability threshold a complete response when the baseline is measurable. Residual enhancing disease can therefore be labeled complete response. The [original RANO paper](https://neuroradiologi.dk/onewebmedia/Updated%20RANO.pdf) requires disappearance of enhancing disease, including nonmeasurable disease, with additional conditions. A simplified computational task is legitimate, but it must be distinguished explicitly from clinical RANO. Disclosure that clinical status and steroids are omitted does not explain the product-versus-diameters mismatch.

**Required action:** decide whether the target is a deliberately stipulated geometric rule or an approximation to RANO. Make the prompt, implementation, and description agree. Recompute affected labels and selection, report how many change, and rerun affected conditions if prompts, membership, or donors change. Keep the original runs as a separately versioned analysis; do not silently overwrite the preregistered experiment. Audit the perpendicular-width calculation and cross-timepoint lesion correspondence while doing this: the current width is a projection extent, and independently selecting the largest component need not track the same lesion.

### 2. TCM is described as explicit rule following, but the rule is not in the model-visible prompt

**Evidence:** `src/lumiere_v4.py:355–361` places the rule in `tcm_rule` metadata, while the question asks what the most appropriate next step is. `src/prompts.py:104–144` builds the prompt from the question, options, and upstream context; it does not inject `tcm_rule`. `src/v4_conditions.py:107` uses this builder. The worked example shows the same clinical question and explains the rule separately.

The manuscript says the test concerns following an explicitly stated management rule. The inspected implementation instead tests a clinical recommendation against an author-defined rule that the model must infer or supply from prior knowledge. Below-lookup accuracy cannot establish failure to follow instructions that were never supplied. Timing flips still measure response sensitivity, but agreement with the stipulated key is not a clean rule-following metric.

**Required action:** add an explicitly rule-provided TCM condition and rerun it, retaining the original as a separate implicit-rule condition. Alternatively, remove the rule-following claim and narrow interpretation to agreement with an unvalidated heuristic. The explicit condition is the stronger repair and is text-only. Ensure its system prompt permits reasoning from supplied facts: the shared prompt currently directs even text-only TCM/PJRF questions to rely on directly observed image features.

### 3. Independent answerability validation is central, not optional polish

The framing argues that image-removal tests require answerable questions. Yet LIL and DSCR keys come from unseen automated masks, and no clinician has judged whether the displayed inputs support them. High reference-model agreement is useful feasibility evidence, but it is not an independent ground-truth audit. Sequence provenance also identifies the source acquisition without guaranteeing that every individual slice is visually distinguishable.

The automated audit's 130/231 determinate agreement (56%, or 130/268 = 49% including abstentions as failures) is agreement with your rule. It does not establish that the remaining expert labels are wrong or unanswerable. The current manuscript acknowledges this, but still gives the statistic disproportionate prominence in the abstract and contribution list.

**Required action:** have qualified readers assess exactly the images, stems, and options shown to models, initially blinded to model outputs and generated keys. Ask separately whether the item is answerable, which answer is supported, and why it is ambiguous. Ideally validate all 51 LIL and 62 DSCR items; at minimum use a prespecified stratified sample and report its limitations. Include representative agreement and disagreement cases from the original audit. Report independent agreement before adjudication, uncertainty, and whether errors arise from segmentation, rendering, target choice, or missing evidence. If qualified review is unavailable, substantially narrow the benchmark-validity claim and the prominence of DSCR.

### 4. Sparse-data inference needs repair and clearer scope

**Bootstrap versus exact test.** MedGemma AIA has five patients correct only with images and zero correct only without them. Its reported percentile-bootstrap interval excludes zero, but the two-sided exact McNemar p-value is 0.0625 before multiplicity adjustment. The manuscript distinguishes its operational gate from Holm significance; nevertheless, the gate can pass when even the unadjusted exact test does not. Do not present gate passage as statistically established image competence.

**Degenerate interval.** Gemma-3-27B's E2 DSCR gain is reported as 0.0 with interval [0.0, 0.0]. `tools/lumiere_v4_stats.py:75–80` resamples observed paired differences. If all observed differences are zero, this procedure cannot represent unobserved discordant outcomes. This is an observed bootstrap degeneracy, not proof of zero population uncertainty. Add a paired-binomial interval suited to sparse discordance as a sensitivity analysis and qualify equivalence claims.

**Repeated visits in the audit.** `tools/lumiere_v4_supplement.py:35–49` applies an ordinary Wilson interval to agreement across longitudinal follow-ups. These include multiple visits per patient, unlike the one-follow-up-per-patient model experiment. Use patient-clustered uncertainty for the audit, and report the patient count as well as visit count.

**Donor dependence.** `src/lumiere_v4.py:400–424` permits each patient to donate to two recipients. E2 resamples recipient differences only. State whether inference is conditional on the fixed donor assignment or intended to generalize over patients and assignments; examine donor reuse and perform an appropriate dependence/assignment sensitivity analysis. Do not assume pair-level resampling covers both estimands.

**Multiplicity.** E2 positives are unadjusted and described as descriptive, but “clearly tracks” appears prominently in the abstract. Prefer “positive unadjusted intervals” or equivalent wording, show exact tests and an explicitly exploratory multiplicity sensitivity analysis, and preserve the original preregistered family.

### 5. The strongest evidence is narrower than the five-phase framing

The paper's own “What the chain adds” paragraph concedes that its clearest findings concern individual AIA/LIL questions. Manufactured upstream context plus a management question can test context use without demonstrating a multi-stage reasoning contribution. PJRF has unverified time origin/censoring; DSCR remains unresolved even for the reference model; TCM needs the repair above.

Existing work already studies image necessity and perturbation in medical VQA. In particular, [HEAL-MedVQA](https://www.ijcai.org/proceedings/2025/0853.pdf) introduces textual and visual perturbations with radiologist annotations. The manuscript cites it, but “we use a chain” is not sufficient differentiation if the chain adds little reliable evidence.

**Required action:** lead with a precise methodological question: when does an image intervention measure correct visual tracking rather than merely response sensitivity? Identify which design choices improve interpretability relative to prior protocols and demonstrate that improvement with a worked failure case. Treat the patient chain as an extension unless corrected TCM results establish a substantive additional finding. A new architecture is unnecessary; a clear, validated empirical insight is necessary.

## Additional revisions

- Reframe the RANO disagreement as a construction audit motivating validation, rather than the headline discovery. Prefer the determinate denominator as the primary agreement number and report coverage separately.
- Compress the abstract substantially. It currently carries five acronyms, construction history, audit qualifications, controls, and several outcomes before establishing the central takeaway.
- Move most v3 history, KAB discussion, and OmniBrainBench compatibility details out of the main narrative. Avoid organizing the scientific argument around internal version names.
- Retain the finding that no open-model E1 test survives Holm correction. Avoid interpreting this as evidence of absence; several intervals admit practically meaningful gains.
- Correct the Limitations sentence saying the bf16 result “argues against quantization as the main cause.” The main Results appropriately says precision and serving stack changed together and a null result does not isolate quantization.
- Describe LIL exclusions exactly: the code allows limited midline crossing if at least 80% of component pixels are on one side, whereas the manuscript says crossing lesions are excluded.
- Treat the E3 moved/informative rates carefully in model comparisons: informative denominators differ by model because conditioning depends on its original answer. Show full transitions and the prespecified original metric alongside the revised one.
- State donor reuse and matching details, class counts, and item exclusions in an accessible dataset summary. AIA is approximately balanced at 16/16/15/15; text-only accuracy has chance expectation under independence, not an exactly fixed 25% realization.
- PJRF should remain noncentral. Without resolving outcome origin and censoring, it is not a validated prognosis evaluation. Removing it from the main table and narrative would improve focus.
- Provide an anonymous artifact with item manifests, exact serialized prompts, donor assignments, model response provenance, analysis versions, and a deterministic table-generation command. Local paths in the paper are not usable supplementary material for reviewers. The model loader lets later records replace earlier ones, so include a run/override manifest.
- Model names and digests support identification; appropriate model reports/cards support scholarly attribution. Reconsider the manuscript's blanket exclusion of non-peer-reviewed references instead of treating it as a conference requirement.
- Rebuild from the current canonical source and inspect every page. The old log and checklist cannot establish current pagination. Remove or clearly archive the unused older `body_main.tex` to prevent accidental submission of stale claims.

## Revision plan to October 12

| Dates | Priority | Concrete deliverable |
|---|---|---|
| Sept 28–30 | Resolve validity blockers | Retrieve raw artifacts; reconcile DSCR definitions; quantify affected items; freeze a versioned correction plan; recruit qualified readers. |
| Oct 1–5 | Produce decisive evidence | Complete independent item review; run explicit-rule TCM; rerun affected DSCR/downstream conditions; complete sparse-data and dependence sensitivity analyses. |
| Oct 6–8 | Rewrite around supported contribution | Tight introduction, shorter abstract, validated primary tasks, clear separation of original and corrected analyses, compact comparison with closest prior work. |
| Oct 9–11 | Verify submission | Regenerate all numbers, build and visually inspect the PDF, check anonymous artifact access, references, checklist, and registration requirements. |
| Oct 12 | Submit | Submit to ARR by 23:59 AoE; confirm the author reviewer-registration requirements in the official call. |

My priority would be **validating labels and aligning prompts with claims before adding more model runs**. A narrower paper with defensible targets, a coherent statistical story, and one useful evaluation insight will be stronger than a larger collection of qualified results. Acceptance remains uncertain even after those repairs; novelty and scope would still need a convincing argument.




The strongest contribution is separating **accuracy benefit, answer sensitivity, and correct donor-image tracking**. Those quantities distinguish behaviors that ordinary accuracy conceals. The reference model’s reported image-dependent performance also gives the study a useful positive result.

Five issues need attention:

1. **The response-category implementation disagrees with the stated task.** The prompt requires two perpendicular diameters each at least 10 mm, but the code checks whether their product is at least 100 mm². A 20 × 6 mm lesion passes the code and fails the prompt. This could affect labels, cohort selection, donor matching, and downstream results. The number of affected cases needs to be measured.
2. **The management rule is not actually supplied to the model.** The paper describes testing an “explicitly stated” rule, but the prompt asks for the most appropriate clinical next step; the rule sits in metadata that the prompt builder does not include. Consequently, poor performance does not establish failure to follow that rule. An additional condition with the rule explicitly supplied would resolve this cleanly.
3. **Answerability remains insufficiently validated.** Your central argument requires questions whose answers can be recovered from the displayed images. Yet the lesion and response-category keys depend on automated masks without independent clinician review. Strong reference-model performance supports feasibility, but does not replace independent validation. This is the highest-value additional evidence to obtain.
4. **Some statistical interpretations are fragile.** For example, MedGemma’s sequence task has five image-only successes and zero text-only successes: its bootstrap interval excludes zero, but its two-sided exact McNemar p-value is **0\.0625**, even before correction. Another donor-tracking interval collapses to **\[0, 0\]** because of bootstrap degeneracy. The longitudinal audit also needs uncertainty that accounts for repeated visits within patients.
5. **The five-phase framing exceeds the strongest evidence.** Your clearest findings concern sequence identification and lesion localization. The chain contributes less convincingly, prognosis has unresolved outcome definitions, and management needs the prompt correction. I would organize the paper around the evaluation insight and make the chain a supported extension.

**My submission advice:** prioritize correcting the label/prompt mismatches and obtaining independent item validation before adding more models. Then shorten the narrative around the strongest supported finding. The full review includes specific code locations, statistical repairs, writing changes, and a September 28–October 12 schedule.


