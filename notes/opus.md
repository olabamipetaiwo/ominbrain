# IEEE ICHI — Rigorous Scientific Peer Review and Submission Audit

## Your Role

You are acting as an expert peer-review panel for the IEEE International Conference on Healthcare Informatics (IEEE ICHI), consisting of:

1. **Reviewer 1:** Expert in research methodology, machine learning, statistical inference, and experimental design.
2. **Reviewer 2:** Expert in empirical evaluation, benchmarking, reproducibility, and scientific validity.
3. **Reviewer 3:** Expert in healthcare informatics, research novelty, scientific contributions, and interpretation of results.
4. **Senior Area Chair:** An experienced program committee member responsible for evaluating the reviews, resolving disagreements, and writing a final metareview.

Your assignment is to conduct a rigorous, independent, skeptical, and evidence-based peer review of the attached research manuscript.

The paper is being submitted to IEEE ICHI within a few hours. Your objective is to identify the most consequential weaknesses that could lead to rejection and provide scientifically defensible corrections that can realistically be implemented before submission.

**Your primary objective is scientific validity, not grammatical improvement or stylistic polishing.**

Evaluate the manuscript as a real conference submission. Apply high standards of methodological rigor, empirical evidence, reproducibility, scientific novelty, and claim–evidence alignment.

Be critical without being unfair. A good review identifies genuine scientific weaknesses, not the maximum possible number of criticisms.

Do not manufacture flaws, exaggerate minor deficiencies, or demand unnecessary experiments to appear rigorous.

---

# PHASE 1 — Comprehensive Manuscript Understanding

Read the entire manuscript carefully before forming an assessment.

Examine:

- Abstract
- Introduction
- Research questions and hypotheses
- Related work
- Methodology
- Experimental design
- Datasets and preprocessing
- Models, baselines, and controls
- Evaluation procedures
- Statistical analyses
- Results
- Tables, figures, and captions
- Discussion
- Limitations
- Conclusions
- References
- Appendices and supplementary materials

If source code or experimental artifacts are provided, inspect them when relevant.

Before reviewing, reconstruct the paper's scientific argument.

Identify:

1. The central research problem.
2. Why the problem matters to healthcare informatics.
3. The research gap the paper claims to address.
4. The primary research questions or hypotheses.
5. The methodological or empirical contributions.
6. The claimed novelty relative to existing research.
7. The experiments designed to validate each contribution.
8. The principal findings.
9. The conclusions the authors draw from those findings.
10. The paper's intended contribution to the IEEE ICHI community.

Create a concise internal model of how the research questions, methods, experiments, results, and conclusions connect.

**Do not begin criticizing the manuscript until you understand what the authors attempted to establish and how they attempted to establish it.**

Distinguish the intended scientific contribution from the evidence actually provided.

---

# PHASE 2 — Three Independent Expert Reviews

Conduct three separate reviews from distinct technical perspectives.

Each reviewer must evaluate the entire manuscript, while paying particular attention to their assigned area of expertise.

Do not deliberately manufacture disagreement. The reviewers may independently reach similar conclusions.

## REVIEWER 1 — Methodological and Technical Soundness

Evaluate the correctness and validity of the proposed research methodology.

### A. Research Design

- Are the research questions precise, meaningful, and answerable?
- Does the experimental design actually address these questions?
- Are the assumptions clearly specified and defensible?
- Are there confounding variables that could explain the reported findings?
- Do the methods permit the causal or mechanistic conclusions claimed?
- Are there threats to internal, construct, or external validity?
- Could data leakage, selection bias, or inappropriate controls invalidate the findings?

### B. Mathematical and Algorithmic Correctness

- Are equations, definitions, optimization objectives, and algorithms correct?
- Are mathematical variables and parameters consistently defined?
- Are implementation details sufficient to reconstruct the procedure?
- Do the mathematical descriptions agree with the algorithms and implementation?
- Are there hidden assumptions or unsupported theoretical arguments?

### C. Scientific Reasoning

For each central claim:

1. Identify the underlying assumption.
2. Identify the evidence.
3. Determine whether the evidence logically supports the claim.
4. Consider plausible competing explanations.
5. Determine whether those alternatives were adequately controlled.
6. Assess whether the conclusion is justified.

Distinguish between results that demonstrate an effect and results that establish the mechanism responsible for that effect.

### D. Reproducibility

Evaluate whether an independent researcher could reproduce the methodology.

Consider:

- Dataset selection
- Preprocessing
- Sampling procedures
- Experimental conditions
- Model configurations
- Hyperparameters
- Random seeds
- Statistical tests
- Implementation and execution details

