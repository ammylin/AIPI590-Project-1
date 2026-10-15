"""Compare a second review pass with preserved original judgments."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.audit import LABELS, PROJECT_ROOT, REVISED_RUN, load_run, review_path_for


def compare(results: Path, original_reviews: Path, packet: Path, key_path: Path,
            review_relationship: str | None = None) -> dict:
    records = load_run(results, original_reviews)
    by_id = {r["test_id"]: r for r in records}
    if any(r["human_label"] == "unreviewed" for r in records):
        raise ValueError("Original review is incomplete.")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    if (key["source_sha256"] != hashlib.sha256(results.read_bytes()).hexdigest()
            or key["run_id"] != records[0]["run_id"]):
        raise ValueError("Review key belongs to different source observations.")
    metadata_path = packet.with_suffix(".metadata.json")
    sources = [results, original_reviews, packet, key_path]
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata["run_id"] != records[0]["run_id"]:
            raise ValueError("Review metadata belongs to a different run.")
        declared = metadata["review_relationship"]
        if review_relationship is not None and review_relationship != declared:
            raise ValueError("Review relationship conflicts with the saved declaration.")
        review_relationship = declared
        sources.append(metadata_path)
    review_relationship = review_relationship or "unspecified"
    if review_relationship not in {"same_reviewer", "independent_reviewer", "unspecified"}:
        raise ValueError("Unknown review relationship.")
    mapping = key["case_to_test"]
    if len(mapping) != len(by_id) or set(mapping.values()) != set(by_id):
        raise ValueError("Review key must cover every test exactly once.")
    with packet.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != len(mapping) or {r["case_id"] for r in rows} != set(mapping):
        raise ValueError("Second-pass packet cases are missing or duplicated.")
    reviewers = {r["reviewer_id"].strip() for r in rows}
    if len(reviewers) != 1 or "" in reviewers:
        raise ValueError("Fill a consistent nonempty reviewer_id on every row.")
    pairs = Counter()
    disagreements = []
    for row in rows:
        original = by_id[mapping[row["case_id"]]]
        for field in ("test_prompt", "expected_behavior", "target_response"):
            if row[field] != original[field]:
                raise ValueError(f"Second-pass packet observation differs: {row['case_id']} / {field}")
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
        "run_id": records[0]["run_id"], "second_pass_reviewer_id": next(iter(reviewers)),
        "review_relationship": review_relationship,
        "agreement_interpretation": (
            "Within-reviewer agreement between two passes; not inter-rater reliability."
            if review_relationship == "same_reviewer" else
            "Between-reviewer agreement under declared independence; not correctness."
            if review_relationship == "independent_reviewer" else
            "Relationship unspecified; no independent-review claim is supported."
        ),
        "n": len(rows), "exact_label_agreement": sum(n for (a, b), n in pairs.items() if a == b) / len(rows),
        "label_cross_tab": [{"original": a, "second": b, "count": n} for (a, b), n in sorted(pairs.items())],
        "disagreements": disagreements,
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "note": "No adjudication performed. Review relationship is a human declaration, not inferred from reviewer IDs. Labels and notes are preserved.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=PROJECT_ROOT / "results" / f"local_pilot_{REVISED_RUN}.jsonl")
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--packet", type=Path, default=PROJECT_ROOT / "data" / "independent_review" / f"second_review_{REVISED_RUN}.csv")
    parser.add_argument("--key", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "analysis" / "second_review_comparison.json")
    parser.add_argument("--review-relationship", choices=["same_reviewer", "independent_reviewer", "unspecified"],
                        help="Declare who completed the second pass; saved metadata takes precedence.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate only the derived comparison report.")
    args = parser.parse_args()
    report = compare(args.results, args.reviews or review_path_for(args.results),
                     args.packet, args.key or args.packet.with_suffix(".key.json"), args.review_relationship)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w" if args.overwrite else "x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(f"Saved review-pass comparison: {args.output}")
    print(report["agreement_interpretation"])


if __name__ == "__main__":
    main()
