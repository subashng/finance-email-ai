from typing import Any, Callable


# ============================================================
# TYPES
# ============================================================

EvaluationRunner = Callable[
    [str],
    dict[str, Any],
]


# ============================================================
# EVALUATE ONE CASE
# ============================================================

def evaluate_case(
    case: dict[str, Any],
    runner: EvaluationRunner,
) -> dict[str, Any]:
    """
    Run one evaluation case and compare the observed result
    with the expected result.
    """

    case_id = str(
        case.get(
            "case_id",
            "UNKNOWN",
        )
    )

    description = str(
        case.get(
            "description",
            "",
        )
    )

    expected_status = case.get(
        "expected_status"
    )

    expected_stage = case.get(
        "expected_stage"
    )

    expected_decision = case.get(
        "expected_decision"
    )

    # --------------------------------------------------------
    # Run case
    # --------------------------------------------------------

    try:

        result = runner(
            case_id
        )

    except Exception as exc:

        return {
            "case_id": case_id,
            "description": description,
            "passed": False,
            "expected": {
                "status": expected_status,
                "stage": expected_stage,
                "decision": expected_decision,
            },
            "actual": {},
            "checks": [],
            "failures": [
                f"Evaluation runner error: {exc}"
            ],
        }

    # --------------------------------------------------------
    # Actual values
    # --------------------------------------------------------

    actual_status = result.get(
        "status"
    )

    actual_stage = result.get(
        "stage"
    )

    actual_decision = None

    agent2_result = result.get(
        "agent2_result"
    )

    if isinstance(
        agent2_result,
        dict,
    ):

        actual_decision = agent2_result.get(
            "decision"
        )

    checks: list[str] = []
    failures: list[str] = []

    # --------------------------------------------------------
    # Status check
    # --------------------------------------------------------

    if expected_status is not None:

        if actual_status == expected_status:

            checks.append(
                "Status matched."
            )

        else:

            failures.append(
                "Status mismatch: "
                f"expected={expected_status}, "
                f"actual={actual_status}."
            )

    # --------------------------------------------------------
    # Stage check
    # --------------------------------------------------------

    if expected_stage is not None:

        if actual_stage == expected_stage:

            checks.append(
                "Stage matched."
            )

        else:

            failures.append(
                "Stage mismatch: "
                f"expected={expected_stage}, "
                f"actual={actual_stage}."
            )

    # --------------------------------------------------------
    # Agent 2 decision check
    # --------------------------------------------------------

    if expected_decision is not None:

        if actual_decision == expected_decision:

            checks.append(
                "Agent 2 decision matched."
            )

        else:

            failures.append(
                "Agent 2 decision mismatch: "
                f"expected={expected_decision}, "
                f"actual={actual_decision}."
            )

    passed = not failures

    return {
        "case_id": case_id,
        "description": description,
        "passed": passed,
        "expected": {
            "status": expected_status,
            "stage": expected_stage,
            "decision": expected_decision,
        },
        "actual": {
            "status": actual_status,
            "stage": actual_stage,
            "decision": actual_decision,
        },
        "checks": checks,
        "failures": failures,
    }


# ============================================================
# RUN FULL EVALUATION SUITE
# ============================================================

