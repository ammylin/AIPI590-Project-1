import json
from pathlib import Path

from src.evaluator import evaluate_response
from src.strategies import create_baseline_tests, create_swarm_tests
from src.target import MockTarget


OUTPUT_PATH = Path("results/offline_experiment.jsonl")


def run_experiment() -> None:
    """Run the baseline and swarm tests using the mock target."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    baseline_tests = create_baseline_tests()
    swarm_tests = create_swarm_tests()
    all_tests = baseline_tests + swarm_tests

    target = MockTarget()

    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        for test in all_tests:
            response = target.respond(test)
            evaluation = evaluate_response(test, response)

            result = {
                **test.to_dict(),
                "target_response": response,
                **evaluation,
                "human_label": "unreviewed",
                "human_notes": None,
            }

            output_file.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )

    print(f"Saved {len(all_tests)} results to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_experiment()