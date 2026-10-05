# AI evaluation: an expert knowledge map and a guide to this project

Prepared 5 October 2026 for a PhD researcher building toward industry AI evaluation roles.

This document answers two questions:

1. **What should an excellent AI evaluation researcher understand, broadly and technically?**
2. **What must you understand to explain, repair, and defend this image-dependence project?**

Expertise means being able to define the claim, design a measurement, identify alternative explanations, implement the evaluation correctly, and explain which decision the evidence supports. Knowing benchmark names or running a leaderboard is only a small part of that skill.

The concepts below are a curriculum, not a claim that one person must specialize equally in every area. The suggested order and exercises are tailored recommendations. Linked papers provide scientific foundations and examples; they do not endorse every recommendation here. Foundational readings are intentionally included alongside newer work.

## How to use this document

Priority labels:

- **P0 — essential now:** needed to defend this paper or conduct trustworthy evaluations.
- **P1 — core professional breadth:** develop for industry evaluation research and engineering.
- **P2 — advanced or specialized:** pursue as the research question requires.

For each topic, aim to do four things: explain it in plain language, state its mathematical or operational definition, construct a counterexample to a naive interpretation, and demonstrate it with a small reproducible experiment.

Start with Part II if preparing for a meeting about this paper. Use Part I to build the broader expertise. The reading list and learning exercises follow both parts.

## Part I — General and specialized AI evaluation expertise

### 1. Mathematical, statistical, and ML prerequisites — P0/P1

You should be comfortable with conditional probability, Bayes' rule, expectation, variance, covariance, independence versus zero correlation, likelihood, and sampling distributions. Understand why conditioning on a selected subset can change a result and why repeated observations need not provide independent information.

In statistics, learn estimation, hypothesis testing, confidence intervals, regression, generalized linear models, hierarchical models, missing-data mechanisms, and simulation. Linear algebra and optimization help you understand embeddings, calibration methods, training, and model comparisons.

In ML, distinguish training, validation, and test data; underfitting and overfitting; empirical and population risk; supervised, self-supervised, and reinforcement learning; pretraining, fine-tuning, and preference optimization. Understand how tokenization, attention, decoding, context windows, and multimodal encoders affect what the evaluated system can receive and produce.

**Mastery check:** explain why a million responses from ten users do not generally give the same uncertainty as a million responses from a million users.

### 2. Measurement theory and construct validity — P0

A **construct** is the property you want to study, such as visual grounding, factual reliability, or safe tool use. An **operationalization** is the concrete task and scoring rule used to measure it. A **metric** is a numerical summary; a **benchmark** combines tasks, inputs, targets, scoring, and an execution protocol.

Learn content validity, convergent and discriminant evidence, criterion-related validity, reliability, and measurement invariance. Repeatedly obtaining the same score establishes consistency, not necessarily that the intended property was measured. A benchmark can omit essential aspects of a capability or reward irrelevant cues.