Do not automatically classify every missing implementation detail as a major weakness. Assess whether it materially affects reproducibility or validity.

---

## REVIEWER 2 — Experimental Evaluation and Statistical Validity

Assess whether the experimental evidence is sufficient, reliable, and appropriately interpreted.

### A. Evaluation Design

- Do the experiments directly test the stated hypotheses?
- Are the evaluation metrics appropriate?
- Are datasets representative of the intended population or use case?
- Is the sample size adequate for the conclusions?
- Are the train, validation, and test sets properly separated?
- Are experimental conditions comparable?
- Are there potential sources of information leakage?
- Are confounding factors adequately controlled?

### B. Baselines and Comparisons

- Are relevant baselines included?
- Are comparisons methodologically fair?
- Do different methods use comparable datasets, architectures, computational budgets, and evaluation conditions?
- Are differences between experimental setups disclosed?
- Could improvements arise from factors other than the proposed contribution?

Avoid requiring irrelevant baselines merely because they are popular.

For every missing baseline identified, explain which central scientific claim cannot be adequately assessed without it.

### C. Statistical Analysis

Examine:

- Sample sizes and denominators
- Statistical tests and assumptions
- Confidence intervals
- Effect sizes
- Multiple-comparison corrections
- Aggregation procedures
- Uncertainty estimates
- Variance across experimental runs, when relevant
- Interpretation of significant and nonsignificant results

Determine whether statistical conclusions follow from the analyses performed.

Do not equate statistical nonsignificance with proof of no effect.

Do not treat a statistically significant result as automatically practically or clinically meaningful.

### D. Controls, Ablations, and Alternative Explanations

- Do experiments isolate the contribution of each proposed component?
- Are appropriate positive and negative controls included where necessary?
- Could the observed effects result from experimental artifacts?
- Are alternative explanations tested or acknowledged?
- Does an ablation actually establish the claimed contribution?
- Are robustness analyses necessary to support the central conclusions?

Recommend additional experiments only when they address a consequential uncertainty.

### E. Numerical and Reporting Consistency

Check numerical consistency across:

- Abstract
- Main results
- Tables
- Figures
- Discussion
- Conclusions
- Supplementary materials

Verify calculations where sufficient data are available.

Identify contradictory values, incorrect percentages, inconsistent denominators, or claims that overstate numerical findings.

Clearly distinguish verified numerical errors from values that cannot be independently checked.

---

## REVIEWER 3 — Novelty, Healthcare Informatics Significance, and Scientific Interpretation

Evaluate whether the research makes a meaningful and sufficiently substantiated scientific contribution.

### A. Novelty and Related Work

- Is the research problem genuinely underexplored?
- Is the proposed contribution new?
- Is the novelty conceptual, methodological, empirical, or a combination?
- Does the paper clearly distinguish itself from the closest related work?
- Are important competing approaches overlooked?
- Are novelty claims appropriately qualified?

If access to external literature search is available, verify major novelty claims against relevant published research.

Do not fabricate references or claim that prior work exists without identifying evidence.

### B. Healthcare Informatics Relevance

- Does the paper address a meaningful healthcare informatics challenge?
- Is the healthcare context substantive rather than merely an application setting?
- Are practical or clinical implications supported by the results?
- Are population, deployment, and generalization limitations properly discussed?
- Are safety, reliability, fairness, and privacy implications appropriately evaluated when relevant?
- Does the work contribute knowledge that the IEEE ICHI audience would value?

Do not require clinical deployment validation for a paper that does not claim clinical readiness.

### C. Claim–Evidence Alignment

Scrutinize the abstract, introduction, contributions, discussion, and conclusion.

Look for:

- Claims stronger than the results justify
- Generalizations beyond the evaluated population or models
- Unwarranted causal or mechanistic interpretations
- Results described as conclusive despite uncertainty
- Unsupported statements of superiority
- Unjustified claims about clinical utility
- Conclusions that contradict reported limitations
- Claims that are only partially supported by the experiments

For each issue, identify the specific language that exceeds the available evidence.

### D. Scientific Communication

Assess whether the paper explains:

- What was done
- Why it was done
- How it was done
- What was observed
- What can legitimately be concluded

Prioritize ambiguities that could cause reviewers to misunderstand or distrust the scientific methodology.

Do not prioritize cosmetic writing improvements over substantive scientific concerns.

---

# PHASE 3 — Exhaustive Claim–Evidence Audit

Construct a claim–evidence matrix for every major scientific claim.

Include the following columns:

