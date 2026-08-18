from typing import Any

from app.database.audit import get_recent_workflow_runs
from app.gmail.mailbox_service import list_business_inbox_messages
from app.send_workflow import send_finance_email


# ============================================================
# STRONG FINANCE INTENT TERMS
# ============================================================

STRONG_FINANCE_TERMS = {
    "invoice",
    "invoices",
    "outstanding balance",
    "outstanding amount",
    "amount owed",
    "amount due",
    "overdue invoice",
    "overdue invoices",
    "aging report",
    "aging bucket",
    "invoice aging",
    "payment status",
    "payment received",
    "payment made",
    "remittance",
    "remittance advice",
    "customer statement",
    "account statement",
    "billing inquiry",
    "billing issue",
    "billing question",
    "finance support",
    "accounts receivable",
    "accounts payable",
    "credit note",
    "debit note",
    "invoice dispute",
    "invoice query",
    "invoice question",
    "due date",
    "outstanding invoice",
}


# ============================================================
# EXPLICIT NON-FINANCE TERMS
# ============================================================

NON_FINANCE_TERMS = {
    "security alert",
    "security notification",
    "verification code",
    "confirmation instructions",
    "confirm your email",
    "welcome to",
    "password reset",
    "sign in",
    "login alert",
    "account security",
    "new sign-in",
    "two-step verification",
    "subscription",
    "newsletter",
    "unsubscribe",
    "api key",
    "developer account",
    "system notification",
}


# ============================================================
# FINANCE CLASSIFIER
# ============================================================

def is_finance_email(
    subject: str,
    email_body: str,
) -> bool:
    """
    Deterministically classify a message as finance-related.

    Routing philosophy:
    - Strong finance intent is required.
    - Generic words such as "payment" or "account" alone
      are NOT sufficient.
    - Known system/security/newsletter messages are excluded.
    """

    subject_text = str(
        subject or ""
    ).strip().lower()

    body_text = str(
        email_body or ""
    ).strip().lower()

    full_text = (
        f"{subject_text}\n{body_text}"
    )

    if not full_text.strip():
        return False

    # --------------------------------------------------------
    # HARD EXCLUSION
    # --------------------------------------------------------

    if any(
        term in full_text
        for term in NON_FINANCE_TERMS
    ):
        return False

    # --------------------------------------------------------
    # STRONG FINANCE INTENT
    # --------------------------------------------------------

    if any(
        term in full_text
        for term in STRONG_FINANCE_TERMS
    ):
        return True

    return False


# ============================================================
# ALREADY PROCESSED MESSAGE IDS
# ============================================================

def get_processed_message_ids() -> set[str]:
    """
    Return Gmail message IDs already represented in audit data.
    """

    runs = get_recent_workflow_runs(
        limit=500
    )

    processed_ids: set[str] = set()

    for run in runs:

        message_id = run.get(
            "incoming_message_id"
        )

        if message_id:

            processed_ids.add(
                str(message_id)
            )

    return processed_ids


# ============================================================
# PROCESS ONE MESSAGE
# ============================================================

def process_one_inbox_message(
    message: dict[str, Any],
) -> dict[str, Any]:
    """
    Route and process one real Gmail inbox message.
    """

    message_id = str(
        message.get(
            "message_id",
            "",
        )
    )

    thread_id = str(
        message.get(
            "thread_id",
            "",
        )
    )

    sender_email = str(
        message.get(
            "sender_email",
            "",
        )
    )

    subject = str(
        message.get(
            "subject",
            "",
        )
    )

    email_body = str(
        message.get(
            "email_body",
            "",
        )
    )

    if not message_id:

        return {
            "status": "SKIPPED",
            "reason": "Gmail message ID is missing.",
            "message_id": None,
        }

    # --------------------------------------------------------
    # ROUTING
    # --------------------------------------------------------

    if not is_finance_email(
        subject=subject,
        email_body=email_body,
    ):

        return {
            "status": "IGNORED",
            "reason": "No strong finance intent detected.",
            "message_id": message_id,
            "thread_id": thread_id,
            "sender_email": sender_email,
            "subject": subject,
        }

    # --------------------------------------------------------
    # FINANCE WORKFLOW
    # --------------------------------------------------------

    result = send_finance_email(
        sender_email=sender_email,
        subject=subject,
        email_body=email_body,
        reply_thread_id=thread_id,
        reply_message_id=message.get(
            "rfc_message_id"
        ),
        reply_references=message.get(
            "references"
        ),
        incoming_message_id=message_id,
        incoming_thread_id=thread_id,
        action_taken=(
            "Finance email automatically processed "
            "from the Gmail inbox."
        ),
    )

    return {
        "status": result.get(
            "status",
            "UNKNOWN",
        ),
        "message_id": message_id,
        "thread_id": thread_id,
        "sender_email": sender_email,
        "subject": subject,
        "result": result,
    }


# ============================================================
# PROCESS NEW INBOX EMAILS
# ============================================================

def process_new_inbox_emails(
    max_messages: int | None = None,
) -> dict[str, Any]:
    """
    Scan Gmail Inbox and process only new finance emails.

    Non-finance emails are ignored.
    Already audited messages are skipped.
    """

    inbox_messages = (
        list_business_inbox_messages(
            max_messages=max_messages
        )
    )

    processed_ids = (
        get_processed_message_ids()
    )

    results: list[dict[str, Any]] = []

    ignored_count = 0
    skipped_count = 0
    finance_count = 0
    answered_count = 0
    failed_count = 0
    exception_count = 0

    for message in inbox_messages:

        message_id = str(
            message.get(
                "message_id",
                "",
            )
        )

        if (
            message_id
            and message_id in processed_ids
        ):

            skipped_count += 1
            continue

        result = process_one_inbox_message(
            message
        )

        results.append(
            result
        )

        status = str(
            result.get(
                "status",
                "",
            )
        ).upper()

        if status == "IGNORED":

            ignored_count += 1

        elif status == "SENT":

            finance_count += 1
            answered_count += 1

        elif status in {
            "SEND_FAILED",
            "NOT_SENT",
        }:

            finance_count += 1
            failed_count += 1
            exception_count += 1

        elif status == "SKIPPED":

            skipped_count += 1

    return {
        "status": "COMPLETED",
        "emails_scanned": len(
            inbox_messages
        ),
        "finance_emails_found": finance_count,
        "answered_count": answered_count,
        "failed_count": failed_count,
        "exception_count": exception_count,
        "ignored_count": ignored_count,
        "skipped_count": skipped_count,
        "results": results,
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = process_new_inbox_emails()

    print("=" * 70)
    print(
        "FINANCE EMAIL AI — INBOX PROCESSOR"
    )
    print("=" * 70)

    print(
        "Emails scanned:",
        result.get(
            "emails_scanned"
        ),
    )

    print(
        "Finance emails:",
        result.get(
            "finance_emails_found"
        ),
    )

    print(
        "Answered:",
        result.get(
            "answered_count"
        ),
    )

    print(
        "Exceptions:",
        result.get(
            "exception_count"
        ),
    )

    print(
        "Ignored:",
        result.get(
            "ignored_count"
        ),
    )

    print(
        "Already processed:",
        result.get(
            "skipped_count"
        ),
    )

    print("\nRESULTS:")

    for item in result.get(
        "results",
        [],
    ):

        print(
            item.get(
                "status"
            ),
            "|",
            item.get(
                "subject"
            ),
        )

    print("=" * 70)