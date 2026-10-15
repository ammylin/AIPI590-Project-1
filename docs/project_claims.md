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
