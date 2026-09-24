# Senior-reviewer 


What works well

  The paper asks an important question: does a correct medical VQA answer reflect information obtained from the image?
  The combination of text-only evaluation, image substitution, and evidence auditing is useful. Reporting majority-class
  baselines, patient-clustered uncertainty, and failures in the initial dataset also strengthens the paper. The worked
  patient example makes the limitations of answer accuracy tangible.

  The principal concerns, in order of importance, are:

  1. The supplied images may not contain enough information to answer the questions.

     At line 274 (paper/latex/acl_latex.tex:274), each timepoint is represented by one axial contrast-enhanced T1 slice.
     Yet LIL asks about whole-lesion volume changes, sometimes with precise percentages.

     Two independently selected maximum-area slices do not uniquely determine a three-dimensional volume change.
     Consequently, low performance could reflect insufficient input rather than failure to use available visual
     evidence.

     DSCR introduces an additional concern: RANO assessment incorporates information beyond a pair of images, including
     clinical status, corticosteroid use, and appropriate reference scans. Specify the criteria used for LUMIERE’s
     labels and whether the model receives their required inputs. The RANO consensus paper makes these dependencies
     explicit.

     Required revision: obtain expert judgments using exactly the model-visible inputs. Either supply sufficient
     imaging/context or restrict questions to findings reliably observable in the supplied slices.

  2. Same-patient continuity does not establish a causal reasoning chain.

     The gating section treats correctness at every preceding phase as necessary for valid downstream reasoning. That is
     an imposed scoring rule, not demonstrated causal dependence. A model can misidentify a sequence yet correctly
     identify a lesion; it can also answer every question correctly through independent shortcuts.

     The paper itself says DSCR labels remain unchanged after modifying the LIL baseline. This further underscores that
     the asserted dependencies require justification.

     Required revision: describe the structure as a same-patient sequential evaluation. To support causal claims,
     intervene on upstream context—correct, incorrect, and absent—while holding downstream inputs fixed. Measure whether
     downstream behavior changes appropriately. Also, a binary threshold that zeros downstream scores is operationally
     hard gating; “soft” needs explanation.

  3. The prognosis answer key confuses an observed outcome with a uniquely correct prediction.

     The worked example at line 385 (paper/latex/acl_latex.tex:385) marks approximately 12 months correct because the
     patient actually survived 48 weeks. A plausible nine-month forecast is marked wrong.

     An individual’s realized survival does not establish that one narrow forecast was the uniquely justified answer at
     the prediction date. The example also involves imaging at week 47 and survival measured from surgery, making the
     information cutoff particularly important.

     Required revision: define the prediction time, available information, and outcome horizon. Use an appropriate
     probabilistic survival task or clinician-validated risk categories. For TCM, similarly distinguish documented
     treatment from a justified treatment recommendation.

  4. The image-substitution experiment does not yet support its “below chance” conclusion.

     At line 345 (paper/latex/acl_latex.tex:345), 26/73 truth-tracking flips are compared against 50% chance. “Binary-
     ish” is not a defensible null model.

     The relevant probability depends on the answer options, their direction/category distribution, the original answer,
     and conditioning on a flip. Furthermore:
      - The original options may contain no fully correct answer for the substituted patient.
      - The donor’s RANO label may depend on clinical facts that were not substituted.
      - Responses share patients across models and phases, so the pooled Wilson interval ignores dependence.
      - AIA’s invariant answer does not make all image-induced changes pure decoding noise.

     Required revision: validate donor-compatible answer options, derive an item-specific or permutation-based null, and
     account for shared patients and donor reuse. Add repeated identical-input runs as the direct variability control.
     Until then, remove “below chance” and “decoding variance alone.”

  5. The evidence auditor cannot establish that copied claims were not visually verified.

     The paper acknowledges this limitation, but its conclusions still rely heavily on it. A model can inspect an image
     and correctly select wording already present in an option. Conversely, a novel fact matching the patient record
     need not have been inferred visually.

     The mutually exclusive categories also hide errors: the worked example’s false location becomes “copied” once
     repeated upstream.

     Required revision: score two separate dimensions: whether a claim was available in the text, and whether it is
     supported, contradicted, or unverifiable. Validate the audit against independent expert annotation. Report “no
     checkable claim” separately, with explicit denominators.

  6. The OmniBrainBench criticism needs more careful attribution.

     Your methods explicitly state that interpreting source_file as patient identity was your own KAB-side decision. The
     abstract and introduction nevertheless present the resulting failure as a construct-validity defect in
     OmniBrainBench.

     Its published abstract describes coverage of clinical tasks; that alone does not promise patient-linked
     longitudinal chains.

     Required revision: frame the finding as an incompatibility between the released benchmark and your proposed
     sequential evaluation unless you identify an explicit contrary claim. Replace “only 2 patients” with “only 2
     verifiable cross-phase patient links” unless identifier completeness is established. Shared images are also not the
     only possible evidence of patient continuity.

  7. The advertised framework is not supported by the reported experiments.

     The introduction claims adaptation distinguishes knowledge gaps from activation failures. The methods correctly
     explain why the current experiment cannot make that distinction. Gating is central to the framework but has no
     reported results; adaptation triggers only 1–4 times per model.

     Required revision: align the contributions with completed evidence. Either validate these components through
     appropriate controls or present them as exploratory extensions. Ontology coverage and answer recoverability should
     be named as vocabulary and consistency measures throughout, rather than promoted as causal faithfulness measures.

  Statistical and reporting corrections

  - Reconcile MedGemma’s table difference of approximately three percentage points with the patient-averaged difference
    of 1.9 points. With five scored items per patient, pooled and patient-mean differences should agree.

  - Explain rounding for Gemma-3-27B: the displayed 54% versus 50% yields four points, while the table reports three.
  - Replace comparisons against individual Wilson intervals with paired uncertainty for the actual difference.
  - Provide a timestamped preregistration artifact, including the ±8-point margin, or use “prespecified analysis plan”
    if that is what exists.

  - Report phase-specific image effects. Overall equivalence can conceal differences between visually dependent and
    largely textual tasks.

  - “Zero audit violations” establishes compliance with that auditor, not absence of leakage—especially when generation
    was optimized against the same rules.

  - Clarify whether upstream context is frozen across experimental arms or regenerated. These estimate different
    effects.

  - Clarify whether gating prevents execution or merely masks scores; both descriptions currently appear.

  How I would reshape the paper

  I would center it on “Auditing Image Dependence in Longitudinal Brain MRI Question Answering.” Shorten the abstract
  substantially, replace the duplicated accuracy bar chart with phase-level paired effects and uncertainty, and move
  dataset debugging history into an appendix.

  The next priority should be expert validation of answerability and answer keys, followed by corrected substitution
  controls and statistical analysis. Adding proprietary models would broaden coverage, but it would not resolve the
  current validity concerns.