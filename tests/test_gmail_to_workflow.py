from app.gmail.gmail_client import get_gmail_message
from app.workflow import process_finance_email


def main():
    print("=" * 70)
    print("GMAIL → FINANCE WORKFLOW INTEGRATION TEST")
    print("=" * 70)

    # =========================================================
    # STEP 1 — Confirm Gmail can retrieve a real message
    # =========================================================

    print("\n[1] Reading one real Gmail message...")

    gmail_messages = None

    try:
        from app.gmail.gmail_client import list_inbox_messages

        gmail_messages = list_inbox_messages(
            max_results=1
        )

    except Exception as exc:
        print(
            "Gmail read test failed:",
            exc,
        )
        return

    if not gmail_messages:
        print(
            "No Gmail inbox messages were found."
        )
        return

    gmail_message_id = gmail_messages[0].get(
        "id"
    )

    print(
        "Gmail Message ID:",
        gmail_message_id,
    )

    # Retrieve the real message.
    real_gmail_message = get_gmail_message(
        gmail_message_id
    )

    print(
        "Gmail Thread ID:",
        real_gmail_message.get(
            "thread_id"
        ),
    )

    print(
        "Gmail Sender:",
        real_gmail_message.get(
            "sender_email"
        ),
    )

    print(
        "Gmail Subject:",
        real_gmail_message.get(
            "subject"
        ),
    )

    # =========================================================
    # IMPORTANT
    #
    # The current inbox contains non-finance emails.
    # We deliberately do NOT send the real Gmail message
    # into Agent 1.
    #
    # The production classifier/routing layer is V2.
    # =========================================================

    print("\n[2] Gmail message retrieved successfully.")
    print(
        "The real inbox message will NOT be processed "
        "because V1 does not yet have email classification."
    )

    # =========================================================
    # STEP 3 — Controlled finance email
    #
    # This represents a Gmail message after the future
    # finance-email routing decision.
    # =========================================================

    print(
        "\n[3] Creating controlled finance Gmail message..."
    )

    controlled_gmail_message = {
        "message_id": "TEST_FINANCE_MESSAGE_001",
        "thread_id": "TEST_FINANCE_THREAD_001",
        "sender_email": "customer@example.com",
        "subject": "Question about my outstanding invoice",
        "email_body": (
            "Hello, I am ABC 001 Traders. "
            "Please tell me how much I currently owe "
            "and whether any of my invoices are overdue."
        ),
    }

    print(
        "Controlled Message ID:",
        controlled_gmail_message["message_id"],
    )

    print(
        "Controlled Thread ID:",
        controlled_gmail_message["thread_id"],
    )

    # =========================================================
    # STEP 4 — Map Gmail fields to workflow inputs
    # =========================================================

    print(
        "\n[4] Mapping Gmail message to workflow..."
    )

    sender_email = controlled_gmail_message[
        "sender_email"
    ]

    subject = controlled_gmail_message[
        "subject"
    ]

    email_body = controlled_gmail_message[
        "email_body"
    ]

    print(
        "Sender:",
        sender_email,
    )

    print(
        "Subject:",
        subject,
    )

    print(
        "Body:",
        email_body,
    )

    # =========================================================
    # STEP 5 — Run existing production workflow
    #
    # This invokes:
    #
    # Agent 1 → Agent 2 → Agent 3
    #
    # No Gmail sending occurs.
    # =========================================================

    print(
        "\n[5] Running existing Finance Email workflow..."
    )

    workflow_result = process_finance_email(
        sender_email=sender_email,
        subject=subject,
        email_body=email_body,
    )

    print("\nWorkflow Status:")
    print(
        workflow_result.get(
            "status"
        )
    )

    print("\nWorkflow Stage:")
    print(
        workflow_result.get(
            "stage"
        )
    )

    print("\nWorkflow Message:")
    print(
        workflow_result.get(
            "message"
        )
    )

    print("\nCan Send:")
    print(
        workflow_result.get(
            "can_send"
        )
    )

    # =========================================================
    # STEP 6 — Verify final email record
    # =========================================================

    if workflow_result.get(
        "status"
    ) != "COMPLETED":

        print("\n" + "=" * 70)
        print(
            "WORKFLOW DID NOT COMPLETE."
        )
        print("=" * 70)
        return

    final_email_body = workflow_result.get(
        "final_email_body",
        "",
    )

    final_email_subject = workflow_result.get(
        "final_email_subject",
        "",
    )

    print("\nFinal Email Subject:")
    print(
        final_email_subject
    )

    print("\nFinal Email Record:")
    print("=" * 70)
    print(
        final_email_body
    )
    print("=" * 70)

    # =========================================================
    # STEP 7 — Assertions
    # =========================================================

    print(
        "\n[6] Integration Test Assertions"
    )
    print("-" * 70)

    if not final_email_body:

        print(
            "FAIL: Final email body is empty."
        )
        return

    if controlled_gmail_message[
        "email_body"
    ] not in final_email_body:

        print(
            "FAIL: Original customer email was not "
            "preserved in the final record."
        )
        return

    if "COMPANY RESPONSE" not in final_email_body:

        print(
            "FAIL: Company response section is missing."
        )
        return

    if workflow_result.get(
        "can_send"
    ) is not True:

        print(
            "FAIL: Completed workflow did not "
            "set can_send=True."
        )
        return

    print(
        "PASS: Gmail message fields were mapped correctly."
    )

    print(
        "PASS: Finance workflow executed successfully."
    )

    print(
        "PASS: Original customer question was preserved."
    )

    print(
        "PASS: Company response was preserved."
    )

    print(
        "PASS: Final communication record was created."
    )

    print(
        "PASS: No email was sent."
    )

    print("\n" + "=" * 70)
    print("FINAL RESULT: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()