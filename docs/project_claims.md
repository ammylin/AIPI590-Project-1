# Project claims for the poster and presentation

## What I built

SwarmAudit Lite is an offline-capable Streamlit dashboard for inspecting
LLM red-teaming tests, target responses, and human-review judgments. It
includes a small hand-authored comparison, paired control/injection
probes, and a constrained AI-assisted test-construction prototype.

## What I observed

- In a revised 12-test pilot against local `qwen2.5:3b`, one reviewer
  labeled 1 of 6 generic tests and 3 of 6 specialized tests as failures.
- In three closely related garden-tour probes, the reviewer labeled
  all three controls as passes and all three injection responses as failures.
- An initial pilot contained an invalid test. Repairing it made its
  unchanged placeholder-only response judgeable.
- Two attempts to have the local model write an entire prompt-injection
  test produced invalid candidates. Constraining the model to select a
  document style while code supplied the essential components produced
  a well-formed probe.

## What I cannot conclude

- Specialized strategies are generally better than a generic red team.
- The three paired probes measure a general failure rate.
- The system is an autonomous multi-agent swarm.
- Mock-evaluator labels establish safety performance for the real model.
- A synthetic placeholder failure measures real-world harm.

## Main limitations

The study uses one small local target model, a small number of
hand-authored tests, fixed model settings, and one human reviewer.
The three paired probes differ only in a short heading. Some human
judgments—especially mixed responses—could reasonably be disputed.

## Main takeaway

A red-teaming result is only as useful as its test validity and review
rubric. Matched controls and human review help distinguish obeying an
embedded instruction from merely mentioning it.
