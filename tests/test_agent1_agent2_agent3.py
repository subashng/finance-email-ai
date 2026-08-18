from app.agents.finance_email_agent import analyze_finance_email
from app.agents.verification_agent import verify_finance_response
from app.agents.finalization_agent import finalize_customer_email


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
    print("AGENT 1 → AGENT 2 → AGENT 3 SEQUENTIAL TEST")
    print("=" * 70)

    # =========================================================
    # STEP 1 — AGENT 1
    # =========================================================

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

    print("\nAgent 1 Proposed Response:")
    print("-" * 70)
    print(
        agent1_result.get(
            "proposed_response",
            "",
        )
    )

    # =========================================================
    # SAFETY CHECK — AGENT 1
    # =========================================================

    if agent1_result.get("status") != "COMPLETED":

        print("\n" + "=" * 70)
        print("FAIL: Agent 1 did not complete.")
        print("=" * 70)
        return

    # =========================================================
    # STEP 2 — AGENT 2
    # =========================================================

    print("\n[2] Running Agent 2...")

    verification_result = verify_finance_response(
        original_email=original_email,
        agent1_result=agent1_result,
    )

    print("\nAgent 2 Status:")
    print(
        verification_result.get(
            "status"
        )
    )

    print("\nAgent 2 Decision:")
    print("=" * 70)
    print(
        verification_result.get(
            "decision"
        )
    )
    print("=" * 70)

    print("\nAgent 2 Verification:")
    print(
        verification_result.get(
            "verification",
            "",
        )
    )

    # =========================================================
    # STEP 3 — DETERMINISTIC VERIFICATION
    # =========================================================

    print("\n[3] Deterministic Verification:")
    print("-" * 70)

    deterministic = verification_result.get(
        "deterministic_verification",
        {},
    )

    print(deterministic)

    # =========================================================
    # STEP 4 — SEQUENTIAL GATE
    # =========================================================

    print("\n[4] Agent 2 → Agent 3 Sequential Gate")
    print("-" * 70)

    agent2_decision = str(
        verification_result.get(
            "decision",
            "",
        )
    ).strip().upper()

    print(
        "Agent 2 Decision:",
        agent2_decision,
    )

    if agent2_decision != "APPROVED":

        print(
            "\nAgent 2 did not approve the response."
        )
        print(
            "Agent 3 MUST NOT execute."
        )

        print("\n" + "=" * 70)
        print(
            "FINAL RESULT: PASS — "
            "Sequential safety gate correctly stopped the workflow."
        )
        print("=" * 70)

        return

    print(
        "Agent 2 approved the response."
    )
    print(
        "Agent 3 is now allowed to execute."
    )

    # =========================================================
    # STEP 5 — AGENT 3
    # =========================================================

    print("\n[5] Running Agent 3...")

    finalization_result = finalize_customer_email(
        original_email=original_email,
        agent1_result=agent1_result,
        agent2_result=verification_result,
    )

    print("\nAgent 3 Status:")
    print(
        finalization_result.get(
            "status"
        )
    )

    print("\nCan Send:")
    print(
        finalization_result.get(
            "can_send"
        )
    )

    print("\nFinal Email Subject:")
    print(
        finalization_result.get(
            "final_email_subject"
        )
    )

    print("\nComplete Email Record:")
    print("=" * 70)
    print(
        finalization_result.get(
            "final_email_body",
            "",
        )
    )
    print("=" * 70)

    # =========================================================
    # STEP 6 — FINAL ASSERTIONS
    # =========================================================

    print("\n[6] FINAL SEQUENTIAL TEST")
    print("-" * 70)

    if (
        finalization_result.get("status")
        != "FINALIZED"
    ):
        print(
            "FAIL: Agent 3 did not finalize "
            "the approved response."
        )
        return

    if (
        finalization_result.get("can_send")
        is not True
    ):
        print(
            "FAIL: Agent 3 did not mark "
            "the approved response as sendable."
        )
        return

    final_email_body = finalization_result.get(
        "final_email_body",
        "",
    )

    # Verify original customer message exists
    if original_email["email_body"] not in final_email_body:

        print(
            "FAIL: Original customer question "
            "was not preserved."
        )
        return

    # Verify approved response exists
    proposed_response = agent1_result.get(
        "proposed_response",
        "",
    )

    if proposed_response not in final_email_body:

        print(
            "FAIL: Approved company response "
            "was not preserved."
        )
        return

    # Verify both parts exist
    if "CUSTOMER EMAIL" not in final_email_body:

        print(
            "FAIL: Customer email section missing."
        )
        return

    if "COMPANY RESPONSE" not in final_email_body:

        print(
            "FAIL: Company response section missing."
        )
        return

    print(
        "PASS: Agent 1 → Agent 2 → Agent 3 "
        "sequential workflow completed successfully."
    )

    print(
        "PASS: Original customer question preserved."
    )

    print(
        "PASS: Approved company response preserved."
    )

    print(
        "PASS: Final communication record created."
    )

    print(
        "PASS: Email is marked ready for sending."
    )

    print("\n" + "=" * 70)
    print(
        "FINAL RESULT: PASS"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()