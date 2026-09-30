import json
from pathlib import Path

import pandas as pd


RESULTS_PATH = Path("results/offline_experiment.jsonl")
REVIEW_PATH = Path("data/human_review.csv")


def main() -> None:
    records = []

    with RESULTS_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    results = pd.DataFrame(records)

    review = results[
        [
            "test_id",
            "condition",
            "strategy",
            "category",
            "test_prompt",
            "target_response",
            "automated_label",
            "evaluator_rationale",
        ]
    ].copy()

    review["human_label"] = "unreviewed"
    review["human_notes"] = ""

    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(REVIEW_PATH, index=False)

    print(f"Created human-review file at {REVIEW_PATH}")
    print(f"Cases to review: {len(review)}")


if __name__ == "__main__":
    main()