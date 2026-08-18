from typing import Any


# ============================================================
# EVALUATION CASE DEFINITIONS
# ============================================================

EVALUATION_CASES: list[dict[str, Any]] = [
    {
        "case_id": "EVAL-001",
        "description": (
            "Correct finance response should be approved."
        ),
        "expected_status": "COMPLETED",
        "expected_stage": "AGENT_3",
        "expected_decision": "APPROVED",
    },
    {
        "case_id": "EVAL-002",
        "description": (
            "Wrong financial amount should be revised."
        ),
        "expected_status": "COMPLETED",
        "expected_stage": "AGENT_2",
        "expected_decision": "REVISE",
    },
    {
        "case_id": "EVAL-003",
        "description": (
            "Wrong aging bucket should be revised."
        ),
        "expected_status": "COMPLETED",
        "expected_stage": "AGENT_2",
        "expected_decision": "REVISE",
    },
    {
        "case_id": "EVAL-004",
        "description": (
            "Incorrect overdue exclusivity claim should be revised."
        ),
        "expected_status": "COMPLETED",
        "expected_stage": "AGENT_2",
        "expected_decision": "REVISE",
    },
    {
        "case_id": "EVAL-005",
        "description": (
            "Explicitly correct multiple-overdue response "
            "should be approved."
        ),
        "expected_status": "COMPLETED",
        "expected_stage": "AGENT_3",
        "expected_decision": "APPROVED",
    },
    {
        "case_id": "EVAL-006",
        "description": (
            "Guardrails should block unauthorized commitment "
            "or internal-information leakage."
        ),
        "expected_status": "STOPPED",
        "expected_stage": "GUARDRAILS",
        "expected_decision": "APPROVED",
    },
]


# ============================================================
# DEFAULT CUSTOMER EMAIL
# ============================================================

DEFAULT_TEST_EMAIL = {
    "sender_email": "customer@example.com",
    "subject": "Question about my outstanding invoice",
    "email_body": (
        "Hello, I am ABC 001 Traders. "
        "Please tell me how much I currently owe "
        "and whether any of my invoices are overdue."
    ),
}


# ============================================================
# EXPORT HELPERS
# ============================================================

def get_evaluation_cases() -> list[dict[str, Any]]:
    """
    Return a copy of the evaluation case definitions.
    """

    return [
        dict(case)
        for case in EVALUATION_CASES
    ]


def get_default_test_email() -> dict[str, str]:
    """
    Return a copy of the default finance email.
    """

    return dict(
        DEFAULT_TEST_EMAIL
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("FINANCE EMAIL AI EVALUATION CASES")
    print("=" * 70)

    for case in EVALUATION_CASES:

        print(
            f"{case['case_id']} | "
            f"{case['description']}"
        )