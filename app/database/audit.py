from datetime import datetime, timezone
from typing import Any

from app.database.database import SessionLocal
from app.database.models import WorkflowRun


def _get_decision(
    result: dict[str, Any] | None,
) -> str | None:
    """Safely extract a decision."""

    if not result:
        return None

    value = result.get("decision")

    if value is None:
        return None

    return str(value)


def save_workflow_run(
    sender_email: str,
    subject: str,
    email_body: str,
    workflow_result: dict[str, Any],
    gmail_message_id: str | None = None,
    gmail_thread_id: str | None = None,
    final_send_status: str | None = None,
) -> dict[str, Any]:
    """
    Save one Finance Email AI workflow execution.

    The original customer email is stored exactly as received.
    """

    performance = workflow_result.get(
        "performance",
        {},
    )

    agent2_result = workflow_result.get(
        "agent2_result",
    )

    guardrails_result = workflow_result.get(
        "guardrails_result",
    )

    communication_record = workflow_result.get(
        "communication_record",
        {},
    )

    customer_email_id = (
        communication_record.get(
            "customer_email_id"
        )
        or workflow_result.get(
            "sender_email"
        )
        or sender_email
    )

    incoming_message_id = (
        communication_record.get(
            "incoming_message_id"
        )
        or workflow_result.get(
            "message_id"
        )
        or gmail_message_id
    )

    thread_id = (
        communication_record.get(
            "thread_id"
        )
        or workflow_result.get(
            "thread_id"
        )
        or gmail_thread_id
    )

    original_customer_email = (
        communication_record.get(
            "original_customer_email"
        )
    )

    if original_customer_email is None:
        original_customer_email = email_body

    action_taken = (
        communication_record.get(
            "action_taken"
        )
        or workflow_result.get(
            "action_taken"
        )
        or "Finance customer email processed."
    )

    workflow_status = str(
        communication_record.get(
            "workflow_status"
        )
        or workflow_result.get(
            "status",
            "",
        )
    )

    subject_value = str(
        communication_record.get(
            "subject"
        )
        or workflow_result.get(
            "subject",
            subject,
        )
    )

    sender_value = str(
        sender_email
        or workflow_result.get(
            "sender_email",
            "",
        )
    )

    run = WorkflowRun(
        created_at=datetime.now(
            timezone.utc
        ).isoformat(),

        sender_email=sender_value,

        customer_email_id=str(
            customer_email_id
        ),

        incoming_message_id=(
            str(incoming_message_id)
            if incoming_message_id
            else None
        ),

        gmail_thread_id=(
            str(thread_id)
            if thread_id
            else None
        ),

        subject=subject_value,

        original_customer_email=str(
            original_customer_email
        ),

        action_taken=str(
            action_taken
        ),

        status=workflow_status,

        stage=str(
            workflow_result.get(
                "stage",
                "",
            )
        ),

        agent2_decision=_get_decision(
            agent2_result
        ),

        guardrails_decision=_get_decision(
            guardrails_result
        ),

        can_send=bool(
            workflow_result.get(
                "can_send",
                False,
            )
        ),

        final_send_status=final_send_status,

        agent1_ms=performance.get(
            "agent1_ms"
        ),

        agent2_ms=performance.get(
            "agent2_ms"
        ),

        guardrails_ms=performance.get(
            "guardrails_ms"
        ),

        agent3_ms=performance.get(
            "agent3_ms"
        ),

        total_ms=performance.get(
            "total_ms"
        ),

        gmail_message_id=gmail_message_id,

        gmail_sent_thread_id=gmail_thread_id,
    )

    db = SessionLocal()

    try:

        db.add(run)
        db.commit()
        db.refresh(run)

        return {
            "status": "SAVED",
            "workflow_run_id": run.id,
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


def update_workflow_run_send_status(
    workflow_run_id: int,
    final_send_status: str,
    gmail_message_id: str | None = None,
    gmail_thread_id: str | None = None,
) -> dict[str, Any]:
    """
    Update the existing audit row after Gmail send succeeds
    or fails.

    This prevents duplicate audit records.
    """

    db = SessionLocal()

    try:

        run = (
            db.query(
                WorkflowRun
            )
            .filter(
                WorkflowRun.id
                == workflow_run_id
            )
            .first()
        )

        if run is None:

            return {
                "status": "NOT_FOUND",
                "workflow_run_id": workflow_run_id,
            }

        run.final_send_status = (
            final_send_status
        )

        if gmail_message_id:
            run.gmail_message_id = (
                gmail_message_id
            )

        if gmail_thread_id:
            run.gmail_sent_thread_id = (
                gmail_thread_id
            )

        db.commit()
        db.refresh(run)

        return {
            "status": "UPDATED",
            "workflow_run_id": run.id,
            "final_send_status": (
                run.final_send_status
            ),
            "gmail_message_id": (
                run.gmail_message_id
            ),
            "gmail_thread_id": (
                run.gmail_sent_thread_id
            ),
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


def get_recent_workflow_runs(
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Return recent workflow executions for the dashboard.
    """

    if limit < 1:
        limit = 1

    if limit > 500:
        limit = 500

    db = SessionLocal()

    try:

        rows = (
            db.query(
                WorkflowRun
            )
            .order_by(
                WorkflowRun.id.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": row.id,
                "created_at": row.created_at,
                "sender_email": row.sender_email,
                "customer_email_id": row.customer_email_id,
                "incoming_message_id": (
                    row.incoming_message_id
                ),
                "gmail_thread_id": (
                    row.gmail_thread_id
                ),
                "subject": row.subject,
                "original_customer_email": (
                    row.original_customer_email
                ),
                "action_taken": (
                    row.action_taken
                ),
                "status": row.status,
                "stage": row.stage,
                "agent2_decision": (
                    row.agent2_decision
                ),
                "guardrails_decision": (
                    row.guardrails_decision
                ),
                "can_send": row.can_send,
                "final_send_status": (
                    row.final_send_status
                ),
                "agent1_ms": row.agent1_ms,
                "agent2_ms": row.agent2_ms,
                "guardrails_ms": row.guardrails_ms,
                "agent3_ms": row.agent3_ms,
                "total_ms": row.total_ms,
                "gmail_message_id": (
                    row.gmail_message_id
                ),
                "gmail_sent_thread_id": (
                    row.gmail_sent_thread_id
                ),
            }
            for row in rows
        ]

    finally:

        db.close()


if __name__ == "__main__":

    print(
        "Finance Email audit repository loaded successfully."
    )