Write the measurement chain explicitly: intended decision → construct → target population → sampled tasks → observed behavior → scoring → estimate → interpretation. Identify assumptions at each link. [Jacobs and Wallach, *Measurement and Fairness*](https://arxiv.org/abs/1912.05511) is a useful foundation.

**Mastery check:** provide three reasons that improved multiple-choice accuracy might not mean improved visual grounding.

### 3. Evaluation objectives and system boundaries — P0/P1

Distinguish **capability evaluation** (what the system can do under specified elicitation), **reliability evaluation** (how consistently it does so), **safety evaluation** (whether specified harmful behaviors occur), and **utility evaluation** (whether it helps the intended user).

Also distinguish model weights from the deployed system. A system includes prompts, retrieval, tools, memory, permissions, parsers, retry rules, and human intervention. A result for one configuration does not automatically describe the base model or another deployment.

Separate exploratory diagnosis, model selection, release gating, and scientific explanation. These uses require different evidence. Decide whether a study estimates ordinary use, best achievable performance under a budget, or worst-case behavior under a threat model.

Holistic evaluation considers multiple desiderata rather than assuming one accuracy metric captures everything. [Liang et al., *Holistic Evaluation of Language Models*](https://arxiv.org/abs/2211.09110).

**Mastery check:** write a one-paragraph evaluation contract naming the system version, population, task, resources, metric, uncertainty, and decision.

### 4. Dataset construction, sampling, and generalization — P0

Understand the **sampling frame**, target population, inclusion/exclusion criteria, stratification, prevalence, selection bias, and sampling weights. A deliberately balanced challenge set answers a different question from a representative deployment sample.

Know the unit of sampling and analysis: patient, user, conversation, repository, image, or generated response. Split by the entity that must generalize. Images from the same patient or tasks from the same repository can leak information across a random item-level split.

Learn temporal and geographic validation, source deduplication, near-duplicate detection, label leakage, preprocessing leakage, and nested validation for tuning. Keep a protected test set; repeated prompt selection against the same test set is still adaptation to that set.

Recognize the difference between a dataset's convenience, diversity, representativeness, and difficulty. Document provenance and intended uses. [Gebru et al., *Datasheets for Datasets*](https://arxiv.org/abs/1803.09010).

**Mastery check:** explain which population your sample represents and what additional assumptions would be required to report a deployment failure rate.

### 5. Targets, annotation, and human evaluation — P0/P1

Distinguish **ground truth**, reference labels, expert judgment, observed outcomes, and synthetic rule outputs. They are not interchangeable. Separate ambiguity from annotation error and from a genuine difference in what raters were asked to assess.

Know rubric design, annotator training, blinding, randomization of presentation order, adjudication, disagreement preservation, and expert versus crowd evaluation. Pairwise preference, categorical labels, ordinal ratings, and continuous scores require different analyses.

Learn raw agreement, Cohen's kappa, Krippendorff's alpha, and intraclass correlation, including their scale assumptions and sensitivity to prevalence or rater design. Agreement does not establish correctness. Report rater recruitment, relevant expertise, instructions, compensation where appropriate, and uncertainty.

Decompose answer quality into dimensions such as correctness, relevance, completeness, and style instead of asking for an undefined “quality” score. [Howcroft et al., *Twenty Years of Confusion in Human Evaluation*](https://aclanthology.org/2020.inlg-1.23/).

**Mastery check:** design an annotation protocol in which disagreement can reveal a flawed question rather than automatically being treated as annotator failure.

### 6. Metrics and aggregation — P0/P1

Know what each metric rewards and which errors it hides:

| Task | Concepts to understand | Common mistake |
|---|---|---|
| Classification | Confusion matrices; precision, recall, specificity; macro/micro averages; balanced accuracy; F1; thresholds | Reporting high accuracy on an imbalanced dataset without class-specific performance |
| Ranking/retrieval | Recall@k, precision@k, mean reciprocal rank, nDCG; incomplete relevance judgments | Scoring answer quality and attributing every failure to the retriever |
| Regression | MAE, MSE/RMSE, robust losses, residuals, heteroscedasticity | Ignoring that squaring errors emphasizes large failures |
| Probability prediction | Log loss, Brier score, calibration, discrimination | Treating AUROC as a calibration metric |
| Text generation | Exact match, token overlap, semantic similarity, factual support, human preference | Assuming similarity to one reference establishes truth |
| Segmentation/detection | Dice/IoU, sensitivity by object size, boundary error, detection AP | Assuming good segmentation overlap guarantees clinically correct measurements |
| Agents/code | End-state success, constraint violations, execution correctness, regressions, retries | Treating passing an incomplete test suite as complete correctness |
| Speech/audio/video | Word error rate, speaker/task slices, temporal localization, audiovisual alignment | Pooling away systematic failures in specific conditions |

Understand prevalence dependence, AUROC versus precision-recall curves, threshold selection, subgroup weighting, Simpson's paradox, and score normalization. An average across benchmarks encodes a weighting choice; it is not a neutral definition of intelligence.

**Mastery check:** construct two models whose ordering reverses under micro versus macro averaging, and explain which metric fits the intended decision.

### 7. Probabilistic forecasting, calibration, and abstention — P0/P1

For binary outcomes, the Brier score is `mean((p_i - y_i)^2)`. Log loss is `-mean(y_i log p_i + (1-y_i) log(1-p_i))`. These evaluate probability forecasts, not just thresholded decisions. Proper scoring rules incentivize truthful probabilities in expectation; sharp forecasts are useful only when adequately calibrated. [Gneiting and Raftery, *Strictly Proper Scoring Rules, Prediction, and Estimation*](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).

Understand reliability diagrams, calibration-in-the-large, calibration slope, and limitations of bin-dependent expected calibration error. A model that always predicts the base rate can be calibrated yet have no discrimination. Fit recalibration on separate data, not on the test set. [Guo et al., *On Calibration of Modern Neural Networks*](https://proceedings.mlr.press/v70/guo17a.html).

Study selective prediction: **coverage** is the fraction answered; **selective risk** is error among answered items. A refusal-heavy model can appear safe while being unusable. Evaluate risk-coverage and utility-cost trade-offs.

Conformal prediction constructs prediction sets under assumptions such as exchangeability. Marginal coverage is not automatic coverage for every subgroup, patient, or shifted population. [Angelopoulos and Bates, *A Gentle Introduction to Conformal Prediction*](https://arxiv.org/abs/2107.07511).

**Mastery check:** distinguish uncertainty in a patient's predicted outcome from uncertainty in the estimated average performance of a model.

### 8. Experimental design and causal reasoning — P0

Learn paired designs, randomization, blocking, factorial experiments, positive and negative controls, ablations, and interaction effects. Change one factor when estimating its isolated effect; use a factorial design when interactions are the question.

Distinguish an intervention on an input from identification of the model's internal mechanism. Removing an image changes more than access to its semantic content: it can change prompt length, image count, formatting, or answer defaults.

Understand potential outcomes, consistency, confounding, selection/collider bias, positivity, interference, mediation, and controlled direct versus total effects. State which are relevant to your actual design rather than adding causal terminology decoratively. [Hernán and Robins, *Causal Inference: What If*](https://miguelhernan.org/whatifbook).

Behavioral tests can check invariance, directional expectations, and minimal functionality. An irrelevant change should preserve the answer; a relevant change may require a specific new answer. [Ribeiro et al., *CheckList*](https://aclanthology.org/2020.acl-main.442/).

**Mastery check:** explain why simultaneously changing quantization and serving software cannot isolate a quantization effect.

### 9. Statistical inference, uncertainty, and effect size — P0

Understand the estimand, estimator, standard error, confidence interval, null hypothesis, test statistic, significance level, and practical effect size. A p-value is a tail probability under a specified null and assumptions; it is not the probability that the null is true.

For paired binary outcomes, learn McNemar's test and the role of discordant pairs. For proportions, learn Wilson or exact intervals rather than automatically using a symmetric normal approximation. For resampling, know the difference between ordinary, paired, stratified, cluster, and hierarchical bootstrap designs.

Learn randomization/permutation tests and exchangeability. A procedure becomes valid through its design or distributional assumptions, not because it shuffles something. Confidence intervals and p-values can disagree when based on different methods. [Dror et al., *The Hitchhiker's Guide to Testing Statistical Significance in NLP*](https://aclanthology.org/P18-1128/).

Bayesian alternatives require explicit priors, likelihoods, posterior predictive checks, and sensitivity analysis. A credible interval has a different interpretation from a frequentist confidence interval; neither repairs biased targets or invalid sampling.

**Mastery check:** identify every independent source of variation in an experiment before choosing a resampling method.

### 10. Power, equivalence, and negative results — P0

**Power** is the probability of rejecting a specified null under a specified alternative. It depends on sample size, effect structure, variance/dependence, the test, and multiplicity correction. Plan for an effect worth detecting; simulate when formulas do not match the design. Post hoc power obtained by plugging in the observed effect adds little to the observed test result. [Card et al., *With Little Power Comes Great Responsibility*](https://aclanthology.org/2020.emnlp-main.745/).

Distinguish superiority, equivalence, and noninferiority. Equivalence requires a justified margin and evidence that the effect lies within it. A conventional two-one-sided-tests procedure at alpha = .05 corresponds to an appropriate 90% confidence interval inside the equivalence bounds; a 95% containment rule is more conservative, not identical. [Lakens, *Equivalence Tests: A Practical Primer*](https://pubmed.ncbi.nlm.nih.gov/28736600/?dopt=Abstract).

For independent trials with zero failures, an approximate one-sided 95% upper bound is `3/n`; zero observed failures is not proof of zero risk. Dependence and selective sampling weaken that interpretation.

**Mastery check:** explain the difference between “no effect detected,” “effects larger than a specified threshold excluded,” and “effect proven to be exactly zero.”

### 11. Multiplicity, adaptation, and continuous testing — P0/P1

Learn family-wise error control, Holm correction, false discovery rate, and the importance of defining the hypothesis family. A separate exploratory family is not made confirmatory by adding a correction after seeing results.

Understand researcher degrees of freedom: selecting prompts, subsets, metrics, seeds, stopping times, or model versions after seeing scores. Benchmark overfitting can happen at the level of an entire research community. [Dwork et al., *Preserving Statistical Validity in Adaptive Data Analysis*](https://arxiv.org/abs/1411.2664).

For live evaluation, learn sequential testing, alpha spending, confidence sequences, and sequential probability ratio tests. A fixed-sample p-value is not automatically valid if repeatedly inspected until favorable.

Keep a distinction between prespecification, externally timestamped preregistration, exploratory analysis, and confirmation on fresh evidence. Exploration is useful; undisclosed exploration is the problem.

**Mastery check:** define a release decision rule that does not change opportunistically after seeing results.

### 12. Psychometrics, item quality, and ranking stability — P1/P2

Learn item difficulty, discrimination, guessing, dimensionality, ceiling/floor effects, and local dependence. A benchmark may not measure a single latent ability even if it produces one score.

Item response theory (IRT) models performance using item properties and latent ability. A simple Rasch model uses `P(correct) = sigmoid(ability - difficulty)`; more elaborate models introduce discrimination and guessing. The assumptions need checking, especially across very different model families.

Study differential item functioning: an item may behave differently across groups or model families even at a comparable modeled ability. Study uncertainty in rankings, pairwise win rates, Bradley–Terry models, and the effects of opponent mix, ties, and nontransitive preferences.

Efficient benchmark subsets can reduce cost, but their score estimates need validation on genuinely held-out model families. See the authors' [tinyBenchmarks project](https://github.com/felipemaiapolo/tinyBenchmarks).

**Mastery check:** explain why two models with the same average score can have substantially different capability profiles.

### 13. LLM-specific evaluation and contamination — P1

Understand prompt templates, chat formatting, few-shot example selection, option-order effects, token likelihood versus generated answers, length normalization, truncation, decoding settings, and context placement. “Temperature zero” does not establish reproducibility across hardware, serving implementations, or changing API versions.

Distinguish knowledge, reasoning, instruction following, factual accuracy, evidence faithfulness, and appropriate uncertainty. Fluent explanations are not reliable evidence of the process that produced the answer. [Turpin et al., *Language Models Don't Always Say What They Think*](https://arxiv.org/abs/2305.04388).

Learn contamination through pretraining, fine-tuning, benchmark-specific tuning, and near-duplicate examples. High performance alone does not prove contamination, and failure to detect contamination does not prove its absence. Statistical detection methods have explicit assumptions. [Oren et al., *Proving Test Set Contamination in Black Box Language Models*](https://arxiv.org/abs/2310.17623).

For reasoning and code, distinguish pass@1, success in at least one of k attempts, and success on all k attempts. Compute budgets and selection/oracle access must accompany these metrics.

**Mastery check:** specify enough of the prompt and decoding protocol for someone else to reproduce a comparison.

### 14. LLM judges, graders, and evaluation of evaluators — P1

Know reference-based versus reference-free judging, pairwise preferences versus absolute rubric scores, deterministic validators versus learned graders, and process versus outcome grading.

Audit position, verbosity, style, self-preference, and authority biases. Check whether the judge rewards correct content or persuasive presentation. Counterbalance response order, blind identities, and include ties or abstention when appropriate. Compare with relevant human judgments and report uncertainty and slice-specific errors. [Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*](https://arxiv.org/abs/2306.05685).

Separate repeatability, agreement with another judge, and validity against the intended criterion. An ensemble of judges can share errors. Calibrate the evaluator on both obvious controls and difficult borderline cases. Freeze the judge model, prompt, rubric, and parser for a comparison.

Treat evaluated content as untrusted data: it can contain instructions attempting to influence the grader. If the grader is also used as a training reward, measure how easily it can be exploited and preserve independent evaluation.

**Mastery check:** create a correct-but-terse answer and an incorrect-but-polished answer, then test whether the judge follows the intended rubric.

### 15. Retrieval, grounding, and multimodal evaluation — P0/P1

For retrieval-augmented generation, separate retrieval relevance/coverage, answer correctness, attribution, and faithfulness to supplied evidence. An answer can agree with the retrieved text while the text is false, or be correct without support from that text. Evaluate document freshness, retrieval omissions, citation entailment, and citation completeness. [Es et al., *Ragas*](https://arxiv.org/abs/2309.15217) is one example of decomposing RAG evaluation, not a substitute for validating its component metrics.

For vision-language systems, separate perception, localization, OCR, cross-modal alignment, reasoning, and final answer generation. Study text-only shortcuts, image-presence effects, contradictory modalities, multiple-image order, resolution sensitivity, and relevant versus irrelevant perturbations.

Grounding is stronger than answer sensitivity: when visual evidence changes, the answer should change in the way the evidence warrants. Correctness on complementary images already appears in [Goyal et al., *Making the V in VQA Matter*](https://arxiv.org/html/1612.00837v3). Do not frame all prior swapping work as measuring arbitrary answer changes.

For video/audio, account for temporal alignment, event ordering, and cross-modal leakage. A model that identifies a scene may still fail to identify when an event occurred.

**Mastery check:** design separate tests for image ingestion, perception, and correct evidence tracking.

### 16. Agent and reinforcement-learning evaluation — P1/P2

An agent evaluation includes an environment, initial state, user goal, observations, tools, permissions, action budget, termination rule, and success verifier. Understand partial observability, state transitions, recovery, memory, and long-horizon error accumulation.

Measure both task completion and constraint compliance. Inspect final state and execution traces: reaching the right final state does not erase an earlier disclosure or unauthorized action. Separate model failures, scaffold failures, environment failures, and verifier failures.

Learn repeated-trial reliability, simulated-user validity, tool API realism, hidden tests, environment reset, and contamination from prior episodes. [τ-bench](https://arxiv.org/abs/2406.12045) illustrates interactive policy-constrained tasks; [SWE-bench](https://arxiv.org/abs/2310.06770) illustrates executable repository-level tasks. Their original papers are useful designs, not claims about the latest versions.

For RL, separate training-seed variation, episode variation, and variation across environments. Understand return, success, sample efficiency, evaluation policy, and uncertainty across tasks. [Agarwal et al., *Deep Reinforcement Learning at the Edge of the Statistical Precipice*](https://proceedings.neurips.cc/paper_files/paper/2021/file/f514cec81cb148559cf475e7426eed5e-Paper.pdf).

For offline policy evaluation, learn importance weighting, support/overlap, doubly robust estimation, and the limits of logged behavior. An offline estimate does not automatically identify how a substantially different policy would perform.

**Mastery check:** explain the difference between one successful agent run and dependable task completion under a fixed budget.

### 17. Security, privacy, and adversarial evaluation — P1; a potential specialization

Start with a threat model: assets, attacker objective, attacker knowledge, controllable inputs, access, budget, and success conditions. Distinguish prompt injection through untrusted content from direct harmful-user requests and from ordinary instruction-following failures.

Evaluate attack success, benign utility, utility under attack, false alarms, and unauthorized side effects. Define denominators: conditional attack success on tasks the agent can normally perform differs from an unconditional rate across all tasks. Test adaptive attacks against the actual defense, rather than only replaying attacks designed for an undefended system. [Debenedetti et al., *AgentDojo*](https://arxiv.org/abs/2406.13352).

Learn adversarial robustness, attack transfer, black-/white-box access, and the lesson that a weak attack can make a weak defense look strong. [Athalye et al., *Obfuscated Gradients Give a False Sense of Security*](https://proceedings.mlr.press/v80/athalye18a.html).

Privacy evaluation includes unauthorized data access/disclosure, training-data extraction, membership inference, and data retention. Formal differential privacy and empirical attack resistance answer different questions; neither should be substituted for the other. [Carlini et al., *Extracting Training Data from Large Language Models*](https://arxiv.org/abs/2012.07805).

Also understand capability elicitation, refusal versus incapability, evaluator awareness, potential sandbagging, and capability uplift over a baseline. These require carefully scoped evidence, not inference from a single surprising transcript.

**Mastery check:** define an agent security failure observable from a trace even when its final answer looks harmless.

### 18. Robustness, distribution shift, fairness, and human impact — P1

Distinguish covariate shift, label/prevalence shift, concept shift, natural corruptions, adversarial perturbations, and changes in user behavior. Separate average-case robustness from worst-group and worst-case results. Realistic external validation matters because laboratory perturbations need not represent deployment changes. [Koh et al., *WILDS*](https://proceedings.mlr.press/v139/koh21a.html).

Fairness requires identifying affected groups, relevant harms, decisions, and context. Learn demographic parity, equalized odds, equal opportunity, calibration by group, and intersectional analysis. These criteria can conflict; choosing one is a substantive decision. Small subgroup samples require honest uncertainty, and a pooled mean can hide important failures. [Selbst et al., *Fairness and Abstraction in Sociotechnical Systems*](https://andrewselbst.com/wp-content/uploads/2019/10/selbst-et-al-fairness-and-abstraction-in-sociotechnical-systems.pdf).

For human-AI systems, measure task outcomes with and without assistance, appropriate reliance, automation bias, expertise differences, and workflow effects. Model-only performance need not predict whether a person-plus-model system improves.

**Mastery check:** explain why a benchmark balanced across demographic groups does not by itself establish fairness in deployment.

### 19. Production evaluation and decision-making — P1

Understand offline evaluation, shadow deployment, online randomized experiments, canary releases, monitoring, and rollback. Offline scores are proxies for real outcomes; online changes can be confounded by traffic, seasonality, and user adaptation.

Define primary outcomes, guardrails, minimum meaningful improvements, acceptable regressions, and the cost of errors. Measure latency distributions, time to first token when relevant, throughput, timeout rates, inference cost, and human-review burden. Optimize a quality-cost-risk trade-off rather than a single score.

Account for delayed labels, selective feedback, exposure bias, drift, and repeated monitoring. Investigate whether an apparent regression is due to model behavior, task mix, a grader update, or a serving change.

Use uncertainty in decisions: “ship,” “hold,” “collect more evidence,” and “investigate this slice” can all be legitimate outcomes. A decision threshold should reflect consequences rather than defaulting mechanically to p < .05.

**Mastery check:** write a release recommendation that distinguishes measured evidence, unresolved risks, and the next observation that would change the decision.

### 20. Evaluation engineering and reproducibility — P0/P1

Build immutable dataset versions, stable item IDs, prompt and rubric versions, model identifiers, dependency locks, configuration snapshots, and response provenance. Preserve raw outputs separately from parsed answers and derived scores.

Understand distributed execution, batching, rate limits, caching, retries, idempotency, checkpointing, and resumable runs. An accidental cache hit or retry policy can change an evaluation. Record failures instead of silently dropping them.

Test parsers and scorers with known-answer cases, malformed output, reordered options, empty responses, and adversarial content. Use invariants: counts reconcile, eligible items have valid targets, and shuffled answer letters map back to the same semantic labels.

Separate data collection, scoring, and statistical analysis. Regenerate tables from recorded outputs without recalling models. Pin what can be pinned and disclose API drift. Document intended use and limitations, following principles in [Mitchell et al., *Model Cards for Model Reporting*](https://arxiv.org/abs/1810.03993).

**Mastery check:** another researcher can reproduce every paper cell, including exclusions and denominators, from one documented command and the released artifact.

### 21. Evaluation-guided improvement and research judgment — P1/P2

An evaluation becomes especially useful when it identifies a failure, motivates an intervention, and detects improvement on protected evidence. Learn error taxonomies, targeted data collection, active learning, reward-model evaluation, and separation of development graders from final assessors.

Recognize Goodhart effects and reward hacking: optimizing a proxy can exploit its weaknesses. Measure whether gains transfer to fresh tasks, independent graders, and meaningful outcomes. A system may optimize formatting or evaluator preferences while underlying ability remains unchanged.

Scientific judgment includes choosing tractable questions, distinguishing descriptive from causal claims, representing prior work accurately, reporting negative results, and communicating limitations without erasing real findings.

**Mastery check:** propose an intervention based on a failure analysis and a held-out test that could falsify your explanation.

### 22. What an excellent evaluator should be able to produce — P0/P1

Your portfolio should eventually demonstrate: an evaluation specification; an auditable dataset; a justified experimental design; a tested harness and scorer; uncertainty-aware analysis; a failure investigation; a reproducible artifact; and a clear recommendation.

For research-scientist roles, emphasize new measurement questions and valid methods. For research-engineer roles, add strong implementation, scaling, and debugging. For applied evaluation roles, emphasize realistic workflows, human evaluation, and decisions. These are overlapping skill profiles, not mutually exclusive career categories.

## Part II — Concepts you need for this project specifically

This part concerns the current **image-dependence brain-MRI study**, not hypothetical future agent projects. It is grounded in [the manuscript](latex/acl_latex.tex), [the current review](review.md), [the proposed fixes](solution.md), and the local analysis code. Reported numbers are used for explanation; this document does not rerun the experiments or certify unresolved results.

### 23. The actual research question: benefit, sensitivity, and tracking — P0

The project asks whether model answers follow the visual evidence supplied in a brain-MRI task. Three observable properties must be separated:

| Property | Operational question | What a positive result establishes |
|---|---|---|
| Image benefit | Is accuracy higher with the patient's image than without it? | An accuracy benefit under these input conditions |
| Image sensitivity | Does changing or removing the image change the answer? | The answer depends on the intervention in some way |
| Correct evidence tracking | Does the answer agree with the specific evidence in the replacement image? | Evidence of appropriate behavior, subject to target validity and a justified comparison |

A model can change its answer incorrectly. It can also improve accuracy by switching to a common class whenever any image appears. Neither behavior requires distinguishing the contents of different images.

The defensible central argument is therefore: **an image-ablation gain alone does not establish correct visual tracking.** The stronger statement that a particular model never uses visual information requires evidence this study does not currently supply. Even successful behavioral tracking would not uniquely identify the model's internal reasoning mechanism.

**Mastery check:** invent a predictor that gains accuracy when images appear but gives the same answer for every image. Explain which of the three properties it demonstrates.

### 24. Understand each phase and where its answer comes from — P0

The five phases have different targets and cannot all be interpreted as clinical correctness:

| Phase | Task in this implementation | Origin of the target | Main interpretive limit |
|---|---|---|---|
| AIA | Identify T1, contrast-enhanced T1, T2, or FLAIR | Identity of the sequence rendered | Sequence identification is only one visual capability |
| LIL | Locate the tumor region by hemisphere and anterior/posterior half | Automated segmentation geometry on the selected slice | The segmentation and rendered orientation must support the target |
| DSCR | Select an enhancement-based response category from longitudinal slices | A simplified rule applied to segmentation-derived measurements | Agreement with this target is not validation of a complete clinical assessment |
| PJRF | Forecast death within 52 weeks of the scan | Recorded survival information | Time origin and censoring are unresolved |
| TCM | Select a management action from supplied facts | The study's management rule | Rule agreement is not observed treatment or validated clinical advice |

For DSCR, understand **baseline**, **follow-up**, and **nadir**. The baseline is the reference scan; follow-up is the scan being assessed; the nadir is the smallest earlier measurement used by the project's progression rule. Two or three images appear depending on whether nadir and baseline coincide. The bidimensional product multiplies a lesion's longest diameter by its longest perpendicular diameter. It is a measurement used by the implemented rule, not lesion volume.

For LIL, distinguish patient left/right from screen left/right. The manuscript specifies radiological orientation checked against the image affine. A correct geometric label can still be scored against an incorrectly rendered view if that transformation is wrong.

Same-patient phase continuity makes a linked evaluation possible. It does not establish that the model's actual inference proceeds through the pictured chain. Each intervention and condition still needs its own interpretation.

**Mastery check:** for each phase, name the visible inputs, hidden information used to construct its target, and the claim a correct answer supports.

### 25. Target validity, answerability, and the motivating audit — P0

The audit compares an automated measurement rule with expert ratings. A disagreement does not tell you which component failed. Possible explanations include a segmentation error, an unsuitable slice, a different target lesion, a different reference scan, omitted information, or a difference between the simplified rule and the expert's assessment.

Three questions are distinct: **Was the key constructed correctly? Is the displayed input sufficient to recover it? Does that key represent the intended clinical construct?** Agreement with a programmatically generated key answers none of these automatically.

The audit also has an abstention category. Agreement among cases for which the rule returns a category differs from success across all attempted cases. Report coverage alongside conditional agreement; otherwise, excluding difficult cases can make the rule look stronger than it is.

The current study therefore treats LIL/DSCR keys as segmentation-derived targets whose validity on the displayed slices remains unverified. A strong reference model provides evidence that some tasks are feasible, but its failures cannot establish that an item is unanswerable. Review by qualified readers of the exact displayed inputs would address a different evidentiary gap.

**Mastery check:** explain why “the automated rule disagrees with the expert” does not imply “the expert's answer cannot be inferred from the image.”

### 26. Define the paired estimands before interpreting a table — P0

Let `y_i` be recipient item i's semantic target, `d_i` its assigned donor's semantic target, and `O_i`, `T_i`, and `S_i` the model's answers with its own image, text only, and the swapped image. Here `1(condition)` equals one when the condition holds and zero otherwise.

The image benefit is:

`Δ_image = mean[1(O_i = y_i) − 1(T_i = y_i)]`.

The reported donor gain is:

`G_donor = mean[1(S_i = d_i) − 1(T_i = d_i)]`.

Swap sensitivity is:

`C_swap = mean[1(S_i ≠ O_i)]`.

Multiply these by 100 to express percentage points or percentages as appropriate. The first two are paired differences: each item's two outcomes belong together. The second scores **both conditions against the donor key**, including the text-only answer produced without seeing the donor. Its baseline estimates how often that answer already matches the donor target.

All three comparisons require a specified eligible set. Own-image DSCR accuracy uses 46 items, while donor comparisons use 42. Accordingly, the Scout own-image value is 54.3% in the full E1 table and 54.8% in the paired E2 table. These describe different denominators rather than a rounding inconsistency.

Option letters are local encodings. If category X is option A for one recipient and option C for another, comparing letters across recipients does not compare categories. Resolve answers through each recipient's actual displayed option map before donor-label analysis.

**Mastery check:** manually calculate all three quantities for four invented items, including an incorrect answer change and a text-only answer that already equals the donor key.

### 27. Read the central Scout result without overclaiming — P0

The current generated E1 table reports Scout DSCR accuracy of 54.3% with images and 8.7% with text only: approximately **+45.7 percentage points**, computed from the underlying counts. This is a substantial observed benefit. It is not invalidated by an unsuccessful tracking analysis.

However, progressive disease accounts for 27 of the 46 DSCR targets, so always predicting that class achieves 58.7%. The own-image accuracy is below that baseline. This shows why absolute performance and class balance matter alongside the ablation gain; it does not show that no individual image was read correctly.

For the 42 donor-paired items, Scout agrees with donor targets in 50.0% of swapped-image responses and 21.4% of text-only responses, a **+28.6-point donor gain**. The current review questions whether the separate permutation analysis justifies donor-specific interpretation. Positive gain and unresolved specificity can coexist.

Do not describe the benefit as arising “only” from poor text-only performance. The difference is measured, but its exclusive mechanism is not identified. Nor should a nonsignificant permutation result be translated into proof that Scout behaves like the generic synthetic predictor.

**Mastery check:** explain these results in three sentences: what improved, what remains unestablished, and what analysis needs repair.

### 28. Why subtracting a no-image prior does not isolate tracking — P0

Consider an illustrative four-class donor set in which 60% of donor keys are class A and 10% are class B. A model always answers B without an image and always answers A with any image. Its donor gain is `60% − 10% = 50` percentage points, although it never distinguishes one donor from another.

Subtracting the text-only baseline removes that baseline's agreement with donor keys. It does **not** remove every response triggered by image presence, image count, prompt format, or class preference. The generic-shift control in the project's synthetic experiment demonstrates this problem.

A specificity analysis must ask whether the observed answers match their particular donors more than an appropriate null mechanism predicts. That requires an explicit null and defensible exchangeability assumptions; it is not a property obtained by subtraction alone.

**Mastery check:** explain why a paired test of zero donor gain and a test of donor-specific association address different null hypotheses.

### 29. Donor assignment is a constrained design — P0

The manuscript's donor design requires a different target from the recipient, the same image count, and no more than two recipients per donor. These constraints help make the intervention interpretable. In particular, preserving image count avoids changing both image content and the number of displayed images.

The current `random_assignment` function in [the validation script](../tools/lumiere_v4_donor_validation.py) instead tries a one-to-one donor permutation. Its failure on the reported DSCR counts can be understood without running inference: among 46 items, 27 have progressive-disease targets; removing four leaves at least 23 such recipients among 42. A one-to-one assignment would need at least 23 distinct non-progressive donors, but there are at most 19 in that set. The requested assignment is impossible.

After unsuccessful attempts, the function silently returns the original assignment. Repeating it does not establish stability across new assignments. The function also omits the image-count constraint. These are concrete implementation problems, separate from whether the original fixed-assignment result is informative.

A repaired validation must preserve the intended donor pool and constraints, record assignment identities and actual variation, and report infeasibility explicitly. Merely satisfying constraints does not establish that a sampler follows the probability distribution needed for a statistical test.

**Mastery check:** explain the 23-versus-19 argument and why allowing two uses per donor changes feasibility without guaranteeing it in every image-count stratum.

### 30. Permutation tests, exchangeability, and donor dependence — P0

A permutation test compares the observed statistic with statistics obtained under a specified null rearrangement. **Exchangeability** means the allowed rearrangements preserve the relevant joint distribution under that null. It needs justification from the design or assumptions.

Two possible interpretations must be separated:

- A **conditional label-association test** holds answers fixed and rearranges labels under stated exchangeability assumptions.
- A **design-based randomization test** uses the actual assignment mechanism and a null under which the required potential outcomes can be evaluated, such as a suitably specified sharp null.

The current [supplementary analysis](../tools/lumiere_v4_supplement.py) permutes donor-key entries and attempts to repair entries that equal the recipient's own key. It does not reproduce all original assignment constraints or preserve reused-donor blocks. Consequently, calling it an assignment test does not establish that interpretation. A repaired sampler also needs evidence that it targets the intended distribution rather than a biased subset of allowable arrangements.

The implementation records accepted permutations. Its Monte Carlo tail estimate uses `(1 + b) / (1 + B)`, with b accepted draws at least as extreme as the observation and B accepted draws in total. Report B, not merely the number attempted. This correction does not repair a misspecified null.

Donor reuse creates another issue: recipients sharing an image may share errors. Resampling those recipients together addresses that particular dependence for uncertainty under a fixed assignment. It does not validate the permutation null, cover every dependence created by overlapping recipient/donor roles, or establish robustness to new assignments. Dropping one donor at a time measures sensitivity to influential donor groups, not power.

**Mastery check:** state what is fixed, what is randomized, what null licenses the randomization, and what the resulting p-value would permit you to conclude.

### 31. Synthetic validation: calibration, power, and stability — P0

Synthetic predictors are useful because their behavior is known by construction. The project's constant, random, image-shift, and tracker predictors probe different weaknesses in the measurement procedure.

**Calibration** asks how often a test falsely detects tracking when its null holds. **Power** asks how often it detects a specified tracking alternative. **Assignment stability** asks how results vary across valid donor assignments. Varying prediction seeds on one assignment answers a different question from varying assignments.

In the current tracker, probability rho selects the correct target directly; otherwise the predictor guesses uniformly. With four choices, expected accuracy is `rho + (1 − rho)/4`. Thus `rho = 0.4` means 55% expected correctness, not 40%. Rho is the probability of taking the tracking branch.

The review reports detection in 46 of 50 DSCR simulations for that predictor. This estimates power against that particular synthetic mechanism on the evaluated design. It leaves simulation uncertainty and says little about alternatives with weaker tracking, class-specific tracking, or correlated donor errors. Matching two predictors' scalar gains does not match their joint answer distributions or detection probabilities.

Deterministic controls with 0% detection are useful sanity checks. They do not establish nominal false-positive calibration across realistic no-tracking mechanisms. Useful additional controls include image-count responses, option-position preferences, and correlated errors. Finally, simulated reassignment cannot establish how an actual model responds to newly assigned images; that requires new model responses.

**Mastery check:** propose one experiment each for calibration, power, and assignment stability, and identify the source of randomness in each.

### 32. Small samples, paired uncertainty, and nondetection — P0

For paired accuracy, only discordant items affect the difference: cases correct only with images and cases correct only without them. Equal numbers of gains and losses can yield zero net improvement despite many changed answers. McNemar's test uses these discordant counts rather than treating the arms as independent samples.

At small sample sizes, an empirical bootstrap can appear overly certain. If every observed paired correctness difference is zero, resampling those differences always returns zero. The resulting `[0, 0]` interval reflects the empirical sample's lack of variation; it does not prove the population effect is exactly zero. The manuscript also reports a sparse-data interval, whose different assumptions must be understood rather than selecting whichever result is favorable.

Keep the registered E1 multiplicity family distinct from exploratory E2 analyses. A raw p-value, a Holm-adjusted p-value, and an interval from another method need not support identical threshold decisions. Report what each calculation tests and avoid treating them as interchangeable.

“No tracking detected” remains compatible with effects the design cannot reliably detect. An exclusion claim needs a justified effect scale, a meaningful threshold, and an appropriate bound or equivalence procedure. The project's ±10-point margin concerns its defined accuracy-effect analysis; it cannot automatically become a bound on every possible form of visual tracking.

**Mastery check:** explain how zero estimated gain, frequent answer changes, and substantial uncertainty can all occur together.

### 33. Positive controls and diagnosing the inference pipeline — P0

AIA probes sequence identification. Poor AIA performance motivates investigation, but does not logically make lesion localization or category reading impossible. Preserve the original prespecified gate as part of the historical analysis while clearly distinguishing any revised, task-specific interpretation.

The input checks answer narrower questions. Added prompt tokens indicate that images affect input processing; known-answer color, number, and image-order probes demonstrate perception on those stimuli. Neither establishes preservation of the MRI information needed for a particular task. Parsing checks establish whether recorded answers were recovered correctly, not whether the images were understood.

Likewise, a bf16 run through vLLM compared with a 4-bit run through Ollama changes precision and serving stack together. It can challenge a broad explanation tied to the original configuration, but cannot isolate a quantization effect. Cross-model comparisons additionally confound model size, training, architecture, and other system choices.

**Mastery check:** trace a failure through image loading, preprocessing, model input, generation, answer parsing, and scoring; name a separate observable check for each stage.

### 34. TCM: interventions, explicit rules, and the denominator bug — P0

TCM asks whether answers respond appropriately when a supplied category or timing fact changes. In this project's base prompts the management rule is absent; the explicit-rule condition adds it. These conditions measure different mixtures of prior knowledge, assumed policy, and adherence to supplied instructions.

Ending at the new target does not establish that a flip caused an appropriate change: the baseline answer might already have been there. For the proposed informative-item analysis, define eligibility from the baseline alone:

`eligible_i = 1(baseline answer ≠ new target)`.

Then the movement rate is the number of eligible items ending at the new target divided by the number eligible, with missing-answer handling stated explicitly.

The current implementation subtracts only cases that both start and end at the new target. It therefore incorrectly includes cases that start at the new target and move away. For example, suppose ten items contain two that start and stay at the target and one that starts there and leaves. Baseline eligibility gives seven items; the current calculation gives eight. If four move correctly, the rates are 4/7 versus 4/8. These are illustrative counts, not recalculated study results.

Report moving away from the target separately. Regenerating the real transition counts is necessary before claiming whether the published values change.

**Mastery check:** classify start-at-target/stay, start-at-target/leave, move-to-target, remain-wrong, and change-to-another-wrong-answer cases before calculating a denominator.

### 35. PJRF: probability forecasts require valid outcomes — P0

PJRF uses probability-bin midpoints as forecasts and evaluates squared error against a binary outcome. A forecast of 0.5 yields a Brier contribution of 0.25 whether the outcome is zero or one. A concentration in that bin can therefore explain a score near 0.25 without demonstrating individualized prognostic skill.

The more fundamental issue is outcome construction. Death within 52 weeks of a scan requires compatible scan and survival time origins. A patient whose follow-up ends before that horizon cannot automatically be treated as known to survive it. The manuscript identifies unresolved time-origin and censoring information, so model scoring cannot repair that missing foundation.

The leave-one-out base rate avoids using an item's own outcome to form its baseline prediction. It still represents this selected cohort, not a deployment population. Similar scores against that baseline do not establish that the supplied facts carry no predictive information.

**Mastery check:** distinguish an inaccurate probability forecast from an incorrectly constructed outcome label.

### 36. What you should be able to defend in a research meeting — P0

A concise explanation of the project is:

> We evaluate image benefit, answer sensitivity, and donor-target agreement separately on linked brain-MRI tasks. A large image-versus-text accuracy gain does not by itself establish that answers track the particular image shown. Our current results illustrate that distinction, but the donor reassignment validation and permutation interpretation require repair before stronger claims. Target validity, small samples, and selected-cohort generalization remain separate limitations.

You should then be able to show the formulas, trace one item through all three image conditions, reconstruct its displayed option mapping, identify its eligible denominator, and explain which uncertainty calculation applies.

For repair, follow the dependency order in [the proposed fixes](solution.md): correct assignment and TCM implementation; justify the permutation null; validate the procedure on multiple mechanisms; regenerate affected results; and reconcile the manuscript's claims. A prose correction is not a statistical rerun, and a successful synthetic test is not new real-model evidence.

The reproducibility chain should connect the item and image versions, donor assignment, prompt and model configuration, raw response, parsed semantic answer, per-item score, aggregate estimate, uncertainty calculation, and final table. Every exclusion and replacement run needs a recorded reason.

**Mastery check:** select any table cell and explain how another researcher could reconstruct its numerator, denominator, and interval from saved artifacts.

## Reading and practice sequence

The following sequence connects Part I's foundations to Part II's immediate project needs. The readings are the linked works already introduced in Part I; the local files show how those ideas appear in this implementation.

| Order | Read and inspect | Produce as evidence of understanding |
|---|---|---|
| 1. Measurement | Part I §§2–3 and Jacobs/Wallach; Part II §§23–25; manuscript task definitions | A one-page claim-to-measurement map for all five phases |
| 2. Paired comparisons | Part I §§8–10 and Dror et al.; Part II §§26–28, 32; [statistics code](../tools/lumiere_v4_stats.py) | A hand-calculated example separating accuracy gain, answer changes, and donor agreement |
| 3. Assignment and inference | Part I §§8–9; Part II §§29–30; [supplement](../tools/lumiere_v4_supplement.py) | A precise null specification with eligible assignments and dependence assumptions |
| 4. Measurement validation | Part I §10 and Card et al.; Part II §31; [synthetic predictors](../tools/lumiere_v4_donor_validation.py) | A validation design separating false positives, power, and assignment variation |
| 5. Secondary outcomes | Part I §7 and Gneiting/Raftery; Part II §§34–35 | A corrected TCM transition example and a PJRF outcome-validity checklist |
| 6. Research defense | Part I §§20–22; Part II §§33, 36; [review](review.md) | A short explanation of supported claims, unresolved findings, and the evidence needed next |

For broader industry preparation, then work through Part I's judging, retrieval, agent, security, and production-evaluation topics. The transferable skill from this project is the ability to connect a claim to a valid measurement, detect when implementation changes the question, and communicate what the evidence actually supports.
