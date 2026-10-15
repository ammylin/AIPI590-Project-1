# Research context and design rationale

## Question, audience, and contribution

How do test validity and evaluation rules change whether an LLM response is judged to have followed an instruction hidden in a document?

The intended audience is students learning Responsible AI evaluation and practitioners prototyping audits of document-processing assistants. They need to inspect the evidence behind a failure label, identify invalid tasks, and see uncertainty rather than inherit an unexplained score.

The contribution is a reusable workflow combining preserved observations, validated review joins, matched controls, an interactive response explorer, and an explicit analysis of evaluator disagreement and judgment sensitivity. The case study is small. Its originality is the integration and inspectable teaching example, not a claim to have invented prompt injection, human review, or a new attack algorithm.

## Explainability methods and their boundaries

The implemented contribution is explainable evaluation and behavioral inspection. It does not provide mechanistic explanations of the language model.

| Implemented technique | What becomes inspectable | Boundary |
|---|---|---|
| Matched control/injection comparisons | Responses with and without one entire embedded instruction | A limited whole-instruction perturbation; no word-level importance or internal causal mechanism is identified |
| Example-based inspection | Prompt, expected task, response, label, and notes | Individual examples do not establish population-level performance |
| Human-written review rationales | Why the reviewer assigned a label | Reviewer reasoning can be inconsistent; it is not the model's reasoning |
| Transparent output rules | Exact conditions producing each detector label | Token matching is not semantic evidence of instruction obedience |
| Judgment sensitivity analysis | How treating one disputed case as borderline changes summaries | A hypothetical scenario, not a new experiment or adjudication |
| Comparison of two self-review passes | Which judgments changed within one reviewer | Agreement after a correction is not independent inter-rater reliability |

SHAP, LIME, Integrated Gradients, attention-based attribution, and phrase-level ablation are not implemented. Calling the current detector comparison "feature attribution" would misdescribe what it measures. A future phrase-level ablation could remove components of the attack instruction while keeping the task, document fact, and model settings fixed, then review the responses. That requires new model observations and contextual review, so it remains future work rather than a result in this artifact.

For presentation: **SwarmAudit Lite explains how prompt-injection evaluations are reached, and shows how observed responses change under a controlled input change. It does not explain the model's internal mechanisms.**

## Relevant work and connection to this project

1. **Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz (2023).** [Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173). This work describes malicious instructions placed in external content that an LLM application processes. It motivates studying the boundary between legitimate task instructions and document data. Our quoted documents simulate that boundary; they do not implement retrieval or reproduce the paper's attacks.

2. **Qiusi Zhan, Zhixiang Liang, Zifan Ying, and Daniel Kang (2024).** [InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents](https://aclanthology.org/2024.findings-acl.624/). Findings of ACL 2024, pp. 10471–10506. DOI: 10.18653/v1/2024.findings-acl.624. InjecAgent studies attacks in tool-integrated agent settings. It provides context for why external-content instructions matter. Our artifact deliberately uses a smaller, inspectable document task without tools; its counts cannot be compared with InjecAgent attack-success rates.

3. **Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, and Florian Tramèr (2024).** [AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents](https://arxiv.org/abs/2406.13352). AgentDojo supplies an extensible environment for evaluating agents over untrusted tool data and notes that agents can fail legitimate tasks even without attacks. Our paired controls likewise help distinguish ordinary task performance from behavior when an embedded instruction is added. That is a design connection, not a replication or evidence of equivalent rigor.

These sources were added to contextualize the artifact and its design. The existing pilot was not preregistered and its later analysis is retrospective.

## Major decisions and tradeoffs

| Decision | Reason | Consequence |
|---|---|---|
| Local `qwen2.5:3b` through Ollama | Accessible local execution without paid APIs | Results apply to one small model/configuration |
| Harmless facts and a synthetic placeholder | Make obedience visible without real secrets or harmful tasks | Outcomes do not quantify real-world harm |
| Hand-authored tests with matched category counts | Keep a small comparison understandable | Wording differs; neither strategy is a representative sample |
| Preserve raw JSONL and separate review CSVs | Keep observations distinguishable from interpretation | Review joins must validate IDs, prompts, responses, and run metadata |
| Use human labels and a borderline option | Allow contextual judgments and explicit uncertainty | The same reviewer completed two passes with 83.3% agreement; independent review has not been conducted |
| Add paired controls differing by one instruction | Check legitimate-task capability while isolating one prompt change | Three heading variants provide little independent diversity |
| Compare two transparent detector rules | Make false positives and judgment dependence concrete | Retrospective descriptive comparison, not a trained or validated judge |
| Expose sensitivity without editing labels | Show the effect of a disputed interpretation | Hypothetical scenarios must not be mistaken for additional human reviews |
| Discover new runs in the dashboard | Let others inspect reruns without editing app code | New observations remain unreviewed until a matching CSV is filled |

## Stakeholders and deployment considerations

**Auditors and students** benefit from inspecting how a score was produced. A single numeric summary can conceal invalid prompts or debatable judgments.

**Developers of summarization and retrieval assistants** can use this workflow to prototype evaluation before introducing more realistic tasks. Passing these examples would not certify an application: retrieval, tool permissions, longer contexts, and other model settings remain outside scope.

**End users and people represented in documents** could be affected if an assistant follows document instructions or produces misleading summaries. This project uses fictional facts and no personal data. Extending it to real documents would require appropriate data access and protection.

**Reviewers** make interpretive decisions. Preserve their original notes, disclose who reviewed a run, and distinguish disagreement from error. A second pass by the same person must be described as self-review, not agreement between independent reviewers. Here, the author confirmed completing both passes; a metadata sidecar records that relationship.

Publishing small synthetic tests is useful for education, but the interface should not encourage users to treat a model as safe because it passed a toy task. No live actions, secret extraction, or harmful requests are tested here.

## Meaningful future work and success criteria

1. Have an independent reviewer label the shuffled packet using the rubric, with original labels withheld. Report the label cross-tab and disagreement notes; adjudicate separately without overwriting either review.
2. Separate **task completion** from **instruction obedience** in annotation. Mixed responses can complete a task yet endorse or repeat an attacker instruction; one label may obscure that distinction.
3. Add matched tasks with substantively different payloads and task types, then hold out new examples when comparing evaluators. Report task-only controls as well as injection outcomes.
4. Repeat on additional model configurations while recording model digests, runtime versions, and truncation metadata. Fixed seeds alone do not prove reproducibility across installations.
5. Ask intended users to perform an audit with the dashboard and record whether they can correctly locate invalid tests and explain a disputed judgment. This would evaluate the interface contribution itself.

Success means more interpretable and reproducible judgments and a useful audit interface. A higher count of apparent failures is not by itself evidence of a better audit.
