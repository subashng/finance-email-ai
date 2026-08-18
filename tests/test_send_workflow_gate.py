from app.send_workflow import send_finance_email


def main():
    print("=" * 70)
    print("SEND WORKFLOW SAFETY GATE TEST")
    print("=" * 70)

    print("\nThis test verifies that an unapproved workflow cannot send email.")

    # ---------------------------------------------------------
    # NOTE:
    # We do NOT call Gmail directly in this test.
    # The test uses an invalid/ambiguous customer scenario so
    # the finance workflow should stop before sending.
    # ---------------------------------------------------------

    result = send_finance_email(
        sender_email="customer@example.com",
        subject="Question about invoice",
        email_body="",
    )

    print("\nSend Workflow Result:")
    print("-" * 70)
    print(result)

    print("\n[TEST EXPECTATION]")
    print("-" * 70)

    if result.get("status") != "SENT":
        print(
            "PASS: Email was not sent because the workflow "
            "did not complete successfully."
        )
    else:
        print(
            "FAIL: Email was sent even though the workflow "
            "should not have completed."
        )


if __name__ == "__main__":
    main()