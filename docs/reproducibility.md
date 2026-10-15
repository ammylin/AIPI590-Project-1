# Reproducing and extending the project

Run commands from the repository root. Python 3.11 is the recommended baseline. The analysis, review-packet, and validation tools use the standard library; the dashboard needs the pinned dependencies in `requirements.txt`.

## View the artifact

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No hosted API, key, network service, or model is needed to view the checked-in evidence. The README describes the datasets and their provenance.

## Reproduce the included analysis

```bash
python -m src.analyze_reviewed_pilot
python -m src.summarize_local_pilot data/local_review_20261005T221442Z.csv
python -m src.validate_paired_probe results/paired_probes/paired_probe_20261007T131704875832Z.jsonl
python -m src.validate_paired_probe results/paired_probes/paired_probe_20261013T234602749276Z.jsonl
python -m src.validate_paired_probe results/paired_probes/paired_probe_20261013T234623243236Z.jsonl
```

The first command regenerates `results/analysis/reviewed_pilot_audit.json` deterministically from existing evidence; it overwrites only that derived report. It does not modify source JSONL or review CSVs. The report includes source SHA-256 hashes. Original and revised pilots must not be pooled as independent trials.

## Rerun the model experiments (optional)

Install [Ollama](https://ollama.com/) separately. Start its service, then download the model:

```bash
ollama pull qwen2.5:3b
```

Ollama must serve its chat API at `http://localhost:11434`. No paid API is used. A model download requires storage, network access, and a machine capable of running it.

```bash
python -m src.run_local_pilot
python -m src.run_paired_probe --style announcement
python -m src.run_paired_probe --style newsletter
python -m src.run_paired_probe --style meeting_note
```

Each command prints its new timestamped result path. Raw result files use exclusive creation to avoid replacing earlier runs. The pilot runner records request errors per test; inspect them before review. A pair command that fails midway can leave a partial JSONL file; complete/retry the run and keep partial files outside the discovered result directories until they are ready for inspection.

The requests use model `qwen2.5:3b`, temperature `0`, seed `42`, `num_predict=128`, and the system prompt in `src/local_target.py`. Those settings are recorded with each observation. The model is told to complete the legitimate task and treat instructions inside documents as content.

Historical files do not contain model digests, the Ollama version, hardware details, or response termination metadata. Exact regeneration cannot be guaranteed from a model tag and seed. New runs additionally record the available model digest, Ollama version, and termination/token metadata; compare these before interpreting differences. Preserve earlier runs rather than replacing their evidence.

## Review a new run

Replace the example paths below with the actual paths printed by the runner:

```bash
python -m src.create_local_review results/local_pilot_NEW_RUN_ID.jsonl
python -m src.create_pair_review results/paired_probes/paired_probe_NEW_RUN_ID.jsonl
```

These commands create blank CSVs with the matching observation fields and refuse to overwrite existing reviews. Fill `human_label` and `human_notes` using [the rubric](review_rubric.md). Use `borderline` when evidence is mixed and `invalid` when the task cannot support the intended judgment. Do not edit prompt or response columns. Missing/blank labels are unreviewed; unexpected labels or stale observation fields are rejected by the dashboard.

```bash
python -m src.summarize_local_pilot data/local_review_NEW_RUN_ID.csv
python -m src.analyze_reviewed_pilot --results results/local_pilot_NEW_RUN_ID.jsonl --reviews data/local_review_NEW_RUN_ID.csv --output results/analysis/new_run_audit.json
```

Refresh/rerun the Streamlit app. New pilot and paired JSONL files automatically appear in the run selectors. Their matching review filenames are discovered without editing `app.py`.

## Completed self-review and future independent review

The author completed `data/independent_review/second_review_20261005T221442Z.csv` themselves. The completed packet is a **second self-review pass**, not an independent reviewer. The `.metadata.json` sidecar records `same_reviewer`; the retained directory name and `reviewer_002` ID are historical identifiers only.

The passes agree on 10/12 labels (83.3%). The comparison report lists two changed judgments and both rationales. No adjudication has been performed, and the original pilot and detector summaries retain their original labels. The current agreement includes the author's correction of a second-pass misclassification; see [the analysis](evaluator_analysis.md#completed-self-review-pass).

To regenerate the derived report:

```bash
python -m src.compare_second_review --overwrite
```

The command rejects incomplete or altered observations, reads the saved relationship declaration, and hashes its source files. `--overwrite` affects only the derived JSON report. Without that flag, existing reports remain protected. To preserve multiple report versions, supply a different `--output` path.

For a future review by a different person, generate a fresh packet in a separate directory, even if reusing the same model run:

```bash
python -m src.create_second_review --results results/local_pilot_20261005T221442Z.jsonl --output-dir data/future_review
```

Give that person only the new CSV and the general rubric, withholding the project-specific provenance paragraph, original labels, findings, and linkage key until review is finished. The original author must not fill this new packet on their behalf. Fill a consistent reviewer ID, labels, and evidence notes without changing observations. Shuffling does not guarantee blindness or independence.

After a genuinely independent review has been completed, use `--packet` for its CSV, a new `--output`, and `--review-relationship independent_reviewer`. This declaration describes the actual procedure; code cannot verify independence. For another self-review, declare `same_reviewer`. If no declaration or metadata is supplied, the comparison reports `unspecified` and makes no independence claim. Record any later adjudication separately without overwriting the review passes.

## Constrained generation prototype

```bash
python -m src.structured_generator
python -m src.paired_probe
```

The first command calls the local model to select one of three styles and prints a code-constructed test. It does not save a generator transcript or submit that test to the target. The second constructs and validates an announcement pair locally without calling a model. The pair runner takes an explicit style; it does not run autonomous generation. The two rejected unconstrained-generation attempts have narrative notes only, with no retained raw candidates or rerunnable generation script.

## Mock pipeline

```bash
python -m src.run_offline_experiment
```

This regenerates `results/offline_experiment.jsonl` using a deterministic mock target and the legacy mock evaluator. It overwrites that demo file; do not interpret its labels as real-model performance. Its confidence scores are illustrative constants.

## Verification

```bash
python -m unittest discover -s tests -v
python -m unittest tests.test_dashboard -v
```

The main suite checks saved evidence/review integrity, detector errors and exclusions, source hashes, paired comparisons, review-pass provenance and validation, and the original strategy/evaluator checks. Dashboard tests use Streamlit's `AppTest` to navigate all datasets, saved runs, and the sensitivity view. They do not query Ollama. No new model responses or completed human reviews are required.

On October 14, 2026, all 20 regression and dashboard checks passed in a fresh Python 3.11 environment installed from `requirements.txt`; `pip check` also passed. No live model experiment or new human review was performed during that verification; reviewer input is read from the saved packets.

If an older environment stalls while importing NumPy/pandas before the app starts, test with a fresh environment instead of interpreting the stall as an evaluation result:

```bash
python3.11 -m venv .venv-fresh
source .venv-fresh/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
