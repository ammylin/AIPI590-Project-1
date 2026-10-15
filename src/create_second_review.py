"""Create an unlabeled, shuffled packet for a new human review pass.

The packet hides original labels, condition names, and strategy names. The
separate key links case IDs to preserved observations. No judgments are made.
"""

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

from src.audit import PROJECT_ROOT, REVISED_RUN, load_run


FIELDS = ["case_id", "test_prompt", "expected_behavior", "target_response",
          "reviewer_id", "human_label", "human_notes"]


def create_packet(results: Path, output_dir: Path) -> tuple[Path, Path]:
    records = load_run(results)
    random.Random(42).shuffle(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    packet = output_dir / f"second_review_{records[0]['run_id']}.csv"
    key = packet.with_suffix(".key.json")
    if packet.exists() or key.exists():
        raise FileExistsError("Packet/key already exists; refusing to overwrite human work.")
    mapping = {}
    with packet.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for index, record in enumerate(records, 1):
            case_id = f"case_{index:03d}"
            mapping[case_id] = record["test_id"]
            writer.writerow({
                "case_id": case_id,
                **{field: record[field] for field in ("test_prompt", "expected_behavior", "target_response")},
                "reviewer_id": "", "human_label": "", "human_notes": "",
            })
    key.write_text(json.dumps({
        "run_id": records[0]["run_id"],
        "source_sha256": hashlib.sha256(results.read_bytes()).hexdigest(),
        "case_to_test": mapping,
    }, indent=2) + "\n", encoding="utf-8")
    return packet, key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=PROJECT_ROOT / "results" / f"local_pilot_{REVISED_RUN}.jsonl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "independent_review")
    args = parser.parse_args()
    packet, key = create_packet(args.results, args.output_dir)
    print(f"Unfilled human-review packet: {packet}")
    print(f"Linkage key (withhold until review is complete): {key}")
    print("Status: unfilled. Record whether the completed pass uses the same reviewer or an independent reviewer; IDs alone do not establish independence.")


if __name__ == "__main__":
    main()
