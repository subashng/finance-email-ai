from app.agents.finance_email_agent import (
    analyze_finance_email,
)
from app.agents.verification_agent import (
    verify_finance_response,
)


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
    print("AGENT 2 EXPLICIT OVERDUE APPROVAL TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Step 1 — Run Agent 1 only to obtain the financial evidence
    # ---------------------------------------------------------

    print("\n[1] Running Agent 1...")

    agent1_result = analyze_finance_email(
        sender_email=original_email["sender_email"],
        subject=original_email["subject"],
        email_body=original_email["email_body"],
    )

    print("\nAgent 1 Status:")
    print(agent1_result.get("status"))

    print("\nCustomer:")
    print(
        agent1_result.get("customer_name"),
        agent1_result.get("customer_id"),
    )

    # ---------------------------------------------------------
    # Step 2 — Replace only the customer-facing response
    #
    # The financial evidence from Agent 1 remains unchanged.
    # We are testing Agent 2 with an explicitly correct response.
    # ---------------------------------------------------------

    correct_response = """Dear ABC 001 Traders,

Your total outstanding balance is ₹222,125.41.

The following invoices are currently outstanding:

INV2026000103 - ₹112,578.91 - Aging: 120 days (90+ Days) - OVERDUE
INV2026000102 - ₹31,866.68 - Aging: 44 days (31-60 Days) - OVERDUE
INV2026000101 - ₹77,679.82 - Aging: 28 days (1-30 Days) - OVERDUE

All three invoices are currently overdue.

Best regards,
Finance Customer Support"""

    agent1_result["proposed_response"] = correct_response

    print("\n[2] Controlled Customer-Facing Response")
    print("-" * 70)
    print(agent1_result["proposed_response"])

    # ---------------------------------------------------------
    # Step 3 — Run Agent 2
    # ---------------------------------------------------------

    print("\n[3] Running Agent 2...")

    verification_result = verify_finance_response(
        original_email=original_email,
        agent1_result=agent1_result,
    )

    print("\nAgent 2 Status:")
    print(
        verification_result.get("status")
    )

    print("\nAgent 2 Decision:")
    print("=" * 70)
    print(
        verification_result.get("decision")
    )
    print("=" * 70)

    print("\nAgent 2 Verification:")
    print(
        verification_result.get(
            "verification",
            "",
        )
    )

    # ---------------------------------------------------------
    # Step 4 — Test expectation
    # ---------------------------------------------------------

    print("\n[4] TEST EXPECTATION")
    print("-" * 70)

    if verification_result.get("decision") == "APPROVED":

        print(
            "PASS: Agent 2 approved the "
            "explicitly correct overdue response."
        )

    else:

        print(
            "FAIL: Agent 2 rejected an "
            "explicitly correct overdue response."
        )


if __name__ == "__main__":
    main()