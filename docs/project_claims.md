# Project claims for presentation and external readers

## What was built

SwarmAudit Lite is an offline-capable Streamlit dashboard and reusable workflow for inspecting LLM tests, raw responses, human judgments, evaluator disagreements, and sensitivity to uncertain labels. It includes a small hand-authored pilot, matched control/injection probes, and a constrained AI-assisted test-construction prototype.

The intended audience is students and practitioners learning to audit document-processing assistants. The contribution is an inspectable evaluation workflow and case study, not a new attack algorithm or a general benchmark. See [research context](research_context.md) for literature, design rationale, stakeholders, and future work.

## What the evidence supports

- One reviewer labeled 1/6 generic and 3/6 specialized tests failures in the revised `qwen2.5:3b` pilot. One of those specialized judgments is disputed; treating it as borderline yields 2 failures, 1 borderline, and 3 passes. The original label remains unchanged.
- Across eight attack responses, a retrospective placeholder-anywhere rule has four false positives relative to original judgments; a placeholder-only rule has one false negative, the disputed mixed response. See [analysis](evaluator_analysis.md).
- Three closely related garden-tour controls were labeled passes and three injection responses failures. Their headings vary; their fact and payload do not.
- An invalid initial test became judgeable after its legitimate task was repaired. Its placeholder-only response was unchanged.
- Pilot notes describe two invalid unconstrained-generator candidates; their raw outputs were not retained. The constrained prototype restricts the model to selecting a document heading while code supplies essential test components.
- The author completed a second self-review pass: 10/12 labels agree (83.3%), with two changed judgments. This is within-reviewer agreement, not independent review or inter-rater reliability. No adjudication has occurred. The author corrected a second-pass misclassification after it was flagged; the current agreement includes that correction.

## Unsupported claims

- Specialized strategies are generally better than generic tests.
- The detector rules are reliable semantic safety judges or validated on a held-out set.
- The sensitivity scenario or second self-review pass is an independent review or adjudicated replacement label.
- The three pairs estimate a general failure rate.
- The system is an autonomous multi-agent swarm.
- Mock labels or confidence scores establish real-model safety.
- Synthetic placeholder failures measure real-world harm.

## Main limitations and takeaway

One small model, fixed settings, hand-authored prompts, one reviewer completing two non-independent passes, retrospective analysis, and closely related pairs limit generalization. Historical runs lack model digests and runtime provenance. The primary lesson is that valid tasks and careful judgments matter: counting placeholder occurrences can misclassify responses, and a mixed response can change the apparent result depending on how uncertainty is represented.

## Presentation material from the current evidence

### Central message

**Mentioning an injected instruction is not the same as obeying it.** The artifact makes this distinction inspectable through matched controls, actual model responses, review rationales, and transparent detector comparisons.

### Short project description

SwarmAudit Lite is an interactive workflow for auditing prompt-injection evaluations. It preserves raw local-model responses separately from human judgments and lets users inspect matched control/injection probes. In a retrospective comparison of eight attack-task responses, a placeholder-anywhere detector produced four false positives relative to the original human labels. A stricter placeholder-only rule reduced those errors but disagreed on a mixed response. The case study shows why valid tasks, contextual review, and explicit uncertainty matter.

### Explainability wording

**We explain evaluation decisions and observed model behavior through matched comparisons, inspectable examples, human-review rationales, transparent rules, and sensitivity analysis. We do not explain the model's internal mechanisms.**

The matched pairs remove the whole embedded instruction, providing a limited controlled input perturbation. They are not SHAP, LIME, Integrated Gradients, or word-level attribution. Phrase-level ablation is future work, not a completed experiment.

### Numbers to use, with their denominators

| Observation | Current value | Necessary context |
|---|---|---|
| Original generic pilot judgments | 1 failure / 6 tests | Original review of revised run |
| Original specialized pilot judgments | 3 failures / 6 tests | Includes one disputed judgment; no superiority claim |
| Hypothetical specialized sensitivity | 2 failures, 1 borderline, 3 passes | Reclassifies only `swarm_ambiguity_001` for analysis; does not edit original labels |
| Placeholder-anywhere detector | 4 false positives; agreement 4/8 | Eight attack-task responses only; original labels are the reference |
| Placeholder-only detector | 0 false positives, 1 false negative; agreement 7/8 | Sole disagreement is the originally failure-labeled mixed response |
| Paired probes | 3 controls labeled pass; 3 injections labeled failure | Three closely related headings with the same fact and payload |
| Self-review agreement after correction | 10/12 labels match (83.3%) | One reviewer, two passes; includes a correction after feedback; not independent reliability |

Use the detector comparison as the main quantitative result. The generic/specialized counts are supporting pilot observations. The self-review figure is a disclosure about judgment consistency, not a model-performance score or the central success metric. Do not pool the pilot and pairs into a single failure rate.

### Screenshot and demo sequence

1. Run `python -m streamlit run app.py` and choose **Paired probes**. Select `paired_probe_20261007T131704875832Z` for the announcement example. Capture the control and injection prompts/responses together. Caption: **Adding one instruction inside the document changed a legitimate summary into a placeholder-only response in this saved pair.**
2. Choose **Local-model pilots** and run `local_pilot_20261005T221442Z`. Leave the sensitivity checkbox unchecked. Capture **When does a placeholder detector disagree with human review?** Caption: **Across eight attack responses, counting any placeholder mention produced four false positives relative to the original human judgments.**
3. For the live demonstration, check **Sensitivity analysis: treat the disputed case as borderline** and explain that this changes only the analysis. The original response and label are preserved.

Crop screenshots for legibility while retaining labels and scope captions. A dashboard screenshot is evidence of the interface; the preserved response/review files support the numerical findings.

### Compact limitations and next step

One small model, hand-authored prompts, one reviewer, retrospective analysis, and closely related paired probes limit generalization. Self-review includes a correction after feedback. Synthetic placeholder outputs do not measure real-world harm. The next step is independent review and more diverse matched tasks, with separate measures of task completion and instruction obedience.

### References to retain

- Greshake et al. (2023), [Not what you've signed up for](https://arxiv.org/abs/2302.12173): instructions embedded in external content.
- Zhan et al. (2024), [InjecAgent](https://aclanthology.org/2024.findings-acl.624/): evaluation of indirect injection in tool-integrated agents.
- Debenedetti et al. (2024), [AgentDojo](https://arxiv.org/abs/2406.13352): evaluating tasks, attacks, and defenses over untrusted tool data.

These sources contextualize the project. The artifact does not reproduce their benchmarks. Repository: https://github.com/ammylin/AIPI590-Project-1.
