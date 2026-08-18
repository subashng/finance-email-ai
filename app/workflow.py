import time
from typing import Any

from app.agents.finance_email_agent import analyze_finance_email
from app.agents.verification_agent import verify_finance_response
from app.agents.finalization_agent import finalize_customer_email
from app.guardrails.guardrails import (
    validate_before_finalization,
)


def _elapsed_ms(
    start_time: float,
) -> float:
    """
    Return elapsed time in milliseconds.
    """

    return round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )


def process_finance_email(
    sender_email: str,
    subject: str,
    email_body: str,
    message_id: str | None = None,
    thread_id: str | None = None,
    action_taken: str = (
        "Finance customer email processed and approved."
    ),
) -> dict[str, Any]:
    """
    Execute the Finance Email AI workflow sequentially.

    Sequence:

        Agent 1
          ↓
        Agent 2
          ↓
        Guardrails
          ↓
        Agent 3
          ↓
        Final Communication Record

    This function does not send email.

    Gmail metadata:
        message_id
        thread_id

    are preserved and passed into Agent 3.
    """

    workflow_start = time.perf_counter()

    # =========================================================
    # ORIGINAL CUSTOMER EMAIL
    # =========================================================

    original_email = {
        "sender_email": sender_email,
        "subject": subject,
        "email_body": email_body,
        "message_id": message_id,
        "thread_id": thread_id,
        "action_taken": action_taken,
    }

    # =========================================================
    # PERFORMANCE CONTAINER
    # =========================================================

    performance: dict[str, Any] = {
        "agent1_ms": None,
        "agent2_ms": None,
        "guardrails_ms": None,
        "agent3_ms": None,
        "total_ms": None,
    }

    # =========================================================
    # STEP 1 — AGENT 1
    # =========================================================

    agent1_start = time.perf_counter()

    agent1_result = analyze_finance_email(
        sender_email=sender_email,
        subject=subject,
        email_body=email_body,
    )

    performance["agent1_ms"] = _elapsed_ms(
        agent1_start
    )

    if agent1_result.get(
        "status"
    ) != "COMPLETED":

        performance["total_ms"] = _elapsed_ms(
            workflow_start
        )

        return {
            "status": "STOPPED",
            "stage": "AGENT_1",
            "message": (
                "Workflow stopped because Agent 1 "
                "did not complete successfully."
            ),
            "agent1_result": agent1_result,
            "agent2_result": None,
            "guardrails_result": None,
            "agent3_result": None,
            "can_send": False,
            "performance": performance,
            "message_id": message_id,
            "thread_id": thread_id,
            "sender_email": sender_email,
            "subject": subject,
        }

    # =========================================================
    # STEP 2 — AGENT 2
    # =========================================================

    agent2_start = time.perf_counter()

    agent2_result = verify_finance_response(
        original_email=original_email,
        agent1_result=agent1_result,
    )

    performance["agent2_ms"] = _elapsed_ms(
        agent2_start
    )

    agent2_decision = str(
        agent2_result.get(
            "decision",
            "",
        )
    ).strip().upper()

    if agent2_decision != "APPROVED":

        performance["total_ms"] = _elapsed_ms(
            workflow_start
        )

        return {
            "status": "STOPPED",
            "stage": "AGENT_2",
            "message": (
                "Workflow stopped because Agent 2 "
                "did not approve the customer response."
            ),
            "agent1_result": agent1_result,
            "agent2_result": agent2_result,
            "guardrails_result": None,
            "agent3_result": None,
            "can_send": False,
            "performance": performance,
            "message_id": message_id,
            "thread_id": thread_id,
            "sender_email": sender_email,
            "subject": subject,
        }

    # =========================================================
    # STEP 3 — GUARDRAILS
    # =========================================================

    guardrails_start = time.perf_counter()

    guardrails_result = validate_before_finalization(
        original_email=original_email,
        agent1_result=agent1_result,
        agent2_result=agent2_result,
    )

    performance["guardrails_ms"] = _elapsed_ms(
        guardrails_start
    )

    if (
        guardrails_result.get("status")
        != "PASSED"
        or guardrails_result.get("passed")
        is not True
        or str(
            guardrails_result.get(
                "decision",
                "",
            )
        ).strip().upper()
        != "APPROVED"
    ):

        performance["total_ms"] = _elapsed_ms(
            workflow_start
        )

        return {
            "status": "STOPPED",
            "stage": "GUARDRAILS",
            "message": (
                "Workflow stopped because Guardrails "
                "did not approve the response."
            ),
            "agent1_result": agent1_result,
            "agent2_result": agent2_result,
            "guardrails_result": guardrails_result,
            "agent3_result": None,
            "can_send": False,
            "performance": performance,
            "message_id": message_id,
            "thread_id": thread_id,
            "sender_email": sender_email,
            "subject": subject,
        }

    # =========================================================
    # STEP 4 — AGENT 3
    # =========================================================

    agent3_start = time.perf_counter()

    agent3_result = finalize_customer_email(
        original_email=original_email,
        agent1_result=agent1_result,
        agent2_result=agent2_result,
    )

    performance["agent3_ms"] = _elapsed_ms(
        agent3_start
    )

    if agent3_result.get(
        "status"
    ) != "FINALIZED":

        performance["total_ms"] = _elapsed_ms(
            workflow_start
        )

        return {
            "status": "STOPPED",
            "stage": "AGENT_3",
            "message": (
                "Workflow stopped because Agent 3 "
                "could not finalize the customer email."
            ),
            "agent1_result": agent1_result,
            "agent2_result": agent2_result,
            "guardrails_result": guardrails_result,
            "agent3_result": agent3_result,
            "can_send": False,
            "performance": performance,
            "message_id": message_id,
            "thread_id": thread_id,
            "sender_email": sender_email,
            "subject": subject,
        }

    # =========================================================
    # FINAL PERFORMANCE
    # =========================================================

    performance["total_ms"] = _elapsed_ms(
        workflow_start
    )

    # =========================================================
    # FINAL WORKFLOW RESULT
    # =========================================================

    return {
        "status": "COMPLETED",
        "stage": "AGENT_3",
        "message": (
            "Finance email workflow completed successfully "
            "and the Final Communication Record was created."
        ),
        "agent1_result": agent1_result,
        "agent2_result": agent2_result,
        "guardrails_result": guardrails_result,
        "agent3_result": agent3_result,
        "can_send": agent3_result.get(
            "can_send",
            False,
        ),
        "final_email_subject": agent3_result.get(
            "final_email_subject"
        ),
        "final_email_body": agent3_result.get(
            "final_email_body"
        ),
        "communication_record": agent3_result.get(
            "communication_record"
        ),
        "message_id": message_id,
        "thread_id": thread_id,
        "sender_email": sender_email,
        "subject": subject,
        "action_taken": action_taken,
        "performance": performance,
    }


