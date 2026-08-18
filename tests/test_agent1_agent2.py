from app.agents.finance_email_agent import analyze_finance_email
from app.agents.verification_agent import verify_finance_response


def main():
    original_email = {
        "sender_email": "customer@example.com",
        "subject": "Question about my outstanding invoice",
        "email_body": (
            "Hello, I am ABC 001 Traders. "
            "Please tell me how much I currently owe "
            "and whether any of my invoices are overdue."
        ),
    }

    print("=" * 70)
    print("AGENT 1 → AGENT 2 FINAL CORRECT-RESPONSE REGRESSION TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1 — Run Agent 1
    # ---------------------------------------------------------

    print("\n[1] Running Agent 1...")

    agent1_result = analyze_finance_email(
        sender_email=original_email["sender_email"],
        subject=original_email["subject"],
        email_body=original_email["email_body"],
    )

    print("\nAgent 1 Status:")
    print(agent1_result["status"])

    print("\nCustomer:")
    print(
        agent1_result.get("customer_name"),
        agent1_result.get("customer_id"),
    )

    print("\nAgent 1 Proposed Response:")
    print("-" * 70)
    print(agent1_result["proposed_response"])

    # ---------------------------------------------------------
    # STEP 2 — Run Agent 2
    # ---------------------------------------------------------

    print("\n[2] Running Agent 2...")

    verification_result = verify_finance_response(
        original_email=original_email,
        agent1_result=agent1_result,
    )

    print("\nAgent 2 Status:")
    print(verification_result["status"])

    print("\nAgent 2 Decision:")
    print("=" * 70)
    print(verification_result["decision"])
    print("=" * 70)

    print("\nAgent 2 Verification:")
    print(
        verification_result["verification"]
    )

    # ---------------------------------------------------------
    # STEP 3 — Deterministic verification
    # ---------------------------------------------------------

    print("\n[3] Deterministic Verification:")
    print("-" * 70)

    deterministic = verification_result.get(
        "deterministic_verification",
        {},
    )

    print(deterministic)

    # ---------------------------------------------------------
    # STEP 4 — Final regression assertion
    # ---------------------------------------------------------

    print("\n[4] FINAL REGRESSION EXPECTATION")
    print("-" * 70)

    if verification_result["decision"] == "APPROVED":
        print(
            "PASS: Correct Agent 1 response was approved by Agent 2."
        )
    else:
        print(
            "FAIL: Correct Agent 1 response was incorrectly rejected."
        )


if __name__ == "__main__":
    main()