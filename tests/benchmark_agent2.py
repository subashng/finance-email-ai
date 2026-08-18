import statistics
import time

from app.agents.finance_email_agent import analyze_finance_email
from app.agents.verification_agent import verify_finance_response


RUNS = 3

SENDER_EMAIL = "customer@example.com"

SUBJECT = "Question about my outstanding invoice"

EMAIL_BODY = (
    "Hello, I am ABC 001 Traders. "
    "Please tell me how much I currently owe "
    "and whether any of my invoices are overdue."
)


def main():
    print("=" * 70)
    print("AGENT 2 PERFORMANCE BENCHMARK")
    print("=" * 70)

    total_times = []
    profiles = []

    for run_number in range(1, RUNS + 1):

        # ----------------------------------------------------
        # Generate Agent 1 result.
        # ----------------------------------------------------

        agent1_result = analyze_finance_email(
            sender_email=SENDER_EMAIL,
            subject=SUBJECT,
            email_body=EMAIL_BODY,
        )

        if agent1_result.get("status") != "COMPLETED":

            print(f"\nRUN {run_number}")
            print(
                "Agent 1 failed. "
                "Cannot benchmark Agent 2."
            )
            continue

        original_email = {
            "sender_email": SENDER_EMAIL,
            "subject": SUBJECT,
            "email_body": EMAIL_BODY,
        }

        # ----------------------------------------------------
        # Benchmark Agent 2.
        # ----------------------------------------------------

        start = time.perf_counter()

        result = verify_finance_response(
            original_email=original_email,
            agent1_result=agent1_result,
        )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        total_times.append(
            elapsed_ms
        )

        performance = result.get(
            "performance",
            {},
        )

        profiles.append(
            performance
        )

        print(f"\nRUN {run_number}")

        print(
            f"Status                  : "
            f"{result.get('status')}"
        )

        print(
            f"Decision                : "
            f"{result.get('decision')}"
        )

        print(
            f"Agent 2 Total           : "
            f"{elapsed_ms:.2f} ms"
        )

        print(
            f"SQL Invoices            : "
            f"{performance.get('sql_invoices_ms')} ms"
        )

        print(
            f"SQL Outstanding         : "
            f"{performance.get('sql_outstanding_ms')} ms"
        )

        print(
            f"SQL Aging               : "
            f"{performance.get('sql_aging_ms')} ms"
        )

        print(
            f"Deterministic Verify    : "
            f"{performance.get('deterministic_verification_ms')} ms"
        )

        print(
            f"Overdue Verify          : "
            f"{performance.get('overdue_verification_ms')} ms"
        )

        print(
            f"RAG                     : "
            f"{performance.get('rag_ms')} ms"
        )

        print(
            f"Semantic LLM            : "
            f"{performance.get('semantic_llm_ms')} ms"
        )

    if not total_times:

        print(
            "\nNo successful Agent 2 benchmark runs."
        )

        return

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("AGENT 2 BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"Successful Runs        : "
        f"{len(total_times)}"
    )

    print(
        f"Average Total          : "
        f"{statistics.mean(total_times):.2f} ms"
    )

    print(
        f"Median Total           : "
        f"{statistics.median(total_times):.2f} ms"
    )

    print(
        f"Minimum Total          : "
        f"{min(total_times):.2f} ms"
    )

    print(
        f"Maximum Total          : "
        f"{max(total_times):.2f} ms"
    )

    print(
        f"Median Seconds         : "
        f"{statistics.median(total_times) / 1000:.2f} s"
    )

    # --------------------------------------------------------
    # Median component timings
    # --------------------------------------------------------

    def median_component(
        key: str,
    ):
        values = [
            p.get(key)
            for p in profiles
            if p.get(key) is not None
        ]

        if not values:
            return None

        return round(
            statistics.median(values),
            2,
        )

    print("\nMedian Component Timings:")
    print("-" * 70)

    print(
        f"SQL Invoices           : "
        f"{median_component('sql_invoices_ms')} ms"
    )

    print(
        f"SQL Outstanding        : "
        f"{median_component('sql_outstanding_ms')} ms"
    )

    print(
        f"SQL Aging              : "
        f"{median_component('sql_aging_ms')} ms"
    )

    print(
        f"Deterministic Verify   : "
        f"{median_component('deterministic_verification_ms')} ms"
    )

    print(
        f"Overdue Verify         : "
        f"{median_component('overdue_verification_ms')} ms"
    )

    print(
        f"RAG                    : "
        f"{median_component('rag_ms')} ms"
    )

    print(
        f"Semantic LLM           : "
        f"{median_component('semantic_llm_ms')} ms"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()