import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.local_target import LocalTarget, SYSTEM_PROMPT
from src.schema import validate_test
from src.strategies import create_baseline_tests, create_swarm_tests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "results"


def main() -> None:
    tests = create_baseline_tests() + create_swarm_tests()

    for test in tests:
        valid, errors = validate_test(test)
        if not valid:
            raise ValueError(f"{test.test_id}: {errors}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    # A timestamped filename preserves earlier runs instead of overwriting them.
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = OUTPUT_DIR / f"local_pilot_{run_id}.jsonl"

    target = LocalTarget()
    print(f"Running {len(tests)} tests against {target.model}")
    print(f"Saving raw responses to {output_path}")

    with output_path.open("x", encoding="utf-8") as output_file:
        for index, test in enumerate(tests, start=1):
            print(f"[{index}/{len(tests)}] {test.test_id}...", flush=True)
            start = time.perf_counter()

            try:
                response = target.respond(test)
                error = None
            except Exception as exc:
                response = None
                error = str(exc)

            record = {
                **test.to_dict(),
                "run_id": run_id,
                "target_type": "local_ollama",
                "target_model": target.model,
                "system_prompt": SYSTEM_PROMPT,
                "temperature": 0,
                "seed": 42,
                "num_predict": 128,
                "target_response": response,
                "error": error,
                "runtime_seconds": round(time.perf_counter() - start, 2),
            }

            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            output_file.flush()

            if error:
                print(f"  Error: {error}")
            else:
                print(f"  Response: {response[:120]!r}")

    print(f"\nSaved pilot results: {output_path}")


if __name__ == "__main__":
    main()