import csv
import json
import sys
from pathlib import Path


FIELDS = [
    "run_id",
    "pair_id",
    "role",
    "test_id",
    "test_prompt",
    "expected_behavior",
    "target_response",
    "human_label",
    "human_notes",
]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m src.create_pair_review "
            "results/paired_probes/paired_probe_<run_id>.jsonl"
        )

    input_path = Path(sys.argv[1])
    with input_path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]

    if len(records) != 2 or {r["role"] for r in records} != {
        "control", "injection"
    }:
        raise ValueError("Expected one control and one injection record.")

    run_id = records[0]["run_id"]
    output_path = Path("data") / f"pair_review_{run_id}.csv"

    # "x" prevents overwriting an existing review.
    with output_path.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({
                **{field: record.get(field, "") for field in FIELDS},
                "human_label": "",
                "human_notes": "",
            })

    print(f"Created {output_path}")


if __name__ == "__main__":
    main()