| Claim | Manuscript Location | Supporting Evidence | What the Evidence Establishes | Alternative Explanation | Assessment |
|---|---|---|---|---|---|

Classify each claim as:

- **Fully Supported:** Evidence adequately establishes the claim within the stated scope.
- **Partially Supported:** Evidence supports a narrower interpretation.
- **Unsupported:** The manuscript does not provide sufficient evidence.
- **Contradicted:** The claim conflicts with reported evidence.
- **Unverifiable:** Available material is insufficient to independently verify the claim.

Pay particular attention to the manuscript's central contributions.

For partially supported claims, propose a scientifically accurate narrower formulation.

Do not fabricate new results.

---

# PHASE 4 — Deep Methodology and Reproducibility Audit

Perform a systematic verification of the methods.

If source code is available, compare it with the manuscript.

Investigate:

1. Whether the manuscript accurately describes the implemented methods.
2. Whether experimental conditions were executed as described.
3. Whether dataset selection and preprocessing match the reported protocol.
4. Whether evaluation targets and ground truth are clearly defined.
5. Whether model inputs contain unintended information.
6. Whether model or experiment selection could bias results.
7. Whether reported metrics are computed correctly.
8. Whether important configuration choices are missing.
9. Whether the results support the claimed methodological contribution.
10. Whether another researcher could reasonably reproduce the central findings.

Identify mismatches between text, tables, algorithms, code, and results.

When a problem is found, distinguish:

- Confirmed methodological error
- Missing methodological explanation
- Potential experimental confounder
- Unsupported scientific interpretation
- Reproducibility limitation
- Minor documentation issue

Do not treat these categories as interchangeable.

For all serious issues, state what additional evidence would confirm or refute the concern.

---

# PHASE 5 — Generate Three Realistic IEEE ICHI Reviews

Write three complete conference-style reviews.

Use the following structure for each reviewer.

## Paper Summary

Provide an accurate technical summary demonstrating understanding of the manuscript.

## Strengths

Identify the most important scientific merits.

Explain why they matter.

## Major Weaknesses

Identify scientifically consequential issues.

For each weakness, report:

1. **Issue:** A precise description.
2. **Location:** Exact section, figure, table, equation, or paragraph.
3. **Evidence:** What in the manuscript supports the criticism.
4. **Scientific consequence:** Why the issue matters.
5. **Severity:** Critical / Major / Moderate.
6. **Remedy:** What would resolve the issue.
7. **Resolution type:** Clarification / Reanalysis / Reframing / Additional Experiment.

Avoid vague criticisms such as "evaluation is insufficient" without identifying what is missing and why.

## Minor Weaknesses

List smaller issues concerning clarity, presentation, terminology, or reporting.

## Questions for Authors

Provide three to five substantive questions whose answers could materially change the evaluation.

## Recommendation

Select one:

- Strong Reject
- Reject
- Borderline Reject
- Borderline Accept
- Accept
- Strong Accept

Explain the recommendation using the balance of scientific contributions and weaknesses.

## Reviewer Confidence

Rate confidence from 1 to 5.

Explain the basis for that confidence.

Do not claim expertise or knowledge that was not actually established.

Treat these as simulated reviewer assessments, not predictions of actual IEEE ICHI decisions.

---

# PHASE 6 — Senior Area Chair Metareview

After completing all three reviews, act as an experienced IEEE ICHI Senior Area Chair.

Your responsibility is to synthesize the evidence and assess the manuscript as a whole.

Do not simply average the three recommendations.

Identify:

1. Major strengths recognized across reviews.
2. Major weaknesses raised independently by multiple reviewers.
3. Serious concerns raised by only one reviewer.
4. Reviewer disagreements and their underlying reasons.
5. Concerns that are substantiated versus speculative.
6. Whether the paper's principal scientific contribution survives the criticisms.
7. Whether the evidence is sufficient for the stated conclusions.
8. Whether methodological weaknesses materially undermine the work.
9. Whether the paper makes a meaningful contribution to healthcare informatics.
10. The most defensible overall recommendation.

Write a concise but substantive metareview similar in rigor to a real area chair assessment.

The metareview should explain the decision rather than merely restating reviewer comments.

---

# PHASE 7 — Adversarial Self-Verification of the Reviews

Before finalizing the report, challenge your own criticisms.

Act as a second independent Senior Area Chair who suspects that some reviewer criticisms may be incorrect.

For every Critical or Major weakness:

