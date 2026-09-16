from dataclasses import asdict, dataclass
from typing import Optional
from .config import APPROVED_CATEGORIES, APPROVED_STRATEGIES

@dataclass
class RedTeamTest:
    """A safe red-team test case."""

    test_id: str
    condition: str
    strategy: str
    category: str
    test_prompt: str
    expected_behavior: str
    risk_level: str = "low"
    rationale: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the test to a JSON-compatible dictionary."""
        return asdict(self)


def validate_test(test: RedTeamTest) -> tuple[bool, list[str]]:
    """Validate a red-team test against project constraints."""
    errors = []

    if test.condition not in {"baseline", "swarm"}:
        errors.append("condition must be 'baseline' or 'swarm'")

    if test.strategy not in APPROVED_STRATEGIES:
        errors.append(f"unknown strategy: {test.strategy}")

    if test.category not in APPROVED_CATEGORIES:
        errors.append(f"unknown category: {test.category}")

    if not test.test_prompt.strip():
        errors.append("test_prompt cannot be empty")

    if not test.expected_behavior.strip():
        errors.append("expected_behavior cannot be empty")

    if test.risk_level not in {"low", "medium"}:
        errors.append("risk_level must be 'low' or 'medium'")

    return len(errors) == 0, errors