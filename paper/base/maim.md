1. General ML: "right answer, wrong reasoning" is well-established (already flagged in your critique notes). Gururangan et al. 2018 (annotation artifacts in NLI), McCoy et al. 2019 ("HANS" — right answers via syntactic heuristics, not entailment). This establishes the general phenomenon exists across ML, not just LLMs.

2. LLM-specific: chain-of-thought faithfulness literature. A stated reasoning chain often doesn't reflect the model's actual computation — Lanham et al. 2023 ("Measuring Faithfulness in Chain-of-Thought Reasoning", Anthropic) established this, and it's an active area: recent work like "Chain-of-Thought Reasoning In The Wild Is Not Always Faithful" (2025) and "Breaking the Chain: A Causal Analysis of LLM Faithfulness to Intermediate Structures" (2026) are directly about whether a model's intermediate reasoning steps causally support later steps — which is exactly the gating question KAB asks.

3. Domain-specific, and this is the important one to look at closely: "Breaking Failure Cascades: Step-Aware Reinforcement Learning for Medical Multimodal Reasoning" (arXiv 2606.31825) — this appears to already study cascading reasoning failures specifically in medical multimodal models, step-by-step. Also relevant: HEAL-MedVQA's textual/visual shortcut-learning benchmark, and the "First Failure Point" metric (where in a reasoning trace the first invalid step occurs) from recent medical-reasoning failure analysis work.

4. Clinical grounding for why the 5-phase structure itself is valid, not arbitrary: Croskerry's dual-process model of clinical cognition ("Clinical cognition and diagnostic error," 2009) is the standard citation for why diagnostic reasoning is a sequential, error-compounding cognitive process in real clinicians — gives the clinical-science basis for treating AIA→LIL→DSCR→PJRF→TCM as a real dependency chain, not just a convenient framework design.

One thing you need to check before the professor meeting: that "Breaking Failure Cascades" paper looks close enough to what KAB's gating mechanism does that you should read it and be ready to say explicitly how our contribution differs (dataset construct validity + KB-grounded faithfulness + feedback-adaptation, vs. whatever their step-aware RL approach does) — better to know that going in than have the professor find it first.

Sources:
- Chain-of-Thought Reasoning In The Wild Is Not Always Faithful
- Breaking the Chain: A Causal Analysis of LLM Faithfulness to Intermediate Structures
- Breaking Failure Cascades: Step-Aware Reinforcement Learning for Medical Multimodal Reasoning
- Localizing Before Answering: A Hallucination Evaluation Benchmark for Grounded Medical Multimodal LLMs
- Clinical cognition and diagnostic error: applications of a dual process model of reasoning