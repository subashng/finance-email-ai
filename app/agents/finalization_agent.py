from typing import Any


def finalize_customer_email(
    original_email: dict[str, Any],
    agent1_result: dict[str, Any],
    agent2_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Finalize the customer communication after Agent 2 verification.

    Agent 3 is responsible for creating the complete
    Final Communication Record.

    Agent 3 does NOT:
    - generate new financial facts
    - recalculate financial information
    - modify the customer's original email
    - override Agent 2
    - send email

    The Final Communication Record contains:

    1. Customer email ID
    2. Incoming Gmail message ID
    3. Gmail thread ID
    4. Exact original subject
    5. Exact original customer email
    6. Action taken
    7. Workflow status
    8. Agent 2 decision
    9. Agent 2 verification
    10. Approved company response

    Agent 3 may proceed only when Agent 2 returns APPROVED.
    """

    # =========================================================
    # STEP 1 — Validate Agent 2 decision
    # =========================================================

    agent2_decision = str(
        agent2_result.get(
            "decision",
            "",
        )
    ).strip().upper()

    if agent2_decision != "APPROVED":

        return {
            "status": "BLOCKED",
            "can_send": False,
            "message": (
                "Agent 3 cannot finalize the email because "
                "Agent 2 did not approve the response."
            ),
            "agent2_decision": agent2_decision,
        }

    # =========================================================
    # STEP 2 — Validate original customer email
    # =========================================================

    sender_email = original_email.get(
        "sender_email"
    )

    subject = original_email.get(
        "subject"
    )

    email_body = original_email.get(
        "email_body"
    )

    incoming_message_id = original_email.get(
        "message_id"
    )

    thread_id = original_email.get(
        "thread_id"
    )

    action_taken = original_email.get(
        "action_taken",
        "Finance customer email processed and approved.",
    )

    if not sender_email:

        return {
            "status": "ERROR",
            "can_send": False,
            "message": (
                "Original customer sender email is missing."
            ),
        }

    if not subject:

        return {
            "status": "ERROR",
            "can_send": False,
            "message": (
                "Original customer email subject is missing."
            ),
        }

    if not email_body or not str(email_body).strip():

        return {
            "status": "ERROR",
            "can_send": False,
            "message": (
                "Original customer email body is missing."
            ),
        }

    # =========================================================
    # STEP 3 — Get Agent 1 proposed response
    # =========================================================

    proposed_response = agent1_result.get(
        "proposed_response"
    )

    if (
        not proposed_response
        or not str(proposed_response).strip()
    ):

        return {
            "status": "ERROR",
            "can_send": False,
            "message": (
                "Agent 1 did not provide a proposed response."
            ),
        }

    # =========================================================
    # STEP 4 — Validate Agent 2 verification
    # =========================================================

    verification_text = agent2_result.get(
        "verification",
        "",
    )

    if not verification_text:

        return {
            "status": "ERROR",
            "can_send": False,
            "message": (
                "Agent 2 approval does not contain "
                "verification information."
            ),
        }

    # =========================================================
    # STEP 5 — Preserve original customer email EXACTLY
    # =========================================================

    original_customer_email = {
        "customer_email_id": sender_email,
        "incoming_message_id": incoming_message_id,
        "thread_id": thread_id,
        "subject": subject,
        "email_body": email_body,
    }

    # =========================================================
    # STEP 6 — Final Communication Record
    # =========================================================

    communication_record = {
        "customer_email_id": sender_email,
        "incoming_message_id": incoming_message_id,
        "thread_id": thread_id,
        "subject": subject,

        # IMPORTANT:
        # Exact incoming customer message.
        "original_customer_email": email_body,

        "action_taken": action_taken,
        "workflow_status": "FINALIZED",
        "agent2_decision": agent2_decision,

        "agent2_verification": {
            "decision": agent2_decision,
            "verification": verification_text,
        },

        "company_response": proposed_response,
    }

    # =========================================================
    # STEP 7 — Build final communication content
    # =========================================================

    final_email_body = (
        "CUSTOMER EMAIL\n"
        "===============\n\n"
        f"Customer Email ID: {sender_email}\n"
        f"Incoming Message ID: "
        f"{incoming_message_id or 'N/A'}\n"
        f"Thread ID: "
        f"{thread_id or 'N/A'}\n"
        f"Subject: {subject}\n\n"

        "Original Customer Message:\n"
        "--------------------------\n"
        f"{email_body}\n\n"

        "ACTION TAKEN\n"
        "============\n"
        f"{action_taken}\n\n"

        "WORKFLOW STATUS\n"
        "===============\n"
        "FINALIZED\n\n"

        "COMPANY RESPONSE\n"
        "================\n\n"
        f"{proposed_response}"
    )

    # =========================================================
    # STEP 8 — Final result
    # =========================================================

    return {
        "status": "FINALIZED",
        "can_send": True,
        "message": (
            "Customer email and approved company response "
            "were successfully combined into the Final "
            "Communication Record."
        ),

        "customer_email": original_customer_email,

        "company_response": proposed_response,

        "communication_record": communication_record,

        "final_email_subject": (
            f"Re: {subject}"
            if not subject.lower().startswith("re:")
            else subject
        ),

        "final_email_body": final_email_body,

        "agent2_decision": agent2_decision,

        "customer_email_id": sender_email,

        "incoming_message_id": incoming_message_id,

        "thread_id": thread_id,

        "action_taken": action_taken,
    }


if __name__ == "__main__":

    print(
        "Finance Email Finalization Agent loaded successfully."
    )