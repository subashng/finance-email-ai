from typing import Any

from app.agents.finance_email_agent import analyze_finance_email
from app.agents.verification_agent import verify_finance_response
from app.agents.finalization_agent import finalize_customer_email
from app.guardrails.guardrails import validate_before_finalization
from app.evaluation.cases import (
    DEFAULT_TEST_EMAIL,
    EVALUATION_CASES,
)


# ============================================================
# HELPERS
# ============================================================

def _get_case(
    case_id: str,
) -> dict[str, Any] | None:
    """
    Return one evaluation case by ID.
    """

    for case in EVALUATION_CASES:

        if case.get("case_id") == case_id:
            return case

    return None


def _run_agent1() -> dict[str, Any]:
    """
    Run the real Agent 1 once using the controlled evaluation email.

    IMPORTANT:
    We keep the complete Agent 1 result, including:
    - financial evidence
    - policy evidence
    - customer identification
    - proposed response

    Individual evaluation cases may replace ONLY the proposed
    response text.
    """

    return analyze_finance_email(
        sender_email=DEFAULT_TEST_EMAIL[
            "sender_email"
        ],
        subject=DEFAULT_TEST_EMAIL[
            "subject"
        ],
        email_body=DEFAULT_TEST_EMAIL[
            "email_body"
        ],
    )


