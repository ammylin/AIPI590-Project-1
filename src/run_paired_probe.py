import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.local_target import LocalTarget, SYSTEM_PROMPT
from src.paired_probe import build_pair


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    control, injection = build_pair("announcement")
    target = LocalTarget()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_dir = PROJECT_ROOT / "results" / "paired_probes"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"paired_probe_{run_id}.jsonl"

    print(f"Target: {target.model}")
    print(f"Saving to: {output_path}")

    with output_path.open("x", encoding="utf-8") as file:
        for role, test in [("control", control), ("injection", injection)]:
            print(f"\nRunning {role}...", flush=True)
            start = time.perf_counter()
            response = target.respond(test)

            record = {
                "run_id": run_id,
                "pair_id": "garden_tour_announcement",
                "role": role,
                **test.to_dict(),
                "target_type": "local_ollama",
                "target_model": target.model,
                "system_prompt": SYSTEM_PROMPT,
                "temperature": 0,
                "seed": 42,
                "num_predict": 128,
                "target_response": response,
                "runtime_seconds": round(time.perf_counter() - start, 2),
            }

            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()
            print(f"Response: {response}")

    print(f"\nSaved both responses to {output_path}")
    print("No labels assigned; review the responses before interpreting them.")


if __name__ == "__main__":
    main()