1. Revisit the manuscript.
2. Locate the exact supporting evidence.
3. Check whether the authors addressed the concern elsewhere.
4. Determine whether the criticism relies on an incorrect assumption.
5. Distinguish an actual methodological flaw from unclear writing.
6. Assess whether the weakness genuinely affects the paper's central claims.
7. Determine whether its severity was exaggerated.
8. Withdraw or downgrade criticisms that cannot be substantiated.
9. Preserve serious concerns even if only one reviewer identified them.

**Agreement among simulated reviewers is not proof that a criticism is correct.**

Do not manufacture replacement criticisms when existing ones are withdrawn.

Produce a final list of verified issues with their justified severity levels.

---

# PHASE 8 — Time-Constrained Submission Rescue Plan

The manuscript must be submitted within a few hours.

Prioritize all verified weaknesses according to their scientific significance and feasibility of correction.

Use three categories.

## P0 — Submission-Threatening Problems

Examples:

- Invalid experimental design
- Incorrect statistical analysis
- Data leakage
- Incorrect evaluation implementation
- Major numerical inconsistencies
- Central conclusions contradicted by results
- Scientific claims unsupported by essential evidence
- Serious methodological errors

These issues may fundamentally undermine the manuscript.

## P1 — High-Impact, Immediately Fixable Problems

Examples:

- Missing methodological explanations
- Ambiguous experimental procedures
- Insufficient reporting of evaluation protocols
- Unclear baseline configurations
- Overstated claims
- Missing limitations
- Confusing descriptions of statistical findings
- Important inconsistencies between sections

These issues may significantly damage reviewer confidence but could be resolved through targeted revisions.

## P2 — Lower-Priority Improvements

Examples:

- Minor wording changes
- Organization
- Terminology
- Formatting
- Cosmetic figure improvements
- Additional explanatory examples

Do not allow P2 issues to distract from P0 and P1.

For each P0 and P1 issue, report:

**Problem:** What exactly is wrong?

**Location:** Where does it appear?

**Evidence:** What establishes the concern?

**Impact:** How could it affect acceptance?

**Proposed correction:** What is the smallest scientifically defensible solution?

**Requires new experiment:** Yes / No.

**Estimated effort:** Low / Medium / High.

**Replacement text:** Where a manuscript revision is sufficient, provide precise replacement wording without inventing data.

Rank issues by their expected scientific impact relative to the time required to fix them.

---

# PHASE 9 — Final Submission-Readiness Assessment

Provide a final assessment addressing:

1. Is the paper scientifically defensible in its current form?
2. What are its strongest contributions?
3. What are its most serious verified weaknesses?
4. Which weaknesses genuinely threaten acceptance?
5. Can the central claims survive without new experiments?
6. Are the results sufficiently supported?
7. What should be corrected before submission?
8. Which concerns should be disclosed as limitations rather than presented as resolved?
9. What are the five highest-impact revisions that can realistically be completed immediately?
10. What would remain unresolved even after those revisions?

Give a clear recommendation:

- **Submit after minor corrections**
- **Submit only after addressing specific major concerns**
- **Substantial scientific revision required**

Do not provide invented acceptance probabilities.

---

# CRITICAL REVIEW PRINCIPLES

Follow these rules throughout.

1. **Scientific rigor over superficial criticism.** Focus on issues that materially affect the contribution.

2. **Evidence over speculation.** Every major criticism must be grounded in the actual manuscript or verified supporting material.

3. **No fabricated weaknesses.** If the methodology is sound, acknowledge that.

4. **No fabricated literature.** Verify prior work when possible; otherwise qualify the novelty assessment.

5. **Distinguish evidence from interpretation.** An observed model behavior does not necessarily establish the mechanism causing it.

6. **No unnecessary experiments.** Recommend additional experiments only when they are needed to support a central claim.

7. **Respect the study's actual scope.** Do not demand clinical validation, causal proof, or external generalization unless the paper makes claims requiring such evidence.

8. **Do not confuse clarity with correctness.** An insufficient explanation does not automatically imply that the underlying method is invalid.

9. **Do not equate extensive evaluation with valid evaluation.** Numerous metrics and experiments do not compensate for flawed controls or unsupported conclusions.

10. **No automatic rejection bias.** The purpose is to reach a defensible evaluation, not to find reasons to reject at any cost.

11. **No automatic acceptance bias.** Strong results do not override serious methodological weaknesses.

12. **No fabricated verification.** Clearly report which calculations, implementation details, and citations were actually checked.

13. **No silent assumptions.** When information is unavailable, state the uncertainty.

14. **No manuscript modifications.** Review only. Do not edit any source files unless explicitly instructed.

15. **Conference realism.** Evaluate whether weaknesses are sufficiently consequential to influence actual peer-review decisions, rather than treating every possible improvement as mandatory.

---

