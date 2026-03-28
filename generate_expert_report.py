from __future__ import annotations

import os

from dccfe import generate_analyst_report_from_pipeline, run_refined_dccfe_pipeline


def main() -> None:
    report = run_refined_dccfe_pipeline(print_output=False, return_full_report=True)
    user_id = report["system_summary"].get("critical_node") or report["node_results"][0]["node_id"]

    result = generate_analyst_report_from_pipeline(
        report=report,
        user_id=str(user_id),
        api_key=os.getenv("GROQ_API_KEY"),
    )

    print("\n=== EXPERT RISK ASSESSMENT ===\n")
    print(result)


if __name__ == "__main__":
    main()
