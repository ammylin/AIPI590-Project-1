"""Reproduce the retrospective evaluator audit without calling a model."""

import argparse
import hashlib
import json
from pathlib import Path

from src.audit import PROJECT_ROOT, REVISED_RUN, condition_summary, detector_audit, load_run, review_path_for


def build_report(results: Path, reviews: Path) -> dict:
    records = load_run(results, reviews)
    if any(row["human_label"] == "unreviewed" for row in records):
        raise ValueError("Complete human reviews before generating an audit report.")
    return {
        "analysis": "Retrospective detector comparison; no new model calls or human reviews",
        "run_id": records[0]["run_id"],
        "source_sha256": {
            results.name: hashlib.sha256(results.read_bytes()).hexdigest(),
            reviews.name: hashlib.sha256(reviews.read_bytes()).hexdigest(),
        },
        "original_judgments": {
            "conditions": condition_summary(records), "detectors": detector_audit(records),
        },
        "sensitivity_disputed_as_borderline": {
            "note": "Hypothetical relabeling of swarm_ambiguity_001, not an independent review or adjudication",
            "conditions": condition_summary(records, True), "detectors": detector_audit(records, True),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=PROJECT_ROOT / "results" / f"local_pilot_{REVISED_RUN}.jsonl")
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "analysis" / "reviewed_pilot_audit.json")
    args = parser.parse_args()
    report = build_report(args.results, args.reviews or review_path_for(args.results))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved reproducible analysis: {args.output}")
    for scenario in ("original_judgments", "sensitivity_disputed_as_borderline"):
        print(scenario)
        for row in report[scenario]["detectors"]["summary"]:
            print(row)


if __name__ == "__main__":
    main()
