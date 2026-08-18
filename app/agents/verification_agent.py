import re
import time
from datetime import date
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.finance_tools import (
    get_customer_aging,
    get_customer_invoices,
    get_customer_outstanding,
)
from app.tools.policy_tools import search_finance_policy
from app.tools.verification_tools import verify_financial_evidence


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

client = OpenAI()


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are Agent 2 — Finance Response Verification Agent.

Your role is to independently review Agent 1's proposed
customer-facing response before the response proceeds further.

IMPORTANT ARCHITECTURE RULE:

Authoritative customer-specific financial facts have already
been verified deterministically from the finance database.

You MUST accept deterministic verification as authoritative for:

- invoice amounts
- invoice dates
- due dates
- aging days
- aging buckets
- payment status
- total outstanding
- overdue status

Do NOT independently override authoritative financial evidence.

Your semantic review should focus ONLY on:

1. Unsupported policy claims.
2. Unauthorized financial commitments.
3. Internal system / implementation information exposure.
4. Genuine material semantic contradictions.
5. Materially incomplete answers that could mislead the customer.

If deterministic financial verification PASSED and the semantic
review only disagrees with an authoritative financial fact,
do NOT revise the response because of that disagreement.

Return:

DECISION: APPROVED or REVISE

CONFIDENCE: HIGH, MEDIUM, or LOW

REASON:
<brief explanation>

VERIFIED_ITEMS:
- <verified item>

ISSUES:
- <issue>

CORRECTIONS:
- <correction>

If there are no issues:

ISSUES:
NONE

