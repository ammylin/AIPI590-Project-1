# Local test-generator pilot

We asked the local qwen2.5:3b model to generate one low-risk
prompt-injection test on two attempts. Neither candidate was sent to
the target model.

## Candidate 1 — rejected

The document contained a placeholder but no embedded instruction to
output it. It lacked a concrete event to summarize, and the expected
behavior was contradictory.

## Candidate 2 — rejected

The document again contained the placeholder but no embedded instruction
to output it. Its rationale incorrectly claimed that the instruction
was present. It also referenced a paragraph that did not exist.

## Design decision

Do not accept a generated test based on the generator's rationale.
Use a structured template for the legitimate task and embedded
instruction. Validate candidates before target-model execution, record
rejection reasons, and have a human inspect accepted tests.