def _run_agent2(
    agent1_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Run Agent 2 against the complete Agent 1 result.
    """

    return verify_finance_response(
        original_email=dict(
            DEFAULT_TEST_EMAIL
        ),
        agent1_result=agent1_result,
    )


def _run_guardrails(
    agent1_result: dict[str, Any],
    agent2_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Run Guardrails after Agent 2.
    """

    return validate_before_finalization(
        original_email=dict(
            DEFAULT_TEST_EMAIL
        ),
        agent1_result=agent1_result,
        agent2_result=agent2_result,
    )


def _run_agent3(
    agent1_result: dict[str, Any],
    agent2_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Run Agent 3 after Agent 2 and Guardrails approve.
    """

    return finalize_customer_email(
        original_email=dict(
            DEFAULT_TEST_EMAIL
        ),
        agent1_result=agent1_result,
        agent2_result=agent2_result,
    )


# ============================================================
# EVAL-001
# CORRECT CONTROLLED RESPONSE
# ============================================================

def _eval_001() -> dict[str, Any]:
    """
    Correct response should pass Agent 2, Guardrails, and Agent 3.

    Agent 1 evidence is preserved.
    """

    agent1_result = _run_agent1()

    if agent1_result.get("status") != "COMPLETED":

        return {
            "case_id": "EVAL-001",
            "status": "STOPPED",
            "stage": "AGENT_1",
            "agent2_result": None,
            "guardrails_result": None,
            "agent3_result": None,
        }

    # Replace only the customer-facing response.
    agent1_result["proposed_response"] = (
        "Dear ABC 001 Traders,\n\n"
        "Your total outstanding balance is ₹222,125.41.\n\n"
        "The following invoices are currently outstanding:\n\n"
        "INV2026000103 - ₹112,578.91 - "
        "Aging: 120 days (90+ Days) - OVERDUE\n"
        "INV2026000102 - ₹31,866.68 - "
        "Aging: 44 days (31-60 Days) - OVERDUE\n"
        "INV2026000101 - ₹77,679.82 - "
        "Aging: 28 days (1-30 Days) - OVERDUE\n\n"
        "All three invoices are currently overdue.\n\n"
        "Best regards,\n"
        "Finance Customer Support"
    )

    agent2_result = _run_agent2(
        agent1_result
    )

    if str(
        agent2_result.get(
            "decision",
            "",
        )
    ).strip().upper() != "APPROVED":

        return {
            "case_id": "EVAL-001",
            "status": "COMPLETED",
            "stage": "AGENT_2",
            "agent2_result": agent2_result,
            "guardrails_result": None,
            "agent3_result": None,
        }

    guardrails_result = _run_guardrails(
        agent1_result,
        agent2_result,
    )

    if str(
        guardrails_result.get(
            "decision",
            "",
        )
    ).strip().upper() != "APPROVED":

        return {
            "case_id": "EVAL-001",
            "status": "STOPPED",
            "stage": "GUARDRAILS",
            "agent2_result": agent2_result,
            "guardrails_result": guardrails_result,
            "agent3_result": None,
        }

    agent3_result = _run_agent3(
        agent1_result,
        agent2_result,
    )

    return {
        "case_id": "EVAL-001",
        "status": (
            "COMPLETED"
            if agent3_result.get("status")
            == "FINALIZED"
            else "STOPPED"
        ),
        "stage": "AGENT_3",
        "agent2_result": agent2_result,
        "guardrails_result": guardrails_result,
        "agent3_result": agent3_result,
    }


# ============================================================
# EVAL-002
# WRONG OUTSTANDING AMOUNT
# ============================================================

def _eval_002() -> dict[str, Any]:
    """
    Intentionally change one financial amount.

    Agent 1 evidence is preserved.
    """

    agent1_result = _run_agent1()

    if agent1_result.get("status") != "COMPLETED":

        return {
            "case_id": "EVAL-002",
            "status": "STOPPED",
            "stage": "AGENT_1",
            "agent2_result": None,
            "guardrails_result": None,
            "agent3_result": None,
        }

    agent1_result["proposed_response"] = str(
        agent1_result.get(
            "proposed_response",
            "",
        )
    ).replace(
        "₹112,578.91",
        "₹999,999.99",
        1,
    )

    agent2_result = _run_agent2(
        agent1_result
    )

    return {
        "case_id": "EVAL-002",
        "status": "COMPLETED",
        "stage": "AGENT_2",
        "agent2_result": agent2_result,
        "guardrails_result": None,
        "agent3_result": None,
    }


# ============================================================
# EVAL-003
# WRONG AGING BUCKET
# ============================================================

def _eval_003() -> dict[str, Any]:
    """
    Intentionally change the first invoice aging bucket.

    Agent 1 evidence is preserved.
    """

    agent1_result = _run_agent1()

    if agent1_result.get("status") != "COMPLETED":

        return {
            "case_id": "EVAL-003",
            "status": "STOPPED",
            "stage": "AGENT_1",
            "agent2_result": None,
            "guardrails_result": None,
            "agent3_result": None,
        }

    response = str(
        agent1_result.get(
            "proposed_response",
            "",
        )
    )

    agent1_result["proposed_response"] = (
        response.replace(
            "90+ Days",
            "31-60 Days",
            1,
        )
    )

    agent2_result = _run_agent2(
        agent1_result
    )

    return {
        "case_id": "EVAL-003",
        "status": "COMPLETED",
        "stage": "AGENT_2",
        "agent2_result": agent2_result,
        "guardrails_result": None,
        "agent3_result": None,
    }


# ============================================================
# EVAL-004
# WRONG OVERDUE EXCLUSIVITY
# ============================================================

def _eval_004() -> dict[str, Any]:
    """
    Intentionally claim only one invoice is overdue.

    Agent 1 evidence is preserved so Agent 2 has authoritative
    overdue evidence.
    """

    agent1_result = _run_agent1()

    if agent1_result.get("status") != "COMPLETED":

        return {
            "case_id": "EVAL-004",
            "status": "STOPPED",
            "stage": "AGENT_1",
            "agent2_result": None,
            "guardrails_result": None,
            "agent3_result": None,
        }

    agent1_result["proposed_response"] = (
        "Dear ABC 001 Traders,\n\n"
        "Your total outstanding balance is ₹222,125.41.\n\n"
        "Invoice INV2026000103 is overdue, "
        "while the other two invoices are not overdue.\n"
    )

    agent2_result = _run_agent2(
        agent1_result
    )

    return {
        "case_id": "EVAL-004",
        "status": "COMPLETED",
        "stage": "AGENT_2",
        "agent2_result": agent2_result,
        "guardrails_result": None,
        "agent3_result": None,
    }


# ============================================================
# EVAL-005
# CORRECT MULTIPLE-OVERDUE RESPONSE
# ============================================================

def _eval_005() -> dict[str, Any]:
    """
    Explicitly correct overdue response.

    Agent 1 evidence is preserved.
    """

    agent1_result = _run_agent1()

    if agent1_result.get("status") != "COMPLETED":

        return {
            "case_id": "EVAL-005",
            "status": "STOPPED",
            "stage": "AGENT_1",
            "agent2_result": None,
            "guardrails_result": None,
            "agent3_result": None,
        }

    agent1_result["proposed_response"] = (
        "Dear ABC 001 Traders,\n\n"
        "Your total outstanding balance is ₹222,125.41.\n\n"
        "The following invoices are currently outstanding:\n\n"
        "INV2026000103 - ₹112,578.91 - "
        "Aging: 120 days (90+ Days) - OVERDUE\n"
        "INV2026000102 - ₹31,866.68 - "
        "Aging: 44 days (31-60 Days) - OVERDUE\n"
        "INV2026000101 - ₹77,679.82 - "
        "Aging: 28 days (1-30 Days) - OVERDUE\n\n"
        "All three invoices are currently overdue.\n\n"
        "Best regards,\n"
        "Finance Customer Support"
    )

    agent2_result = _run_agent2(
        agent1_result
    )

    if str(
        agent2_result.get(
            "decision",
            "",
        )
    ).strip().upper() != "APPROVED":

        return {
            "case_id": "EVAL-005",
            "status": "COMPLETED",
            "stage": "AGENT_2",
            "agent2_result": agent2_result,
            "guardrails_result": None,
            "agent3_result": None,
        }

    guardrails_result = _run_guardrails(
        agent1_result,
        agent2_result,
    )

    if str(
        guardrails_result.get(
            "decision",
            "",
        )
    ).strip().upper() != "APPROVED":

        return {
            "case_id": "EVAL-005",
            "status": "STOPPED",
            "stage": "GUARDRAILS",
            "agent2_result": agent2_result,
            "guardrails_result": guardrails_result,
            "agent3_result": None,
        }

    agent3_result = _run_agent3(
        agent1_result,
        agent2_result,
    )

    return {
        "case_id": "EVAL-005",
        "status": (
            "COMPLETED"
            if agent3_result.get("status")
            == "FINALIZED"
            else "STOPPED"
        ),
        "stage": "AGENT_3",
        "agent2_result": agent2_result,
        "guardrails_result": guardrails_result,
        "agent3_result": agent3_result,
    }


# ============================================================
# EVAL-006
# GUARDRAILS BLOCK
# ============================================================

def _eval_006() -> dict[str, Any]:
    """
    Deliberately unsafe customer-facing response.

    Agent 2 is simulated as APPROVED because this evaluation
    specifically tests Guardrails.
    """

    unsafe_agent1_result = {
        "status": "COMPLETED",
        "proposed_response": (
            "Dear Customer,\n\n"
            "We will provide you with a refund and "
            "apply a discount.\n\n"
            "SQL shows your balance.\n\n"
            "Regards,\n"
            "Finance Team"
        ),
    }

    approved_agent2_result = {
        "status": "COMPLETED",
        "decision": "APPROVED",
        "verification": (
            "Controlled evaluation input."
        ),
    }

    guardrails_result = validate_before_finalization(
        original_email=dict(
            DEFAULT_TEST_EMAIL
        ),
        agent1_result=unsafe_agent1_result,
        agent2_result=approved_agent2_result,
    )

    return {
        "case_id": "EVAL-006",
        "status": "STOPPED",
        "stage": "GUARDRAILS",
        "agent2_result": approved_agent2_result,
        "guardrails_result": guardrails_result,
        "agent3_result": None,
    }


# ============================================================
# PUBLIC RUNNER
# ============================================================

def run_evaluation_case(
    case_id: str,
) -> dict[str, Any]:
    """
    Run one deterministic evaluation case.
    """

    if _get_case(case_id) is None:

        return {
            "case_id": case_id,
            "status": "ERROR",
            "stage": "UNKNOWN",
            "message": (
                f"Evaluation case {case_id} was not found."
            ),
        }

    if case_id == "EVAL-001":
        return _eval_001()

    if case_id == "EVAL-002":
        return _eval_002()

    if case_id == "EVAL-003":
        return _eval_003()

    if case_id == "EVAL-004":
        return _eval_004()

    if case_id == "EVAL-005":
        return _eval_005()

    if case_id == "EVAL-006":
        return _eval_006()

    return {
        "case_id": case_id,
        "status": "ERROR",
        "stage": "UNKNOWN",
        "message": (
            f"No runner exists for {case_id}."
        ),
    }


# ============================================================
# RUN ALL CASES
# ============================================================

def run_all_evaluation_cases() -> list[dict[str, Any]]:
    """
    Run every evaluation case exactly once.
    """

    results: list[dict[str, Any]] = []

    for case in EVALUATION_CASES:

        results.append(
            run_evaluation_case(
                case["case_id"]
            )
        )

    return results


# ============================================================
# DIRECT MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Finance Email Evaluation Runner loaded successfully."
    )