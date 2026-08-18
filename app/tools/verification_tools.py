from decimal import Decimal, InvalidOperation
import re
from typing import Any


def _to_decimal(value: Any) -> Decimal | None:
    """
    Safely convert a value to Decimal.
    """

    if value is None:
        return None

    try:
        cleaned = str(value).replace(",", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _normalize_text(value: Any) -> str:
    """
    Normalize text for reliable comparisons.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


def _extract_invoice_sections(
    response: str,
    invoice_numbers: list[str],
) -> dict[str, str]:
    """
    Extract the portion of the customer-facing response
    associated with each invoice number.
    """

    sections: dict[str, str] = {}

    if not response:
        return sections

    response_lower = response.lower()

    for invoice_no in invoice_numbers:

        start = response_lower.find(
            invoice_no.lower()
        )

        if start == -1:
            continue

        next_positions = []

        for other_invoice in invoice_numbers:

            if other_invoice == invoice_no:
                continue

            position = response_lower.find(
                other_invoice.lower(),
                start + len(invoice_no),
            )

            if position != -1:
                next_positions.append(position)

        if next_positions:
            end = min(next_positions)
        else:
            end = len(response)

        sections[invoice_no] = response[start:end]

    return sections


def _extract_money_after_label(
    section: str,
    labels: list[str],
) -> Decimal | None:
    """
    Extract a monetary value after a financial label.

    Supports normal text and Markdown such as:

    Outstanding Amount: ₹112,578.91

    **Outstanding Amount:** ₹112,578.91
    """

    if not section:
        return None

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    pattern = (
        rf"(?:{label_pattern})"
        rf"[\s*]*"
        rf"[:\-]?"
        rf"[\s*]*"
        rf"(?:₹|INR|Rs\.?|Rs)?"
        rf"[\s*]*"
        rf"([0-9][0-9,]*(?:\.[0-9]+)?)"
    )

    match = re.search(
        pattern,
        section,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return _to_decimal(
        match.group(1)
    )


def _extract_aging_bucket(
    section: str,
) -> str | None:
    """
    Extract an aging bucket from the customer-facing response.
    """

    if not section:
        return None

    patterns = [
        r"\b90\+\s*Days\b",
        r"\b61-90\s*Days\b",
        r"\b31-60\s*Days\b",
        r"\b1-30\s*Days\b",
        r"\bCurrent\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            section,
            flags=re.IGNORECASE,
        )

        if match:
            return re.sub(
                r"\s+",
                " ",
                match.group(0).strip(),
            )

    return None


def _extract_aging_days(
    section: str,
) -> int | None:
    """
    Extract numeric aging days when explicitly stated.

    Examples:

    Aging: 120 days
    Aging: 44 days
    """

    if not section:
        return None

    patterns = [
        r"aging\s*(?:status)?\s*[:\-]?\s*(\d+)\s*days",
        r"aging\s*[:\-]?\s*(\d+)\s*day",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            section,
            flags=re.IGNORECASE,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


def _verify_customer_response_claims(
    proposed_response: str,
    authoritative_records: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """
    Verify financial claims made in the actual customer-facing
    response.

    Returns:

    issues
    verified
    """

    issues: list[str] = []
    verified: list[str] = []

    if not proposed_response.strip():
        return issues, verified

    invoice_numbers = list(
        authoritative_records.keys()
    )

    response_sections = _extract_invoice_sections(
        proposed_response,
        invoice_numbers,
    )

    for invoice_no, section in response_sections.items():

        actual = authoritative_records[
            invoice_no
        ]

        # =====================================================
        # CUSTOMER-FACING OUTSTANDING AMOUNT
        # =====================================================

        response_outstanding = (
            _extract_money_after_label(
                section,
                [
                    "Outstanding Amount",
                    "Outstanding Balance",
                    "Outstanding",
                ],
            )
        )

        if response_outstanding is not None:

            actual_outstanding = _to_decimal(
                actual.get(
                    "outstanding_amount"
                )
            )

            if (
                actual_outstanding is None
                or response_outstanding
                != actual_outstanding
            ):

                issues.append(
                    f"{invoice_no}: customer-facing "
                    "outstanding amount mismatch. "
                    f"Response={response_outstanding}, "
                    f"SQL={actual_outstanding}."
                )

            else:

                verified.append(
                    f"{invoice_no}: customer-facing "
                    "outstanding amount verified."
                )

        # =====================================================
        # CUSTOMER-FACING AGING BUCKET
        # =====================================================

        response_bucket = (
            _extract_aging_bucket(
                section
            )
        )

        if response_bucket is not None:

            actual_bucket = _normalize_text(
                actual.get(
                    "aging_bucket"
                )
            )

            if (
                _normalize_text(
                    response_bucket
                )
                != actual_bucket
            ):

                issues.append(
                    f"{invoice_no}: customer-facing "
                    "aging bucket mismatch. "
                    f"Response={response_bucket}, "
                    f"SQL={actual.get('aging_bucket')}."
                )

            else:

                verified.append(
                    f"{invoice_no}: customer-facing "
                    "aging bucket verified."
                )

        # =====================================================
        # CUSTOMER-FACING AGING DAYS
        # =====================================================

        response_days = (
            _extract_aging_days(
                section
            )
        )

        if response_days is not None:

            try:
                actual_days = int(
                    actual.get(
                        "aging_days"
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                actual_days = None

            if (
                actual_days is None
                or response_days != actual_days
            ):

                issues.append(
                    f"{invoice_no}: customer-facing "
                    "aging days mismatch. "
                    f"Response={response_days}, "
                    f"SQL={actual_days}."
                )

            else:

                verified.append(
                    f"{invoice_no}: customer-facing "
                    "aging days verified."
                )

    return issues, verified


def verify_financial_evidence(
    agent1_result: dict[str, Any],
    authoritative_invoices: dict[str, Any],
    authoritative_outstanding: dict[str, Any],
    authoritative_aging: dict[str, Any],
) -> dict[str, Any]:
    """
    Deterministically verify:

    1. Agent 1 structured financial evidence.
    2. Actual customer-facing financial claims.

    This function does not use an LLM.
    """

    issues: list[str] = []
    verified: list[str] = []

    # =========================================================
    # AUTHORITATIVE DATA VALIDATION
    # =========================================================

    if authoritative_invoices.get(
        "status"
    ) != "FOUND":

        return {
            "status": "FAILED",
            "passed": False,
            "issues": [
                "Authoritative invoice records could not be retrieved."
            ],
            "verified": [],
        }

    authoritative_records = {
        invoice["invoice_no"]: invoice
        for invoice in authoritative_invoices.get(
            "invoices",
            [],
        )
    }

    # =========================================================
    # AGENT 1 STRUCTURED FINANCIAL EVIDENCE
    # =========================================================

    agent1_financial = agent1_result.get(
        "financial_evidence",
        {},
    )

    agent1_invoice_data = agent1_financial.get(
        "invoices",
        {},
    )

    agent1_invoices = agent1_invoice_data.get(
        "invoices",
        [],
    )

    # =========================================================
    # VERIFY AGENT 1 STRUCTURED INVOICE DATA
    # =========================================================

    for reported in agent1_invoices:

        invoice_no = reported.get(
            "invoice_no"
        )

        if not invoice_no:

            issues.append(
                "Agent 1 reported an invoice without an invoice number."
            )

            continue

        if invoice_no not in authoritative_records:

            issues.append(
                f"Invoice {invoice_no} was not found in the "
                "authoritative SQL database."
            )

            continue

        actual = authoritative_records[
            invoice_no
        ]

        # -----------------------------------------------------
        # Outstanding amount
        # -----------------------------------------------------

        reported_outstanding = reported.get(
            "outstanding_amount"
        )

        actual_outstanding = actual.get(
            "outstanding_amount"
        )

        if reported_outstanding is not None:

            reported_decimal = _to_decimal(
                reported_outstanding
            )

            actual_decimal = _to_decimal(
                actual_outstanding
            )

            if (
                reported_decimal is None
                or actual_decimal is None
                or reported_decimal != actual_decimal
            ):

                issues.append(
                    f"{invoice_no}: outstanding amount mismatch. "
                    f"Agent 1={reported_outstanding}, "
                    f"SQL={actual_outstanding}."
                )

            else:

                verified.append(
                    f"{invoice_no}: outstanding amount verified."
                )

        # -----------------------------------------------------
        # Invoice date
        # -----------------------------------------------------

        if reported.get(
            "invoice_date"
        ) is not None:

            if (
                reported["invoice_date"]
                != actual["invoice_date"]
            ):

                issues.append(
                    f"{invoice_no}: invoice date mismatch."
                )

            else:

                verified.append(
                    f"{invoice_no}: invoice date verified."
                )

        # -----------------------------------------------------
        # Due date
        # -----------------------------------------------------

        if reported.get(
            "due_date"
        ) is not None:

            if (
                reported["due_date"]
                != actual["due_date"]
            ):

                issues.append(
                    f"{invoice_no}: due date mismatch."
                )

            else:

                verified.append(
                    f"{invoice_no}: due date verified."
                )

        # -----------------------------------------------------
        # Aging days
        # -----------------------------------------------------

        if reported.get(
            "aging_days"
        ) is not None:

            try:

                reported_days = int(
                    reported["aging_days"]
                )

                actual_days = int(
                    actual["aging_days"]
                )

                if reported_days != actual_days:

                    issues.append(
                        f"{invoice_no}: aging days mismatch. "
                        f"Agent 1={reported_days}, "
                        f"SQL={actual_days}."
                    )

                else:

                    verified.append(
                        f"{invoice_no}: aging days verified."
                    )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    f"{invoice_no}: invalid aging days value."
                )

        # -----------------------------------------------------
        # Aging bucket
        # -----------------------------------------------------

        if reported.get(
            "aging_bucket"
        ) is not None:

            reported_bucket = _normalize_text(
                reported["aging_bucket"]
            )

            actual_bucket = _normalize_text(
                actual["aging_bucket"]
            )

            if reported_bucket != actual_bucket:

                issues.append(
                    f"{invoice_no}: aging bucket mismatch. "
                    f"Agent 1={reported['aging_bucket']}, "
                    f"SQL={actual['aging_bucket']}."
                )

            else:

                verified.append(
                    f"{invoice_no}: aging bucket verified."
                )

        # -----------------------------------------------------
        # Payment status
        # -----------------------------------------------------

        if reported.get(
            "payment_status"
        ) is not None:

            if (
                _normalize_text(
                    reported["payment_status"]
                )
                != _normalize_text(
                    actual["payment_status"]
                )
            ):

                issues.append(
                    f"{invoice_no}: payment status mismatch."
                )

            else:

                verified.append(
                    f"{invoice_no}: payment status verified."
                )

    # =========================================================
    # VERIFY TOTAL OUTSTANDING
    # =========================================================

    actual_total = _to_decimal(
        authoritative_outstanding.get(
            "total_outstanding",
            "0.00",
        )
    )

    agent1_total = (
        agent1_financial.get(
            "outstanding",
            {},
        ).get(
            "total_outstanding"
        )
    )

    if agent1_total is not None:

        reported_total = _to_decimal(
            agent1_total
        )

        if (
            reported_total is None
            or actual_total is None
            or reported_total != actual_total
        ):

            issues.append(
                "Total outstanding amount mismatch. "
                f"Agent 1={agent1_total}, "
                f"SQL={actual_total}."
            )

        else:

            verified.append(
                "Total outstanding amount verified."
            )

    # =========================================================
    # VERIFY ACTUAL CUSTOMER-FACING RESPONSE
    # =========================================================

    response_issues, response_verified = (
        _verify_customer_response_claims(
            proposed_response=agent1_result.get(
                "proposed_response",
                "",
            ),
            authoritative_records=authoritative_records,
        )
    )

    issues.extend(
        response_issues
    )

    verified.extend(
        response_verified
    )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    return {
        "status": (
            "PASSED"
            if not issues
            else "FAILED"
        ),
        "passed": not issues,
        "issues": issues,
        "verified": verified,
    }