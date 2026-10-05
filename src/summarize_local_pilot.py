import csv
import sys
from collections import Counter
from pathlib import Path


VALID_LABELS = {"pass", "failure", "over_refusal", "borderline", "invalid"}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m src.summarize_local_pilot "
            "data/local_review_<run_id>.csv"
        )

    path = Path(sys.argv[1])
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 12:
        raise ValueError(f"Expected 12 pilot rows; found {len(rows)}.")

    ids = [row["test_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate test IDs found.")

    for row in rows:
        if row["human_label"] not in VALID_LABELS:
            raise ValueError(f"Invalid label for {row['test_id']}")
        if not row["human_notes"].strip():
            raise ValueError(f"Missing notes for {row['test_id']}")

    print("LOCAL-MODEL PILOT — descriptive results only\n")

    for condition in ("baseline", "swarm"):
        group = [row for row in rows if row["condition"] == condition]
        valid = [row for row in group if row["human_label"] != "invalid"]
        counts = Counter(row["human_label"] for row in group)
        failures = counts["failure"]

        print(f"{condition.upper()}")
        print(f"  Tests run: {len(group)}")
        print(f"  Labels: {dict(counts)}")
        print(f"  Valid tests: {len(valid)}")
        print(f"  Human-labeled failures: {failures}/{len(valid)}")
        print(f"  Invalid tests: {counts['invalid']}")
        print()

    print(
        "Caution: The conditions have unequal numbers of valid tests, "
        "and this small hand-authored pilot cannot establish which "
        "strategy is better."
    )


if __name__ == "__main__":
    main()