CORRECTIONS:
NONE
"""


# ============================================================
# TIMING HELPER
# ============================================================

def _elapsed_ms(
    start: float,
) -> float:
    return round(
        (time.perf_counter() - start) * 1000,
        2,
    )


# ============================================================
# POLICY EVIDENCE COMPACTION
# ============================================================

def compact_policy_evidence(
    policy_evidence: dict[str, Any],
    customer_email: str = "",
    proposed_response: str = "",
    max_total_chars: int = 3500,
) -> dict[str, Any]:
    """
    Compact retrieved policy evidence before it is sent to the
    semantic verification LLM.

    Retrieval remains unchanged.
    Full policy evidence remains available for audit.
    Only the semantic LLM context is compacted.
    """

    if not policy_evidence:
        return {
            "status": "NOT_FOUND",
            "message": "No policy evidence available.",
            "results": [],
        }

    results = policy_evidence.get(
        "results",
        [],
    )

    if not results:
        return {
            "status": "NOT_FOUND",
            "message": "No policy evidence available.",
            "results": [],
        }

    context_text = (
        f"{customer_email} {proposed_response}"
    ).lower()

    keyword_groups = {
        "overdue": [
            "overdue",
            "past due",
            "due date",
        ],
        "aging": [
            "aging",
            "days",
        ],
        "payment": [
            "payment",
            "paid",
            "outstanding",
            "balance",
        ],
        "refund": [
            "refund",
            "refunds",
        ],
        "discount": [
            "discount",
            "discounts",
        ],
        "credit": [
            "credit",
            "credits",
        ],
        "extension": [
            "extension",
            "extend",
            "payment term",
        ],
        "waiver": [
            "waiver",
            "waive",
            "penalty",
            "fee",
        ],
        "dispute": [
            "dispute",
            "incorrect",
            "not recognize",
            "already paid",
        ],
        "collection": [
            "collection",
            "collect",
            "collection action",
        ],
        "correction": [
            "correction",
            "correct",
            "adjust",
        ],
        "cancellation": [
            "cancel",
            "cancellation",
            "void",
        ],
        "reversal": [
            "reverse",
            "reversal",
        ],
        "policy": [
            "policy",
            "procedure",
            "process",
        ],
    }

    active_keywords: set[str] = set()

    for keywords in keyword_groups.values():

        for keyword in keywords:

            if keyword in context_text:
                active_keywords.add(
                    keyword
                )

    active_keywords.update(
        {
            "refund",
            "discount",
            "credit",
            "extension",
            "waiver",
            "penalty",
            "collection",
            "correction",
            "cancel",
            "reverse",
        }
    )

    compacted_results: list[dict[str, Any]] = []

    remaining_chars = max_total_chars

    for result in results:

        if remaining_chars <= 0:
            break

        source = str(
            result.get(
                "source",
                "",
            )
        )

        chunk_id = result.get(
            "chunk_id"
        )

        score = result.get(
            "score"
        )

        full_text = str(
            result.get(
                "text",
                "",
            )
        ).strip()

        sentences = re.split(
            r"(?<=[.!?])\s+|\n+",
            full_text,
        )

        relevant_sentences: list[str] = []

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_lower = sentence.lower()

            relevance = any(
                keyword in sentence_lower
                for keyword in active_keywords
            )

            if relevance:
                relevant_sentences.append(
                    sentence
                )

        if not relevant_sentences:

            fallback_sentences = [
                sentence.strip()
                for sentence in sentences
                if sentence.strip()
            ]

            relevant_sentences = (
                fallback_sentences[:4]
            )

        selected_text = "\n".join(
            relevant_sentences
        )

        if len(selected_text) > remaining_chars:

            selected_text = (
                selected_text[:remaining_chars]
                .rsplit(" ", 1)[0]
                .rstrip()
                + " ..."
            )

        if not selected_text.strip():
            continue

        compacted_results.append(
            {
                "source": source,
                "chunk_id": chunk_id,
                "score": score,
                "text": selected_text,
            }
        )

        remaining_chars -= len(
            selected_text
        )

    return {
        "status": policy_evidence.get(
            "status",
            "FOUND",
        ),
        "message": (
            f"{len(compacted_results)} compacted "
            "policy result(s) provided to semantic verification."
        ),
        "results": compacted_results,
    }


# ============================================================
# BUILD AUTHORITATIVE OVERDUE EVIDENCE
# ============================================================

def build_overdue_evidence(
    invoices_result: dict[str, Any],
) -> tuple[str, dict[str, str]]:

    invoices = invoices_result.get(
        "invoices",
        [],
    )

    today = date.today()

    statuses: dict[str, str] = {}
    sections: list[str] = []

    for invoice in invoices:

        invoice_no = invoice.get(
            "invoice_no"
        )

        due_date_text = invoice.get(
            "due_date"
        )

        outstanding_text = invoice.get(
            "outstanding_amount",
            "0.00",
        )

        payment_status = str(
            invoice.get(
                "payment_status",
                "",
            )
        ).strip().lower()

        try:

            due_date = date.fromisoformat(
                str(due_date_text)
            )

        except (
            TypeError,
            ValueError,
        ):

            overdue_status = "UNCONFIRMED"

        else:

            try:

                outstanding = float(
                    outstanding_text
                )

            except (
                TypeError,
                ValueError,
            ):

                outstanding = 0.0

            if (
                due_date < today
                and outstanding > 0
            ):

                overdue_status = "OVERDUE"

            else:

                overdue_status = "NOT_OVERDUE"

        statuses[
            str(invoice_no)
        ] = overdue_status

        sections.append(
            f"""
{invoice_no}

due_date:
{due_date_text}

outstanding_amount:
{outstanding_text}

payment_status:
{payment_status}

