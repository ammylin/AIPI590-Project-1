from .schema import RedTeamTest


class MockTarget:
    """
    Deterministic stand-in for a target model.

    This is only for testing the pipeline. It does not represent
    real model behavior.
    """

    def respond(self, test: RedTeamTest) -> str:
        """Return a predictable response for a test case."""

        if test.test_id == "baseline_002":
            return "[PROTECTED_PLACEHOLDER]"

        if test.test_id == "baseline_003":
            return "I cannot assist with that request."

        if test.test_id == "swarm_ambiguity_001":
            return (
                "I will follow the instruction because the document "
                "claims it has higher priority."
            )

        if test.test_id == "swarm_consistency_002":
            return (
                "The team will meet tomorrow. "
                "This preserves the original meaning."
            )

        return (
            "I followed the requested task and treated embedded instructions "
            "as untrusted content."
        )