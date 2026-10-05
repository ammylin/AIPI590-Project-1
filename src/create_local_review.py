import csv
import json
import sys
from pathlib import Path


FIELDS = [
    "run_id",
    "test_id",
    "condition",
    "strategy",
    "category",
    "test_prompt",
    "expected_behavior",
    "target_response",
    "human_label",
    "human_notes",
]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m src.create_local_review "
            "results/local_pilot_<run_id>.jsonl"
        )

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        raise SystemExit(f"Pilot file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]

    if not records:
        raise SystemExit("Pilot file is empty.")

    run_ids = {record["run_id"] for record in records}
    if len(run_ids) != 1:
        raise SystemExit("Expected exactly one run_id in the pilot file.")

    if any(record.get("error") or record.get("target_response") is None for record in records):
        raise SystemExit("Some tests had model errors; inspect the pilot before review.")

    run_id = run_ids.pop()
    output_path = Path("data") / f"local_review_{run_id}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # "x" prevents accidentally overwriting completed human reviews.
    with output_path.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()

        for record in records:
            writer.writerow({
                **{field: record.get(field, "") for field in FIELDS},
                "human_label": "",
                "human_notes": "",
            })

    print(f"Created {output_path} with {len(records)} cases.")
    print("The mock-review CSV was not changed.")


if __name__ == "__main__":
    main()