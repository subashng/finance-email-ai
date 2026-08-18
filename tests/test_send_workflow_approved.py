from app.send_workflow import send_finance_email


def main():
    print("=" * 70)
    print("APPROVED WORKFLOW → GMAIL SELF-SEND TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Controlled finance email
    # ---------------------------------------------------------

    sender_email = "ngsubasht@gmail.com"

    subject = "Finance Email AI Controlled Send Test"

    email_body = (
        "Hello, I am ABC 001 Traders. "
        "Please tell me how much I currently owe "
        "and whether any of my invoices are overdue."
    )

    print("\n[1] Running approved Finance Email workflow...")

    result = send_finance_email(
        sender_email=sender_email,
        subject=subject,
        email_body=email_body,
        reply_thread_id=None,
        reply_message_id=None,
        reply_references=None,
    )

    print("\nSend Workflow Status:")
    print(result.get("status"))

    print("\nStage:")
    print(result.get("stage"))

    print("\nMessage:")
    print(result.get("message"))

    print("\nRecipient:")
    print(result.get("recipient_email"))

    print("\nThread ID:")
    print(result.get("thread_id"))

    print("\nGmail Message ID:")
    print(result.get("gmail_message_id"))

    print("\nSubject:")
    print(result.get("subject"))

    print("\n[2] TEST EXPECTATION")
    print("-" * 70)

    if result.get("status") == "SENT":

        print(
            "PASS: Approved workflow sent the controlled "
            "test email successfully."
        )

    else:

        print(
            "FAIL: Approved workflow did not send "
            "the controlled test email."
        )

    print("\nNOTE:")
    print(
        "This test sends only to the configured project "
        "Gmail account, not to a customer."
    )


if __name__ == "__main__":
    main()