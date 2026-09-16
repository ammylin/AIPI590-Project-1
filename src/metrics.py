import pandas as pd


def calculate_agreement(results: pd.DataFrame) -> float:
    """Calculate agreement between automated and human labels."""
    if results.empty:
        return 0.0

    return (
        results["automated_label"] == results["human_label"]
    ).mean()


def calculate_condition_summary(results: pd.DataFrame) -> pd.DataFrame:
    """Create summary metrics for each experimental condition."""
    summaries = []

    for condition, group in results.groupby("condition"):
        summaries.append(
            {
                "condition": condition,
                "tests": len(group),
                "categories_covered": group["category"].nunique(),
                "failures": (group["automated_label"] == "failure").sum(),
                "over_refusals": (
                    group["automated_label"] == "over_refusal"
                ).sum(),
                "borderline_cases": (
                    group["human_label"] == "borderline"
                ).sum(),
                "human_evaluator_agreement": (
                    group["automated_label"] == group["human_label"]
                ).mean(),
            }
        )

    return pd.DataFrame(summaries)


def calculate_category_coverage(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Count tests in each category for each condition."""
    return (
        results.groupby(["condition", "category"])
        .size()
        .reset_index(name="test_count")
    )