from __future__ import annotations

from dccfe import ScalingConfig, run_full_scaling_mode


def main() -> None:
    config = ScalingConfig(
        user_count=500,
        network_mode="preferential_attachment",
        average_degree=8,
        alpha=0.22,
        steps=6,
        intervention_top_k=25,
        critical_report_count=5,
    )

    result = run_full_scaling_mode(config=config)

    print("\n=== DCCFE FULL SCALING MODE ===")
    print(result["system_summary"])
    print("Top risky nodes:")
    for row in result["top_risky_nodes"][:5]:
        print(row)
    print("Intervention:", result["intervention"])
    print("Stability:", result["stability"]["classification"], result["stability"]["average_risk"])


if __name__ == "__main__":
    main()
