import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.metrics import (
    calculate_agreement,
    calculate_category_coverage,
    calculate_condition_summary,
)


DATA_PATH = Path("data/sample_results.jsonl")


def load_results(path: Path) -> pd.DataFrame:
    """Load JSONL evaluation results into a DataFrame."""
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return pd.DataFrame(records)


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

if not DATA_PATH.exists():
    st.error(f"Could not find sample data at `{DATA_PATH}`.")
    st.stop()

results = load_results(DATA_PATH)

st.success(f"Loaded {len(results)} evaluation results.")

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

overall_agreement = calculate_agreement(results)

st.metric(
    "Overall agreement",
    f"{overall_agreement:.1%}",
)

disagreement_data = results[
    results["automated_label"] != results["human_label"]
]

if disagreement_data.empty:
    st.success("No human/evaluator disagreements in the sample.")
else:
    st.warning(
        f"{len(disagreement_data)} result(s) contain human/evaluator disagreement."
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
    f"{selected_test['evaluator_confidence']:.0%}"
)

st.subheader("Test prompt")
st.info(selected_test["test_prompt"])

st.subheader("Expected behavior")
st.write(selected_test["expected_behavior"])

st.subheader("Target response")
st.code(selected_test["target_response"])

st.subheader("Notes")
st.write(selected_test["notes"])