import re
from typing import Any


# ============================================================
# PROHIBITED / UNSUPPORTED COMMITMENT PATTERNS
# ============================================================

UNAUTHORIZED_COMMITMENT_PATTERNS = [
    r"\bwe will issue a refund\b",
    r"\bwe will provide a refund\b",
    r"\bwe will give you a refund\b",
    r"\bwe will apply a discount\b",
    r"\bwe will provide a discount\b",
    r"\bwe will extend the payment\b",
    r"\bwe will extend your payment\b",
    r"\bwe will waive the penalty\b",
    r"\bwe will waive the fee\b",
    r"\bwe will cancel the invoice\b",
    r"\bwe will reverse the payment\b",
    r"\bwe will correct the invoice\b",
    r"\bwe will issue a credit\b",
    r"\bwe will apply a credit\b",
]


# ============================================================
# INTERNAL INFORMATION PATTERNS
# ============================================================

INTERNAL_INFORMATION_PATTERNS = [
    r"\bsql\b",
    r"\bsql database\b",
    r"\bfaiss\b",
    r"\bembedding\b",
    r"\bvector database\b",
    r"\brag\b",
    r"\blarge language model\b",
    r"\bgpt-4o-mini\b",
    r"\bverification agent\b",
    r"\bagent 1\b",
    r"\bagent 2\b",
    r"\bagent 3\b",
    r"\bsystem prompt\b",
    r"\binternal prompt\b",
    r"\bdatabase query\b",
    r"\binternal reasoning\b",
]


# ============================================================
# CUSTOMER-FACING PLACEHOLDER PATTERNS
# ============================================================

OBVIOUS_PLACEHOLDER_PATTERNS = [
    r"\[\s*your name\s*\]",
    r"\[\s*your position\s*\]",
    r"\[\s*your title\s*\]",
    r"\[\s*your company\s*\]",
    r"\[\s*your contact information\s*\]",
    r"\[\s*company name\s*\]",
    r"\[\s*customer name\s*\]",
    r"\[\s*account number\s*\]",
    r"\[\s*invoice number\s*\]",
    r"\[\s*date\s*\]",
    r"\[\s*email address\s*\]",
    r"\[\s*phone number\s*\]",
    r"\[\s*insert .*?\]",
    r"\[\s*enter .*?\]",
    r"\[\s*add .*?\]",
    r"<\s*your name\s*>",
    r"<\s*your position\s*>",
    r"<\s*your company\s*>",
]


# ============================================================
# HELPER
# ============================================================

def _find_matches(
    text: str,
    patterns: list[str],
) -> list[str]:
    """
    Return matched patterns.
    """

    matches: list[str] = []

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            matches.append(pattern)

    return matches


# ============================================================
# MAIN GUARDRAILS FUNCTION
# ============================================================