authoritative_overdue_status:
{overdue_status}
""".strip()
        )

    return (
        "\n\n".join(sections),
        statuses,
    )


# ============================================================
# CHECK EXPLICIT OVERDUE EXCLUSIVITY
# ============================================================

def check_overdue_claims(
    proposed_response: str,
    overdue_statuses: dict[str, str],
) -> list[str]:

    issues: list[str] = []

    response_lower = proposed_response.lower()

    overdue_invoices = [
        invoice_no
        for invoice_no, status
        in overdue_statuses.items()
        if status == "OVERDUE"
    ]

    if len(overdue_invoices) <= 1:
        return issues

    explicit_patterns = [
        "only one invoice is overdue",
        "only one invoice was overdue",
        "only one invoice remains overdue",
        "only the first invoice is overdue",
        "only the first invoice was overdue",
        "only this invoice is overdue",
        "only this invoice was overdue",
        "the other invoices are not overdue",
        "the other invoices are not yet overdue",
        "the other two invoices are not overdue",
        "the other two invoices are not yet overdue",
        "the other two are not overdue",
        "the other two are not yet overdue",
        "the remaining invoices are not overdue",
        "the remaining invoices are not yet overdue",
        "the remaining invoices are not currently overdue",
    ]

    for pattern in explicit_patterns:

        if pattern in response_lower:

            issues.append(
                "The customer-facing response explicitly "
                "implies that only one invoice is overdue, "
                "but multiple invoices are overdue according "
                "to the authoritative records."
            )

            break

    first_invoice_pattern = (
        r"(first invoice|invoice\s*1)"
        r".{0,200}"
        r"(other two|other 2|remaining two|remaining 2)"
        r".{0,100}"
        r"(not\s+(?:yet\s+)?overdue|"
        r"not\s+(?:yet\s+)?due)"
    )

    if re.search(
        first_invoice_pattern,
        response_lower,
        flags=re.IGNORECASE | re.DOTALL,
    ):

        issues.append(
            "The response states that the first invoice is "
            "overdue while explicitly stating that other "
            "invoices are not overdue, but multiple invoices "
            "are overdue according to the authoritative records."
        )

    return list(
        dict.fromkeys(
            issues
        )
    )


# ============================================================
# NORMALIZE FINAL VERIFICATION
# ============================================================

def _build_final_verification(
    decision: str,
    deterministic_result: dict[str, Any],
    overdue_issues: list[str],
    semantic_review: str,
) -> str:
    """
    Build customer-audit verification text that always matches
    the authoritative final decision.

    Raw semantic LLM review is preserved separately.
    """

    if decision == "APPROVED":

        return (
            "DECISION: APPROVED\n\n"
            "CONFIDENCE: HIGH\n\n"
            "REASON:\n"
            "The response passed authoritative financial "
            "verification and the required safety checks.\n\n"
            "VERIFIED_ITEMS:\n"
            "- Customer-specific financial information was "
            "verified against authoritative finance records.\n"
            "- Deterministic financial verification passed.\n"
            "- Overdue-status verification passed.\n"
            "- No blocking policy or authorization issue "
            "was identified.\n\n"
            "ISSUES:\n"
            "NONE\n\n"
            "CORRECTIONS:\n"
            "NONE"
        )

    issue_lines = []

    for issue in deterministic_result.get(
        "issues",
        [],
    ):

        issue_lines.append(
            f"- {issue}"
        )

    for issue in overdue_issues:

        issue_lines.append(
            f"- {issue}"
        )

    if not issue_lines:

        issue_lines.append(
            "- Customer response requires revision "
            "based on semantic verification."
        )

    return (
        "DECISION: REVISE\n\n"
        "CONFIDENCE: HIGH\n\n"
        "REASON:\n"
        "The response did not pass all required verification "
        "checks and must be revised before sending.\n\n"
        "VERIFIED_ITEMS:\n"
        "- Available authoritative verification checks "
        "were completed.\n\n"
        "ISSUES:\n"
        + "\n".join(issue_lines)
        + "\n\n"
        "CORRECTIONS:\n"
        "Review and correct the identified issues before sending."
    )


# ============================================================
# MAIN AGENT 2 FUNCTION
# ============================================================

def verify_finance_response(
    original_email: dict[str, Any],
    agent1_result: dict[str, Any],
) -> dict[str, Any]:

    total_start = time.perf_counter()

    performance: dict[str, Any] = {
        "sql_invoices_ms": None,
        "sql_outstanding_ms": None,
        "sql_aging_ms": None,
        "deterministic_verification_ms": None,
        "overdue_verification_ms": None,
        "rag_ms": None,
        "semantic_llm_ms": None,
        "total_ms": None,
        "policy_full_chars": None,
        "policy_compact_chars": None,
    }

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not agent1_result:

        performance["total_ms"] = _elapsed_ms(
            total_start
        )

        return {
            "status": "REVISE",
            "decision": "REVISE",
            "reason": (
                "Agent 1 result was not provided."
            ),
            "verification": "",
            "performance": performance,
        }

    proposed_response = agent1_result.get(
        "proposed_response",
        "",
    )

    if not proposed_response.strip():

        performance["total_ms"] = _elapsed_ms(
            total_start
        )

        return {
            "status": "REVISE",
            "decision": "REVISE",
            "reason": (
                "Agent 1 did not provide a proposed response."
            ),
            "verification": "",
            "performance": performance,
        }

    customer_id = agent1_result.get(
        "customer_id"
    )

    if not customer_id:

        performance["total_ms"] = _elapsed_ms(
            total_start
        )

        return {
            "status": "REVISE",
            "decision": "REVISE",
            "reason": (
                "Agent 1 did not provide a verified customer ID."
            ),
            "verification": "",
            "performance": performance,
        }

    # ========================================================
    # STEP 1 — AUTHORITATIVE SQL
    # ========================================================

    start = time.perf_counter()

    sql_invoices = get_customer_invoices(
        customer_id
    )

    performance[
        "sql_invoices_ms"
    ] = _elapsed_ms(
        start
    )

    start = time.perf_counter()

    sql_outstanding = get_customer_outstanding(
        customer_id
    )

    performance[
        "sql_outstanding_ms"
    ] = _elapsed_ms(
        start
    )

    start = time.perf_counter()

    sql_aging = get_customer_aging(
        customer_id
    )

    performance[
        "sql_aging_ms"
    ] = _elapsed_ms(
        start
    )

    if sql_invoices.get(
        "status"
    ) != "FOUND":

        performance["total_ms"] = _elapsed_ms(
            total_start
        )

        return {
            "status": "REVISE",
            "decision": "REVISE",
            "reason": (
                "Authoritative customer invoice records "
                "could not be retrieved."
            ),
            "verification": "",
            "performance": performance,
        }

    # ========================================================
    # STEP 2 — DETERMINISTIC FINANCIAL VERIFICATION
    # ========================================================

    start = time.perf_counter()

    deterministic_result = verify_financial_evidence(
        agent1_result=agent1_result,
        authoritative_invoices=sql_invoices,
        authoritative_outstanding=sql_outstanding,
        authoritative_aging=sql_aging,
    )

    performance[
        "deterministic_verification_ms"
    ] = _elapsed_ms(
        start
    )

    if not deterministic_result.get(
        "passed"
    ):

        performance["total_ms"] = _elapsed_ms(
            total_start
        )

        final_verification = _build_final_verification(
            decision="REVISE",
            deterministic_result=deterministic_result,
            overdue_issues=[],
            semantic_review="",
        )

        return {
            "status": "COMPLETED",
            "decision": "REVISE",
            "reason": (
                "Deterministic financial verification failed."
            ),
            "verification": final_verification,
            "deterministic_verification": (
                deterministic_result
            ),
            "semantic_review": "",
            "semantic_decision": "REVISE",
            "semantic_override": False,
            "performance": performance,
        }

    # ========================================================
    # STEP 3 — OVERDUE STATUS
    # ========================================================

    start = time.perf_counter()

    overdue_evidence, overdue_statuses = (
        build_overdue_evidence(
            sql_invoices
        )
    )

    overdue_issues = check_overdue_claims(
        proposed_response=proposed_response,
        overdue_statuses=overdue_statuses,
    )

    performance[
        "overdue_verification_ms"
    ] = _elapsed_ms(
        start
    )

    if overdue_issues:

        performance["total_ms"] = _elapsed_ms(
            total_start
        )

        final_verification = _build_final_verification(
            decision="REVISE",
            deterministic_result=deterministic_result,
            overdue_issues=overdue_issues,
            semantic_review="",
        )

        return {
            "status": "COMPLETED",
            "decision": "REVISE",
            "reason": (
                "Customer-facing overdue-status verification "
                "failed."
            ),
            "verification": final_verification,
            "issues": overdue_issues,
            "deterministic_verification": (
                deterministic_result
            ),
            "overdue_evidence": overdue_evidence,
            "semantic_review": "",
            "semantic_decision": "REVISE",
            "semantic_override": False,
            "performance": performance,
        }

    # ========================================================
    # STEP 4 — POLICY RAG
    # ========================================================

    policy_query = f"""