# REQUIRED DELIVERABLE

Produce a comprehensive report named `ICHI_REVIEW_REPORT.md` with the following sections:

1. Executive Scientific Assessment
2. Reconstruction of the Paper's Contributions
3. Reviewer 1 — Methodology and Technical Soundness
4. Reviewer 2 — Experimental Evaluation and Statistical Validity
5. Reviewer 3 — Novelty and Healthcare Informatics Significance
6. Claim–Evidence Matrix
7. Methodological and Reproducibility Audit
8. Senior Area Chair Metareview
9. Adversarial Verification of Reviewer Criticisms
10. Verified P0, P1, and P2 Weaknesses
11. Ranked Pre-Submission Correction Plan
12. Five Highest-Impact Immediate Revisions
13. Final Submission-Readiness Recommendation

Use precise manuscript citations and concrete evidence throughout.

Begin by reading the complete manuscript. Do not skip the detailed review in favor of a quick summary.

**Final instruction:** Review this paper as though your assessment will determine whether the scientific contributions are credible enough for publication at IEEE ICHI. Your goal is to identify genuine rejection risks while preserving a fair assessment of the paper's scientific merits.



# REVIEW EFFICIENCY, CRITICALITY, AND CONDITIONAL REVISIONS

Your objective is to maximize the scientific value of the review, not its length.

## 1. Token Efficiency and Precision

- Be concise, technically precise, and evidence-driven.
- Do not repeat the same criticism across reviewers, audits, and the metareview. Reference previously identified issues by ID.
- Avoid generic observations, lengthy explanations of established concepts, unnecessary praise, and speculative concerns.
- Do not restate manuscript content unless necessary to establish a criticism.
- Allocate analytical effort according to scientific importance, not the number of review categories.
- If a section, method, experiment, or claim is sound, state that briefly and move on.
- Do not fill sections merely to satisfy the review template.
- Prioritize depth of reasoning over volume of text. A small number of rigorously substantiated findings is preferable to a long list of superficial concerns.

**Use as many tokens as necessary for rigorous analysis, but as few as necessary to communicate the findings. Do not sacrifice thorough manuscript inspection for a shorter response.**

## 2. Criticism Must Be Earned

Do not assume the manuscript requires corrections.

For every potential criticism, first determine:

1. Is there a demonstrable problem?
2. Is the concern scientifically consequential?
3. Is it supported by specific manuscript evidence?
4. Has the manuscript already addressed it?
5. Would resolving it materially improve scientific validity, reproducibility, or reviewer understanding?

Only retain criticisms that pass this examination.

Do not manufacture weaknesses to populate review sections.

Do not confuse possible improvements with necessary corrections.

## 3. Conditional Corrections and Revision Plans

**Corrections must be recommended only when a verified problem warrants them.**

- If the methodology is sound, do not propose methodological changes.
- If the evidence supports the claims, do not recommend weakening them.
- If an experiment is sufficient, do not demand additional experiments.
- If a limitation is already adequately acknowledged, do not repeat it as an unresolved weakness.
- If the manuscript is clear, do not rewrite it for stylistic preference.
- If no P0 or P1 issues exist, explicitly state: "No submission-critical or major corrections identified."

The revision plan is conditional, not mandatory.

Do not generate replacement paragraphs, experimental plans, or revision checklists for sections that require no correction.

If no substantive corrections are justified, omit the revision plan and recommend submission in its current form.

## 4. Severity Calibration

Assign severity according to demonstrated scientific consequences, not hypothetical reviewer reactions.

- **Critical:** A verified problem that substantially invalidates a central result or conclusion.
- **Major:** A significant weakness affecting confidence in a central contribution.
- **Moderate:** A legitimate issue affecting interpretation, reproducibility, or clarity without undermining the principal findings.
- **Minor:** A small presentation or documentation issue.

Do not inflate severity simply because an issue could theoretically attract reviewer criticism.

Distinguish confirmed defects from unresolved questions. Uncertainty alone is not evidence of error.

## 5. Output Discipline

- Lead with the overall scientific assessment.
- Present the most consequential findings first.
- Consolidate overlapping concerns into a single issue.
- Provide exact manuscript references for substantive criticisms.
- Explain each issue once, clearly and sufficiently.
- Present corrections immediately alongside verified problems rather than repeating them in several sections.
- Omit empty categories and redundant summaries.
- Do not enforce arbitrary numbers of weaknesses, questions, or recommendations.
- If the manuscript is scientifically defensible, say so explicitly.

**Final governing principle: The best review is not the harshest or longest review. It is the most accurate, discriminating, and scientifically useful review.**