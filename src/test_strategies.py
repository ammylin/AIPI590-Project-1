from src.schema import validate_test
from src.strategies import create_baseline_tests, create_swarm_tests


def main() -> None:
    baseline_tests = create_baseline_tests()
    swarm_tests = create_swarm_tests()

    all_tests = baseline_tests + swarm_tests

    print(f"Baseline tests: {len(baseline_tests)}")
    print(f"Swarm tests: {len(swarm_tests)}")
    print(f"Total tests: {len(all_tests)}")

    for test in all_tests:
        is_valid, errors = validate_test(test)

        print(
            f"{test.test_id}: "
            f"strategy={test.strategy}, "
            f"category={test.category}, "
            f"valid={is_valid}"
        )

        if errors:
            print(f"  Errors: {errors}")

    assert all(validate_test(test)[0] for test in all_tests)

    print("All generated tests are valid.")


if __name__ == "__main__":
    main()