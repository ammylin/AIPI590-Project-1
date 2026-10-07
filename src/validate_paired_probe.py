import json
import sys
from pathlib import Path

from src.structured_generator import EMBEDDED_INSTRUCTION


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m src.validate_paired_probe "
            "results/paired_probes/paired_probe_<run_id>.jsonl"
        )

    path = Path(sys.argv[1])
    with path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]

    if len(records) != 2:
        raise ValueError(f"Expected 2 records; found {len(records)}")

    by_role = {record["role"]: record for record in records}
    if set(by_role) != {"control", "injection"}:
        raise ValueError("Expected one control and one injection record")

    control = by_role["control"]
    injection = by_role["injection"]

    for field in ("run_id", "pair_id", "target_model", "system_prompt",
                  "temperature", "seed", "num_predict"):
        if control[field] != injection[field]:
            raise ValueError(f"Pair differs on {field}")

    if injection["test_prompt"].count(EMBEDDED_INSTRUCTION) != 1:
        raise ValueError("Injection prompt must contain the instruction once")

    if (
        injection["test_prompt"].replace(EMBEDDED_INSTRUCTION, "")
        != control["test_prompt"]
    ):
        raise ValueError("Prompts differ by more than the embedded instruction")

    if not all(record.get("target_response") for record in records):
        raise ValueError("A target response is missing")

    print("Saved pair is valid.")
    print("Control response:", control["target_response"])
    print("Injection response:", injection["target_response"])
    print("No outcome label has been assigned.")


if __name__ == "__main__":
    main()