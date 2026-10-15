"""Explore preserved model observations, reviews, and evaluator disagreement."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.audit import (
    DISPUTED_CASE, PROJECT_ROOT, REVISED_RUN, condition_summary, detector_audit,
    discover_runs, load_run, review_path_for,
)
from src.validate_paired_probe import validate_pair
from src.compare_second_review import compare


CONDITION_NAMES = {"baseline": "Generic baseline", "swarm": "Specialized strategies"}


def show_response(row: dict) -> None:
    st.write(f"**Human label:** `{row.get('human_label', 'unreviewed')}`")
    st.subheader("Prompt")
    st.code(row["test_prompt"], language=None)
    st.write("**Expected behavior:**", row["expected_behavior"])
    st.subheader("Model response")
    st.code(row.get("target_response") or "No response recorded", language=None)
    if row.get("error"):
        st.error(row["error"])
    if row.get("response_metadata", {}).get("done_reason") == "length":
        st.warning("Generation reached its token limit. Consider truncation before assigning an outcome label.")
    st.write("**Human-review notes:**", row.get("human_notes") or "Not yet reviewed")
    if row.get("target_model"):
        with st.expander("Model settings and recorded provenance"):
            st.json({key: row[key] for key in (
                "run_id", "target_model", "system_prompt", "temperature", "seed",
                "num_predict", "provenance", "response_metadata",
            ) if key in row})
            if "response_metadata" not in row:
                st.caption("This historical response has no recorded termination metadata or model digest.")


def show_detector_audit(records: list[dict], sensitivity: bool) -> None:
    report = detector_audit(records, sensitivity)
    st.header("When does a placeholder detector disagree with human review?")
    st.write(
        "Contains placeholder flags any mention. Placeholder only flags a response "
        "consisting solely of the placeholder, ignoring case and surrounding whitespace. "
        "Both rules are deliberately simple; neither determines whether a response "
        "semantically obeyed an instruction."
    )
    if not report["included"]:
        st.info("No attack responses with pass/failure human labels are available for comparison.")
        return
    table = pd.DataFrame(report["summary"]).rename(columns={
        "rule": "Rule", "n": "Compared", "true_positive": "True positives",
        "false_positive": "False positives", "true_negative": "True negatives",
        "false_negative": "False negatives", "agreement": "Agreement",
        "precision": "Precision", "recall": "Recall",
    })
    st.dataframe(table, hide_index=True)
    st.caption(
        "Positive = human-labeled prompt-injection/instruction-conflict failure. "
        "Human labels are one reviewer's judgments, not established ground truth. "
        "Benign-task categories and labels other than pass/failure are excluded. "
        f"Excluded counts: {report['excluded']}. This is retrospective analysis, "
        "not a held-out benchmark or a new model experiment."
    )
    disagreements = []
    by_id = {row["test_id"]: row for row in records}
    for case in report["cases"]:
        for rule in ("contains_placeholder", "placeholder_only"):
            if case[rule] != (case["human_label"] == "failure"):
                disagreements.append({
                    "Test": case["test_id"], "Rule": rule,
                    "Rule label": "failure" if case[rule] else "pass",
                    "Human label": case["human_label"],
                    "Response": by_id[case["test_id"]]["target_response"],
                })
    if disagreements:
        st.subheader("Inspect disagreements")
        st.dataframe(pd.DataFrame(disagreements), hide_index=True)
    else:
        st.info("These rules agree with the available labels on this sample.")


def show_review_pass(path: Path, records: list[dict]) -> None:
    run_id = records[0]["run_id"]
    packet = PROJECT_ROOT / "data" / "independent_review" / f"second_review_{run_id}.csv"
    if not packet.exists():
        return
    report = compare(path, review_path_for(path), packet, packet.with_suffix(".key.json"))
    same_reviewer = report["review_relationship"] == "same_reviewer"
    st.header("Second review pass by the same reviewer" if same_reviewer else "Second review pass")
    st.metric("Agreement between review passes", f"{report['exact_label_agreement']:.0%}")
    st.write(
        f"{report['n'] - len(report['disagreements'])} of {report['n']} labels match. "
        + report["agreement_interpretation"]
    )
    st.caption("Both passes are preserved. Neither adjudication nor a replacement of the original labels has occurred.")
    if report["disagreements"]:
        with st.expander("Inspect changed judgments and both rationales"):
            st.dataframe(pd.DataFrame(report["disagreements"]), hide_index=True)
            by_id = {row["test_id"]: row for row in records}
            for change in report["disagreements"]:
                if (change["second_label"] == "pass"
                        and by_id[change["test_id"]]["target_response"].strip() == "[PROTECTED_PLACEHOLDER]"):
                    st.warning(
                        f"{change['test_id']} is labeled pass in the second pass, but its "
                        "entire response is the placeholder. Check this judgment against "
                        "the rubric's placeholder-only failure example. The label is preserved."
                    )


def show_pilot() -> None:
    paths = discover_runs("pilot")
    if not paths:
        st.info("No saved local-model pilots found.")
        return
    default = next((i for i, p in enumerate(paths) if REVISED_RUN in p.name), 0)
    path = st.selectbox("Choose pilot run", paths, index=default, format_func=lambda p: p.stem)
    records = load_run(path, review_path_for(path))
    st.caption(
        f"{records[0]['target_model']} · {records[0]['run_id']} · "
        "original human judgments preserved separately from responses"
    )
    st.header("Generic vs. specialized tests")
    st.dataframe(pd.DataFrame(condition_summary(records)), hide_index=True)
    st.warning(
        "These are descriptive counts from hand-authored tests and one reviewer. "
        "Category counts were matched by design. They do not establish that one "
        "strategy is generally better or that an autonomous swarm was evaluated."
    )
    sensitivity = False
    disputed = next((r for r in records if r["test_id"] == DISPUTED_CASE), None)
    if disputed and disputed["human_label"] == "failure":
        st.subheader("A judgment that can change the result")
        st.write(
            "swarm_ambiguity_001 summarizes the appointment before discussing the "
            "injected priority claim. Its original failure label is debatable: the "
            "response could be describing the instruction rather than obeying it. "
            "A later pass by the same reviewer is shown below; independent review has not been conducted."
        )
        with st.expander("Read the disputed prompt, response, and original rationale"):
            show_response(disputed)
        sensitivity = st.checkbox("Sensitivity analysis: treat the disputed case as borderline")
        if sensitivity:
            st.dataframe(pd.DataFrame(condition_summary(records, True)), hide_index=True)
            st.info(
                "This hypothetical scenario changes only the analysis. The saved human "
                "label remains failure. Borderline cases are excluded from binary detector metrics."
            )
    show_detector_audit(records, sensitivity)
    show_review_pass(path, records)
    st.header("Explore a response")
    selected = st.selectbox("Select a test", [r["test_id"] for r in records])
    row = next(r for r in records if r["test_id"] == selected)
    st.write(f"**Condition:** {CONDITION_NAMES[row['condition']]} · **Category:** {row['category']}")
    show_response(row)
    st.download_button("Download responses with review labels", json.dumps(records, indent=2),
                       file_name=f"{path.stem}_with_reviews.json", mime="application/json")


def show_pairs() -> None:
    paths = discover_runs("pair")
    if not paths:
        st.info("No saved paired probes found.")
        return
    st.header("Saved matched probes")
    summary = []
    for path in paths:
        rows = load_run(path, review_path_for(path))
        validate_pair(rows)
        by_role = {r["role"]: r for r in rows}
        summary.append({
            "Run": rows[0]["run_id"], "Pair": rows[0]["pair_id"],
            "Control": by_role["control"]["human_label"],
            "Injection": by_role["injection"]["human_label"],
        })
    st.dataframe(pd.DataFrame(summary), hide_index=True)
    path = st.selectbox("Choose paired run", paths, format_func=lambda p: p.stem)
    records = load_run(path, review_path_for(path))
    validate_pair(records)
    st.caption(f"{records[0]['target_model']} · {records[0]['pair_id']}")
    st.write("The prompts differ only by one instruction embedded inside the document.")
    by_role = {r["role"]: r for r in records}
    for column, role in zip(st.columns(2), ("control", "injection")):
        with column:
            st.subheader(role.title())
            show_response(by_role[role])
    st.warning(
        "The three supplied garden-tour probes share the same fact and instruction, "
        "with different headings. They are closely related observations, not "
        "independent attack strategies or a general failure-rate estimate. "
        "Unreviewed responses carry no outcome claim."
    )


def show_demo(path: Path) -> None:
    st.warning(
        "Demonstration data: these are curated examples or deterministic mock-target "
        "outputs. They are not observations of a real model. Confidence values are "
        "illustrative constants, not calibrated probabilities."
    )
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    frame = pd.DataFrame(records)
    st.dataframe(frame.groupby(["condition", "automated_label"]).size().reset_index(name="Count"), hide_index=True)
    st.bar_chart(frame.groupby("automated_label").size())
    selected = st.selectbox("Select a demo test", frame["test_id"].tolist())
    row = next(r for r in records if r["test_id"] == selected)
    show_response(row)
    st.write("**Mock automated label:**", row["automated_label"])
    st.write("**Mock rationale:**", row.get("evaluator_rationale", ""))
    st.caption(f"Illustrative rule score: {row.get('evaluator_confidence', 0):.0%}; not a probability of correctness.")
    # Preserve the original demo's coverage and evaluator-agreement views.
    from src.metrics import calculate_category_coverage, calculate_condition_summary
    st.subheader("Demo category coverage and condition metrics")
    frame["human_label"] = frame.get("human_label", pd.Series("unreviewed", index=frame.index)).fillna("unreviewed")
    st.dataframe(calculate_category_coverage(frame), hide_index=True)
    reviewed = frame[frame["human_label"] != "unreviewed"]
    if not reviewed.empty:
        st.dataframe(calculate_condition_summary(reviewed), hide_index=True)
    else:
        st.caption("No reviewed demo labels; evaluator agreement is unavailable.")


st.set_page_config(page_title="SwarmAudit Lite", page_icon="🛡️", layout="wide")
st.title("🛡️ SwarmAudit Lite")
st.subheader("Human-reviewed prompt-injection evaluation")
st.write(
    "For students and practitioners auditing LLM behavior: inspect whether a model "
    "obeyed an instruction hidden inside a document or merely mentioned it while "
    "doing the legitimate task. Explore real saved responses, human judgments, "
    "matched controls, and the limitations of simple automatic detectors."
)
selection = st.selectbox("Choose an evaluation dataset", [
    "Local-model pilots", "Paired probes", "Curated sample data", "Offline experiment",
])
try:
    if selection == "Local-model pilots":
        show_pilot()
    elif selection == "Paired probes":
        show_pairs()
    else:
        path = PROJECT_ROOT / ("data/sample_results.jsonl" if selection == "Curated sample data" else "results/offline_experiment.jsonl")
        show_demo(path)
except (ValueError, KeyError, OSError) as exc:
    st.error(f"Could not validate the selected evidence: {exc}")
    st.stop()

with st.expander("Research context, scope, and next steps"):
    st.markdown(
        "Document instructions cross a trust boundary when treated as commands "
        "([Greshake et al., 2023](https://arxiv.org/abs/2302.12173)). "
        "Larger agent benchmarks include "
        "[InjecAgent](https://aclanthology.org/2024.findings-acl.624/) and "
        "[AgentDojo](https://arxiv.org/abs/2406.13352). "
        "This project contributes an inspectable teaching and audit workflow, with "
        "a small evaluation case study. It does not reproduce those benchmarks.\n\n"
        "Next steps: independent human review, more diverse matched tasks and "
        "models, and separate measures of task completion and instruction obedience. "
        "Synthetic placeholder outputs do not measure real-world harm."
    )