def validate_before_finalization(
    original_email: dict[str, Any],
    agent1_result: dict[str, Any],
    agent2_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Perform deterministic safety checks after Agent 2 and before
    Agent 3.

    Guardrails do NOT:
    - calculate financial values
    - replace SQL verification
    - replace Agent 2
    - generate a new response
    - send email

    Guardrails decide whether the approved response is safe
    to proceed to Agent 3.
    """

    issues: list[str] = []
    warnings: list[str] = []
    passed_checks: list[str] = []

    # =========================================================
    # CHECK 1 — Agent 2 approval
    # =========================================================

    decision = str(
        agent2_result.get(
            "decision",
            "",
        )
    ).strip().upper()

    if decision != "APPROVED":

        issues.append(
            "Agent 2 did not approve the customer-facing response."
        )

    else:

        passed_checks.append(
            "Agent 2 approval confirmed."
        )

    # =========================================================
    # CHECK 2 — Agent 1 response exists
    # =========================================================

    proposed_response = str(
        agent1_result.get(
            "proposed_response",
            "",
        )
    )

    if not proposed_response.strip():

        issues.append(
            "Customer-facing response is empty."
        )

    else:

        passed_checks.append(
            "Customer-facing response is present."
        )

    # =========================================================
    # CHECK 3 — Original customer email exists
    # =========================================================

    customer_body = str(
        original_email.get(
            "email_body",
            "",
        )
    )

    customer_sender = str(
        original_email.get(
            "sender_email",
            "",
        )
    )

    customer_subject = str(
        original_email.get(
            "subject",
            "",
        )
    )

    if not customer_sender.strip():

        issues.append(
            "Original customer sender email is missing."
        )

    else:

        passed_checks.append(
            "Original customer sender is present."
        )

    if not customer_subject.strip():

        issues.append(
            "Original customer subject is missing."
        )

    else:

        passed_checks.append(
            "Original customer subject is present."
        )

    if not customer_body.strip():

        issues.append(
            "Original customer email body is missing."
        )

    else:

        passed_checks.append(
            "Original customer email body is present."
        )

    # =========================================================
    # CHECK 4 — Unauthorized financial commitments
    # =========================================================

    commitment_matches = _find_matches(
        proposed_response,
        UNAUTHORIZED_COMMITMENT_PATTERNS,
    )

    if commitment_matches:

        issues.append(
            "The customer-facing response contains a potentially "
            "unauthorized financial commitment."
        )

    else:

        passed_checks.append(
            "No prohibited financial commitment detected."
        )

    # =========================================================
    # CHECK 5 — Internal information leakage
    # =========================================================

    internal_matches = _find_matches(
        proposed_response,
        INTERNAL_INFORMATION_PATTERNS,
    )

    if internal_matches:

        issues.append(
            "The customer-facing response appears to expose "
            "internal system or implementation information."
        )

    else:

        passed_checks.append(
            "No obvious internal implementation information detected."
        )

    # =========================================================
    # CHECK 6 — Customer-facing placeholders
    #
    # IMPORTANT:
    # This is now a HARD BLOCK.
    # =========================================================

    placeholder_matches = _find_matches(
        proposed_response,
        OBVIOUS_PLACEHOLDER_PATTERNS,
    )

    if placeholder_matches:

        issues.append(
            "The customer-facing response contains unresolved "
            "placeholders and must not be sent."
        )

    else:

        passed_checks.append(
            "No unresolved customer-facing placeholders detected."
        )

    # =========================================================
    # CHECK 7 — Internal verification sections
    # =========================================================

    internal_section_patterns = [
        r"\bDETERMINISTIC VERIFICATION\b",
        r"\bAUTHORITATIVE OVERDUE STATUS\b",
        r"\bSQL EVIDENCE\b",
        r"\bPOLICY EVIDENCE\b",
        r"\bVERIFIED_ITEMS\b",
        r"\bISSUES:\s*NONE\b",
        r"\bCORRECTIONS:\s*NONE\b",
    ]

    section_matches = _find_matches(
        proposed_response,
        internal_section_patterns,
    )

    if section_matches:

        issues.append(
            "The customer-facing response appears to contain "
            "internal verification content."
        )

    else:

        passed_checks.append(
            "No obvious internal verification sections detected."
        )

    # =========================================================
    # CHECK 8 — Unusually short customer message
    # =========================================================

    if (
        customer_body.strip()
        and len(customer_body.strip()) < 3
    ):

        warnings.append(
            "Original customer message is unusually short."
        )

    # =========================================================
    # FINAL DECISION
    # =========================================================

    passed = not issues

    if passed:

        status = "PASSED"
        decision = "APPROVED"

        message = (
            "Guardrails passed. The verified response may proceed "
            "to Agent 3."
        )

    else:

        status = "BLOCKED"
        decision = "REVISE"

        message = (
            "Guardrails blocked the response. It must not proceed "
            "to Agent 3."
        )

    return {
        "status": status,
        "passed": passed,
        "decision": decision,
        "message": message,
        "issues": issues,
        "warnings": warnings,
        "passed_checks": passed_checks,
    }


# ============================================================
# DIRECT MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Finance Email Guardrails loaded successfully."
    )