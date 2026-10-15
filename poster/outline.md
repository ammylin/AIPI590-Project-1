# SwarmAudit Lite — Poster Outline

## Title
SwarmAudit Lite: Human-Reviewed Prompt-Injection Evaluation

## Research question
How can test validity, matched controls, and human review help distinguish
genuine prompt-injection failures from misleading evaluation results?

## Motivation
A model response that mentions an embedded instruction is not necessarily
following it. Invalid tests and simplistic automated labels can make
red-teaming results misleading.

## What I built
- Offline-capable Streamlit dashboard
- Small, hand-authored generic-versus-specialized test pilot
- Human-review rubric and preserved review data
- Three matched control/injection probes
- Constrained AI-assisted test-construction prototype

## Method
1. Run safe, synthetic tests against local qwen2.5:3b.
2. Save raw responses separately from human labels.
3. Review whether each test is valid and whether the response completes
   the legitimate task or follows an embedded instruction.
4. Compare descriptive pilot results and inspect matched pairs.

## Results
- Revised pilot: generic tests — 1/6 human-labeled failures;
  specialized tests — 3/6 human-labeled failures.
- Three closely related paired probes: all controls labeled pass;
  all injection responses labeled failure.
- An invalid test in the first pilot changed from invalid to a
  judgeable failure after its legitimate task was repaired.
- Two unconstrained AI-generated candidate tests were rejected as invalid.

## Recommended visuals
- Screenshot of the dashboard's side-by-side control/injection view
- Small table of revised pilot labels
- Diagram: test → target response → human review → dashboard
- Example showing “mentions instruction” versus “obeys instruction”

## Limitations
One small model, one reviewer, 12 hand-authored pilot tests, and three
closely related paired probes. No autonomous multi-agent swarm. These
results do not estimate general failure rates or real-world harm.

## Takeaway
Better red-teaming requires valid tests and careful review—not just more
prompts or a count of placeholder appearances.

## Links
GitHub repository: https://github.com/ammylin/AIPI590-Project-1
Dashboard: run locally using the README instructions