def run_evaluation_suite(
    cases: list[dict[str, Any]],
    runner: EvaluationRunner,
) -> dict[str, Any]:
    """
    Run all evaluation cases and generate a clean summary.
    """

    results: list[dict[str, Any]] = []

    for case in cases:

        result = evaluate_case(
            case=case,
            runner=runner,
        )

        results.append(
            result
        )

    total_cases = len(
        results
    )

    passed_cases = sum(
        1
        for result in results
        if result.get("passed") is True
    )

    failed_cases = (
        total_cases - passed_cases
    )

    pass_rate = (
        (passed_cases / total_cases) * 100
        if total_cases
        else 0.0
    )

    # --------------------------------------------------------
    # Stage summary
    # --------------------------------------------------------

    stage_summary: dict[str, int] = {}

    for result in results:

        actual_stage = (
            result.get(
                "actual",
                {}
            ).get(
                "stage"
            )
        )

        if actual_stage:

            stage_summary[actual_stage] = (
                stage_summary.get(
                    actual_stage,
                    0,
                )
                + 1
            )

    # --------------------------------------------------------
    # Decision summary
    # --------------------------------------------------------

    decision_summary: dict[str, int] = {}

    for result in results:

        actual_decision = (
            result.get(
                "actual",
                {}
            ).get(
                "decision"
            )
        )

        if actual_decision:

            decision_summary[actual_decision] = (
                decision_summary.get(
                    actual_decision,
                    0,
                )
                + 1
            )

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "pass_rate": round(
            pass_rate,
            2,
        ),
        "all_passed": (
            total_cases > 0
            and failed_cases == 0
        ),
        "stage_summary": stage_summary,
        "decision_summary": decision_summary,
        "failed_case_ids": [
            result["case_id"]
            for result in results
            if not result.get(
                "passed"
            )
        ],
        "results": results,
    }


# ============================================================
# PRINT CLEAN REPORT
# ============================================================

def print_evaluation_summary(
    evaluation_result: dict[str, Any],
) -> None:
    """
    Print a clean human-readable evaluation report.
    """

    print("=" * 70)
    print("FINANCE EMAIL AI — EVALUATION REPORT")
    print("=" * 70)

    print(
        f"\nTotal Cases   : "
        f"{evaluation_result.get('total_cases', 0)}"
    )

    print(
        f"Passed Cases  : "
        f"{evaluation_result.get('passed_cases', 0)}"
    )

    print(
        f"Failed Cases  : "
        f"{evaluation_result.get('failed_cases', 0)}"
    )

    print(
        f"Pass Rate     : "
        f"{evaluation_result.get('pass_rate', 0.0)}%"
    )

    print(
        f"All Passed    : "
        f"{evaluation_result.get('all_passed', False)}"
    )

    # --------------------------------------------------------
    # Stage summary
    # --------------------------------------------------------

    print("\nStage Summary:")
    print("-" * 70)

    for stage, count in sorted(
        evaluation_result.get(
            "stage_summary",
            {},
        ).items()
    ):

        print(
            f"{stage:<20} {count}"
        )

    # --------------------------------------------------------
    # Decision summary
    # --------------------------------------------------------

    print("\nDecision Summary:")
    print("-" * 70)

    for decision, count in sorted(
        evaluation_result.get(
            "decision_summary",
            {},
        ).items()
    ):

        print(
            f"{decision:<20} {count}"
        )

    # --------------------------------------------------------
    # Case summary
    # --------------------------------------------------------

    print("\nCase Results:")
    print("-" * 70)

    for result in evaluation_result.get(
        "results",
        [],
    ):

        status = (
            "PASS"
            if result.get(
                "passed"
            )
            else "FAIL"
        )

        actual = result.get(
            "actual",
            {},
        )

        print(
            f"{status:<5} "
            f"{result.get('case_id'):<12} "
            f"{actual.get('stage', '-'):<15} "
            f"{actual.get('decision', '-'):<10} "
            f"{result.get('description', '')}"
        )

        for failure in result.get(
            "failures",
            [],
        ):

            print(
                f"      FAILURE: {failure}"
            )

    # --------------------------------------------------------
    # Failed cases
    # --------------------------------------------------------

    failed_ids = evaluation_result.get(
        "failed_case_ids",
        [],
    )

    print("\nFailed Case IDs:")

    if failed_ids:

        for case_id in failed_ids:

            print(
                f"  - {case_id}"
            )

    else:

        print(
            "  NONE"
        )

    print("\n" + "=" * 70)

    if evaluation_result.get(
        "all_passed"
    ):

        print(
            "FINAL RESULT: PASS"
        )

    else:

        print(
            "FINAL RESULT: FAIL"
        )

    print("=" * 70)


# ============================================================
# DIRECT MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Finance Email Evaluation module loaded successfully."
    )