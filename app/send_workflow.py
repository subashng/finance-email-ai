from typing import Any

from app.gmail.gmail_client import send_gmail_message
from app.workflow import process_finance_email
from app.database.audit import (
    save_workflow_run,
    update_workflow_run_send_status,
)


def _save_audit_safely(
    sender_email: str,
    subject: str,
    email_body: str,
    workflow_result: dict[str, Any],
    gmail_message_id: str | None,
    gmail_thread_id: str | None,
    final_send_status: str,
) -> dict[str, Any] | None:
    """
    Save the workflow audit record without allowing an audit
    failure to crash the finance workflow result.
    """

    try:

        return save_workflow_run(
            sender_email=sender_email,
            subject=subject,
            email_body=email_body,
            workflow_result=workflow_result,
            gmail_message_id=gmail_message_id,
            gmail_thread_id=gmail_thread_id,
            final_send_status=final_send_status,
        )

    except Exception as exc:

        return {
            "status": "AUDIT_FAILED",
            "message": str(exc),
        }


def send_finance_email(
    sender_email: str,
    subject: str,
    email_body: str,
    reply_thread_id: str | None = None,
    reply_message_id: str | None = None,
    reply_references: str | None = None,
    incoming_message_id: str | None = None,
    incoming_thread_id: str | None = None,
    action_taken: str = (
        "Finance customer email processed."
    ),
) -> dict[str, Any]:
    """
    Execute the Finance Email AI workflow and send the finalized
    response through Gmail.

    Production sequence:

        Agent 1
          ↓
        Agent 2
          ↓
        Guardrails
          ↓
        Agent 3
          ↓
        Save audit record
          ↓
        Gmail Send
          ↓
        Update same audit record

    Sending is allowed only when:

        workflow.status == COMPLETED
        workflow.can_send == True
        Agent 2 decision == APPROVED
        Guardrails decision == APPROVED
        Agent 3 status == FINALIZED
    """

    # =========================================================
    # STEP 1 — RUN FINANCE WORKFLOW
    # =========================================================

    workflow_result = process_finance_email(
        sender_email=sender_email,
        subject=subject,
        email_body=email_body,
        message_id=incoming_message_id,
        thread_id=incoming_thread_id,
        action_taken=action_taken,
    )

    # =========================================================
    # STEP 2 — SAVE INITIAL AUDIT RECORD
    # =========================================================

    initial_audit = _save_audit_safely(
        sender_email=sender_email,
        subject=subject,
        email_body=email_body,
        workflow_result=workflow_result,
        gmail_message_id=incoming_message_id,
        gmail_thread_id=incoming_thread_id,
        final_send_status="NOT_SENT",
    )

    workflow_result["audit_result"] = (
        initial_audit
    )

    workflow_run_id = None

    if (
        initial_audit
        and initial_audit.get("status")
        == "SAVED"
    ):

        workflow_run_id = initial_audit.get(
            "workflow_run_id"
        )

    # =========================================================
    # STEP 3 — WORKFLOW MUST BE COMPLETED
    # =========================================================

    if workflow_result.get(
        "status"
    ) != "COMPLETED":

        return {
            "status": "NOT_SENT",
            "stage": "WORKFLOW",
            "message": (
                "Email was not sent because the finance "
                "workflow did not complete successfully."
            ),
            "workflow_result": workflow_result,
            "audit_result": initial_audit,
        }

    # =========================================================
    # STEP 4 — AGENT 3 MUST ALLOW SENDING
    # =========================================================

    if workflow_result.get(
        "can_send"
    ) is not True:

        return {
            "status": "NOT_SENT",
            "stage": "SEND_GATE",
            "message": (
                "Email was not sent because Agent 3 did not "
                "mark the finalized response as sendable."
            ),
            "workflow_result": workflow_result,
            "audit_result": initial_audit,
        }

    # =========================================================
    # STEP 5 — VALIDATE FINAL EMAIL
    # =========================================================

    final_subject = workflow_result.get(
        "final_email_subject"
    )

    final_body = workflow_result.get(
        "final_email_body"
    )

    if not final_subject:

        return {
            "status": "NOT_SENT",
            "stage": "SEND_VALIDATION",
            "message": (
                "Email was not sent because the final "
                "email subject is missing."
            ),
            "workflow_result": workflow_result,
            "audit_result": initial_audit,
        }

    if not final_body or not final_body.strip():

        return {
            "status": "NOT_SENT",
            "stage": "SEND_VALIDATION",
            "message": (
                "Email was not sent because the final "
                "email body is missing."
            ),
            "workflow_result": workflow_result,
            "audit_result": initial_audit,
        }

    # =========================================================
    # STEP 6 — RECIPIENT
    # =========================================================

    recipient_email = sender_email

    if not recipient_email:

        return {
            "status": "NOT_SENT",
            "stage": "SEND_VALIDATION",
            "message": (
                "Email was not sent because the customer "
                "email address is missing."
            ),
            "workflow_result": workflow_result,
            "audit_result": initial_audit,
        }

    # =========================================================
    # STEP 7 — GMAIL SEND
    # =========================================================

    try:

        gmail_result = send_gmail_message(
            to_email=recipient_email,
            subject=final_subject,
            body=final_body,
            thread_id=reply_thread_id,
            in_reply_to=reply_message_id,
            references=reply_references,
        )

    except Exception as exc:

        # -----------------------------------------------------
        # Update the SAME audit record
        # -----------------------------------------------------

        if workflow_run_id is not None:

            try:

                update_workflow_run_send_status(
                    workflow_run_id=workflow_run_id,
                    final_send_status="SEND_FAILED",
                )

            except Exception as audit_exc:

                workflow_result[
                    "audit_update_error"
                ] = str(audit_exc)

        return {
            "status": "SEND_FAILED",
            "stage": "GMAIL_SEND",
            "message": (
                "The finance workflow completed, but Gmail "
                "sending failed."
            ),
            "error": str(exc),
            "workflow_result": workflow_result,
            "audit_result": initial_audit,
        }

    # =========================================================
    # STEP 8 — UPDATE SAME AUDIT RECORD AS SENT
    # =========================================================

    sent_message_id = gmail_result.get(
        "message_id"
    )

    sent_thread_id = gmail_result.get(
        "thread_id"
    )

    final_audit_update = None

    if workflow_run_id is not None:

        try:

            final_audit_update = (
                update_workflow_run_send_status(
                    workflow_run_id=workflow_run_id,
                    final_send_status="SENT",
                    gmail_message_id=sent_message_id,
                    gmail_thread_id=sent_thread_id,
                )
            )

        except Exception as exc:

            final_audit_update = {
                "status": "AUDIT_UPDATE_FAILED",
                "message": str(exc),
            }

    # =========================================================
    # STEP 9 — FINAL RESULT
    # =========================================================

    return {
        "status": "SENT",
        "stage": "GMAIL_SEND",
        "message": (
            "Finance customer response was approved, finalized, "
            "audited, and sent successfully through Gmail."
        ),
        "recipient_email": recipient_email,
        "thread_id": sent_thread_id,
        "gmail_message_id": sent_message_id,
        "subject": gmail_result.get(
            "subject"
        ),
        "workflow_result": workflow_result,
        "audit_result": initial_audit,
        "audit_update": final_audit_update,
    }


if __name__ == "__main__":

    print(
        "Finance Email Send Workflow loaded successfully."
    )