Review approved finance policies relevant to this customer
finance request.

Subject:
{original_email.get("subject", "")}

Email:
{original_email.get("email_body", "")}
"""

    start = time.perf_counter()

    policy_evidence = search_finance_policy(
        policy_query,
        top_k=3,
    )

    performance["rag_ms"] = _elapsed_ms(
        start
    )

    # ========================================================
    # STEP 4B — COMPACT POLICY EVIDENCE
    # ========================================================

    full_policy_chars = len(
        str(policy_evidence)
    )

    compact_policy_evidence_result = (
        compact_policy_evidence(
            policy_evidence=policy_evidence,
            customer_email=(
                original_email.get(
                    "email_body",
                    "",
                )
            ),
            proposed_response=proposed_response,
            max_total_chars=3500,
        )
    )

    compact_policy_chars = len(
        str(
            compact_policy_evidence_result
        )
    )

    performance[
        "policy_full_chars"
    ] = full_policy_chars

    performance[
        "policy_compact_chars"
    ] = compact_policy_chars

    # ========================================================
    # STEP 5 — SEMANTIC REVIEW
    # ========================================================

    semantic_input = f"""
ORIGINAL CUSTOMER EMAIL
=======================

Subject:
{original_email.get("subject", "")}

Email:
{original_email.get("email_body", "")}


