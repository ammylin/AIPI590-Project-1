"""Compare a completed independent packet with preserved original judgments."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.audit import LABELS, PROJECT_ROOT, REVISED_RUN, load_run, review_path_for


def compare(results: Path, original_reviews: Path, packet: Path, key_path: Path) -> dict:
    records = load_run(results, original_reviews)
    by_id = {r["test_id"]: r for r in records}
    if any(r["human_label"] == "unreviewed" for r in records):
        raise ValueError("Original review is incomplete.")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    if (key["source_sha256"] != hashlib.sha256(results.read_bytes()).hexdigest()
            or key["run_id"] != records[0]["run_id"]):
        raise ValueError("Review key belongs to different source observations.")
    mapping = key["case_to_test"]
    if len(mapping) != len(by_id) or set(mapping.values()) != set(by_id):
        raise ValueError("Review key must cover every test exactly once.")
    with packet.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != len(mapping) or {r["case_id"] for r in rows} != set(mapping):
        raise ValueError("Independent packet cases are missing or duplicated.")
    reviewers = {r["reviewer_id"].strip() for r in rows}
    if len(reviewers) != 1 or "" in reviewers:
        raise ValueError("Fill a consistent nonempty reviewer_id on every row.")
    pairs = Counter()
    disagreements = []
    for row in rows:
        original = by_id[mapping[row["case_id"]]]
        for field in ("test_prompt", "expected_behavior", "target_response"):
            if row[field] != original[field]:
                raise ValueError(f"Independent packet observation differs: {row['case_id']} / {field}")
        label = row["human_label"].strip()
        if label not in LABELS or not row["human_notes"].strip():
            raise ValueError(f"Complete the human label and evidence notes for {row['case_id']}.")
        pairs[(original["human_label"], label)] += 1
        # Agreement describes consistency, not correctness or adjudication.
        if original["human_label"] != label:
            disagreements.append({
                "test_id": original["test_id"], "original_label": original["human_label"],
                "second_label": label, "original_notes": original["human_notes"],
                "second_notes": row["human_notes"],
            })
    return {
        "run_id": records[0]["run_id"], "second_reviewer": next(iter(reviewers)),
        "n": len(rows), "exact_label_agreement": sum(n for (a, b), n in pairs.items() if a == b) / len(rows),
        "label_cross_tab": [{"original": a, "second": b, "count": n} for (a, b), n in sorted(pairs.items())],
        "disagreements": disagreements,
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (results, original_reviews, packet, key_path)},
        "note": "No adjudication performed; reviewer independence is procedural and cannot be verified by code.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=PROJECT_ROOT / "results" / f"local_pilot_{REVISED_RUN}.jsonl")
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--packet", type=Path, default=PROJECT_ROOT / "data" / "independent_review" / f"second_review_{REVISED_RUN}.csv")
    parser.add_argument("--key", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "analysis" / "second_review_comparison.json")
    args = parser.parse_args()
    report = compare(args.results, args.reviews or review_path_for(args.results),
                     args.packet, args.key or args.packet.with_suffix(".key.json"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(f"Saved independent-review comparison: {args.output}")


if __name__ == "__main__":
    main()
