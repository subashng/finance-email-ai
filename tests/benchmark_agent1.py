import statistics
import time

from app.agents.finance_email_agent import analyze_finance_email


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
    print("AGENT 1 PERFORMANCE BENCHMARK")
    print("=" * 70)

    times = []

    for run_number in range(1, RUNS + 1):

        start = time.perf_counter()

        result = analyze_finance_email(
            sender_email=SENDER_EMAIL,
            subject=SUBJECT,
            email_body=EMAIL_BODY,
        )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        times.append(elapsed_ms)

        performance = result.get(
            "performance",
            {},
        )

        print(
            f"\nRUN {run_number}"
        )

        print(
            f"Status            : "
            f"{result.get('status')}"
        )

        print(
            f"Identification     : "
            f"{result.get('identification_method')}"
        )

        print(
            f"Total              : "
            f"{elapsed_ms:.2f} ms"
        )

        print(
            f"Response LLM       : "
            f"{performance.get('response_llm_ms')} ms"
        )

        print(
            f"RAG                : "
            f"{performance.get('rag_ms')} ms"
        )

        print(
            f"SQL Invoices       : "
            f"{performance.get('sql_invoices_ms')} ms"
        )

        print(
            f"SQL Outstanding    : "
            f"{performance.get('sql_outstanding_ms')} ms"
        )

        print(
            f"SQL Aging          : "
            f"{performance.get('sql_aging_ms')} ms"
        )

    median_ms = statistics.median(
        times
    )

    average_ms = statistics.mean(
        times
    )

    minimum_ms = min(times)
    maximum_ms = max(times)

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"Runs               : {RUNS}"
    )

    print(
        f"Average            : {average_ms:.2f} ms"
    )

    print(
        f"Median             : {median_ms:.2f} ms"
    )

    print(
        f"Minimum            : {minimum_ms:.2f} ms"
    )

    print(
        f"Maximum            : {maximum_ms:.2f} ms"
    )

    print(
        f"Median Seconds     : "
        f"{median_ms / 1000:.2f} s"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()