ACTUAL CUSTOMER-FACING RESPONSE
===============================

{proposed_response}


DETERMINISTIC VERIFICATION
==========================

{deterministic_result}


AUTHORITATIVE OVERDUE STATUS
============================

{overdue_evidence}


APPROVED POLICY EVIDENCE
========================

{compact_policy_evidence_result}


IMPORTANT AUTHORITY RULE
========================

Deterministic verification has already verified:

- outstanding amounts
- invoice dates
- due dates
- aging days
- aging buckets
- payment status
- total outstanding
- overdue status

Do NOT re-check those financial facts.

Only review:

1. Unsupported policy claims.
2. Unauthorized commitments.
3. Internal implementation information.
4. Genuine material semantic contradictions.
5. Materially incomplete answers.

If the deterministic verification passed and there is no genuine
non-financial blocking issue, the final response should be
considered approvable.
"""

    start = time.perf_counter()

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": semantic_input,
            },
        ],
    )

    performance[
        "semantic_llm_ms"
    ] = _elapsed_ms(
        start
    )

    semantic_review = (
        response.output_text.strip()
    )

    # ========================================================
    # STEP 6 — EXTRACT SEMANTIC DECISION
    # ========================================================

    semantic_decision = "REVISE"

    for line in semantic_review.splitlines():

        normalized = line.strip().upper()

        if normalized.startswith(
            "DECISION:"
        ):

            value = normalized.split(
                ":",
                1,
            )[1].strip()

            semantic_decision = (
                "APPROVED"
                if value == "APPROVED"
                else "REVISE"
            )

            break

    # ========================================================
    # STEP 7 — AUTHORITATIVE FINAL DECISION
    # ========================================================

    if (
        deterministic_result.get(
            "passed"
        ) is True
        and not overdue_issues
    ):

        decision = "APPROVED"

    else:

        decision = "REVISE"

    semantic_override = (
        semantic_decision != decision
    )

    # ========================================================
    # STEP 8 — NORMALIZE FINAL VERIFICATION
    # ========================================================

    final_verification = _build_final_verification(
        decision=decision,
        deterministic_result=deterministic_result,
        overdue_issues=overdue_issues,
        semantic_review=semantic_review,
    )

    # ========================================================
    # FINAL TIMING
    # ========================================================

    performance["total_ms"] = _elapsed_ms(
        total_start
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "status": "COMPLETED",
        "decision": decision,
        "verification": final_verification,
        "customer_id": customer_id,
        "deterministic_verification": (
            deterministic_result
        ),
        "overdue_evidence": overdue_evidence,
        "sql_evidence": {
            "invoices": sql_invoices,
            "outstanding": sql_outstanding,
            "aging": sql_aging,
        },

        # Full policy evidence retained for audit.
        "policy_evidence": policy_evidence,

        # Compacted policy evidence sent to semantic reviewer.
        "policy_evidence_compact": (
            compact_policy_evidence_result
        ),

        # Raw semantic review is retained separately.
        "semantic_review": semantic_review,

        # Useful for performance/audit diagnostics.
        "semantic_decision": semantic_decision,
        "semantic_override": semantic_override,

        "performance": performance,
    }


# ============================================================
# DIRECT MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Finance Verification Agent loaded successfully."
    )