if __name__ == "__main__":

    result = process_finance_email(
        sender_email="customer@example.com",
        subject="Question about my outstanding invoice",
        email_body=(
            "Hello, I am ABC 001 Traders. "
            "Please tell me how much I currently owe "
            "and whether any of my invoices are overdue."
        ),
        message_id="CONTROLLED_TEST_MESSAGE_001",
        thread_id="CONTROLLED_TEST_THREAD_001",
        action_taken=(
            "Outstanding invoice inquiry verified "
            "against authoritative finance records."
        ),
    )

    print("=" * 70)
    print("FINANCE EMAIL WORKFLOW")
    print("=" * 70)

    print("\nSTATUS:")
    print(
        result.get("status")
    )

    print("\nSTAGE:")
    print(
        result.get("stage")
    )

    print("\nAGENT 2 DECISION:")
    print(
        result.get(
            "agent2_result",
            {},
        ).get(
            "decision"
        )
    )

    print("\nGUARDRAILS DECISION:")
    print(
        result.get(
            "guardrails_result",
            {},
        ).get(
            "decision"
        )
    )

    print("\nCAN SEND:")
    print(
        result.get("can_send")
    )

    print("\nMESSAGE ID:")
    print(
        result.get("message_id")
    )

    print("\nTHREAD ID:")
    print(
        result.get("thread_id")
    )

    print("\nACTION TAKEN:")
    print(
        result.get("action_taken")
    )

    print("\nFINAL COMMUNICATION RECORD:")
    print("-" * 70)
    print(
        result.get(
            "communication_record"
        )
    )

    print("\nPERFORMANCE:")
    print("-" * 70)

    performance = result.get(
        "performance",
        {},
    )

    print(
        f"Agent 1      : "
        f"{performance.get('agent1_ms')} ms"
    )

    print(
        f"Agent 2      : "
        f"{performance.get('agent2_ms')} ms"
    )

    print(
        f"Guardrails   : "
        f"{performance.get('guardrails_ms')} ms"
    )

    print(
        f"Agent 3      : "
        f"{performance.get('agent3_ms')} ms"
    )

    print(
        f"Total        : "
        f"{performance.get('total_ms')} ms"
    )