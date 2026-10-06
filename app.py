import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.metrics import (
    calculate_agreement,
    calculate_category_coverage,
    calculate_condition_summary,
)


PROJECT_ROOT = Path(__file__).resolve().parent

DATASETS = {
    "Curated sample data": PROJECT_ROOT / "data" / "sample_results.jsonl",
    "Offline experiment": PROJECT_ROOT / "results" / "offline_experiment.jsonl",
    "Revised local-model pilot": (
    PROJECT_ROOT / "results" / "local_pilot_20261005T221442Z.jsonl"
),
}


def load_results(path: Path) -> pd.DataFrame:
    """Load JSONL evaluation results into a DataFrame."""
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    results = pd.DataFrame(records)

    # Ensure optional columns exist for all datasets.
    defaults = {
        "human_label": "unreviewed",
        "human_notes": "",
        "notes": "",
        "failure_mode": None,
        "evaluator_confidence": 0.0,
    }

    for column, default_value in defaults.items():
        if column not in results.columns:
            results[column] = default_value

    # The dashboard uses "notes" for the test explorer.
    # If only human_notes exists, preserve both columns.
    results["notes"] = results["notes"].fillna("")
    results["human_notes"] = results["human_notes"].fillna("")

    return results


st.set_page_config(
    page_title="SwarmAudit Lite",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ SwarmAudit Lite")
st.subheader("Multi-agent red-teaming evaluation")

st.write(
    """
    SwarmAudit Lite compares a generic red-team strategy with a small,
    role-diverse red-team workflow. The goal is to study coverage,
    redundancy, failure patterns, and evaluator agreement.
    """
)

available_datasets = {
    name: path for name, path in DATASETS.items() if path.exists()
}

if not available_datasets:
    st.error("No evaluation datasets were found.")
    st.stop()

selected_dataset = st.selectbox(
    "Choose an evaluation dataset",
    options=list(available_datasets.keys()),
)

data_path = available_datasets[selected_dataset]
results = load_results(data_path)
if selected_dataset == "Revised local-model pilot":
    import csv

    review_path = (
        PROJECT_ROOT / "data" / "local_review_20261005T221442Z.csv"
    )

    if not review_path.exists():
        st.error(f"Missing human-review file: {review_path}")
        st.stop()

    with review_path.open(newline="", encoding="utf-8") as file:
        reviews = list(csv.DictReader(file))

    review_by_id = {row["test_id"]: row for row in reviews}

    if len(review_by_id) != len(reviews):
        st.error("Duplicate test IDs found in the review file.")
        st.stop()

    if set(results["test_id"]) != set(review_by_id):
        st.error("The pilot results and human reviews have different test IDs.")
        st.stop()

    results["human_label"] = results["test_id"].map(
        lambda test_id: review_by_id[test_id]["human_label"].strip()
    )
    results["human_notes"] = results["test_id"].map(
        lambda test_id: review_by_id[test_id]["human_notes"].strip()
    )

    st.success(f"Loaded {len(results)} real-model pilot responses.")
    st.caption(
        "Target: qwen2.5:3b running locally. Labels are from one human "
        "reviewer; no automated evaluator was applied to this pilot."
    )

    st.header("Baseline vs. specialized strategies")

    summary = []
    for condition in ("baseline", "swarm"):
        group = results[results["condition"] == condition]
        valid = group[group["human_label"] != "invalid"]

        summary.append({
            "Condition": condition,
            "Tests run": len(group),
            "Valid tests": len(valid),
            "Human-labeled failures": (
                valid["human_label"] == "failure"
            ).sum(),
            "Passes": (valid["human_label"] == "pass").sum(),
            "Invalid tests": (
                group["human_label"] == "invalid"
            ).sum(),
        })

    st.dataframe(pd.DataFrame(summary), hide_index=True)

    st.warning(
        "This is a small, hand-authored pilot—not evidence that an "
        "autonomous swarm outperforms a baseline. Category counts were "
        "matched by design, so category coverage is not an outcome here."
    )

    st.header("Explore a response")

    selected_id = st.selectbox(
        "Select a test",
        results["test_id"].tolist(),
    )
    row = results.loc[results["test_id"] == selected_id].iloc[0]

    st.write(
        f"**Condition:** {row['condition']} · "
        f"**Strategy:** {row['strategy']} · "
        f"**Category:** {row['category']}"
    )
    st.write(f"**Human label:** `{row['human_label']}`")
    st.subheader("Legitimate task and test prompt")
    st.info(row["test_prompt"])
    st.subheader("Expected behavior")
    st.write(row["expected_behavior"])
    st.subheader("Model response")
    st.code(row["target_response"])
    st.subheader("Human-review rationale")
    st.write(row["human_notes"])

    # The existing dashboard sections expect automated_label. They apply
    # to the mock datasets, not to this human-reviewed local pilot.
    st.stop()

st.success(
    f"Loaded {len(results)} results from `{data_path.relative_to(PROJECT_ROOT)}`."
)

st.divider()

# Summary metrics
total_tests = len(results)
baseline_tests = len(results[results["condition"] == "baseline"])
swarm_tests = len(results[results["condition"] == "swarm"])
categories_covered = results["category"].nunique()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total tests", total_tests)

with col2:
    st.metric("Baseline tests", baseline_tests)

with col3:
    st.metric("Swarm tests", swarm_tests)

with col4:
    st.metric("Categories covered", categories_covered)

st.divider()

# Comparison by condition
st.header("Comparison by condition")

condition_summary = calculate_condition_summary(results)

display_summary = condition_summary.copy()

display_summary["human_evaluator_agreement"] = (
    display_summary["human_evaluator_agreement"] * 100
).round(1).astype(str) + "%"

st.dataframe(display_summary, use_container_width=True)

st.subheader("Automated labels by condition")

label_counts = (
    results.groupby(["condition", "automated_label"])
    .size()
    .unstack(fill_value=0)
)

st.bar_chart(label_counts)

# Human versus automated evaluation
st.header("Human versus automated evaluation")

reviewed_results = results[results["human_label"] != "unreviewed"]

if reviewed_results.empty:
    st.info(
        "No human-reviewed labels are present in this dataset yet. "
        "The agreement metric will appear after human review."
    )
else:
    overall_agreement = calculate_agreement(reviewed_results)

    st.metric(
        "Human/evaluator agreement",
        f"{overall_agreement:.1%}",
    )

    disagreement_data = reviewed_results[
        reviewed_results["automated_label"]
        != reviewed_results["human_label"]
    ]

    if disagreement_data.empty:
        st.success("No human/evaluator disagreements in the reviewed sample.")
    else:
        st.warning(
            f"{len(disagreement_data)} reviewed result(s) contain disagreement."
        )

        st.dataframe(
            disagreement_data[
                [
                    "test_id",
                    "condition",
                    "strategy",
                    "category",
                    "automated_label",
                    "human_label",
                    "notes",
                    "human_notes",
                ]
            ],
            use_container_width=True,
        )

# Category coverage
st.header("Category coverage")

coverage = calculate_category_coverage(results)

st.dataframe(coverage, use_container_width=True)

coverage_chart = (
    coverage
    .pivot(
        index="category",
        columns="condition",
        values="test_count",
    )
    .fillna(0)
)

st.bar_chart(coverage_chart)

# Individual test explorer
st.header("Test explorer")

selected_test_id = st.selectbox(
    "Select a test",
    options=results["test_id"].tolist(),
)

selected_test = results[
    results["test_id"] == selected_test_id
].iloc[0]

st.write(f"**Condition:** {selected_test['condition']}")
st.write(f"**Strategy:** {selected_test['strategy']}")
st.write(f"**Category:** {selected_test['category']}")
st.write(f"**Automated label:** `{selected_test['automated_label']}`")
st.write(f"**Human label:** `{selected_test['human_label']}`")
st.write(
    f"**Evaluator confidence:** "
    f"{float(selected_test['evaluator_confidence']):.0%}"
)

st.subheader("Test prompt")
st.info(selected_test["test_prompt"])

st.subheader("Expected behavior")
st.write(selected_test["expected_behavior"])

st.subheader("Target response")
st.code(selected_test["target_response"])

st.subheader("Evaluator rationale")
st.write(selected_test.get("evaluator_rationale", ""))

st.subheader("Notes")
st.write(selected_test["notes"])