from __future__ import annotations

import math
from typing import Dict, List, Tuple


class CognitiveEngine:
    def score_user(self, income: float, activity: float, transactions: int, defaults: int) -> Tuple[float, List[str]]:
        activity = min(max(activity, 0.0), 1.0)
        transactions = max(transactions, 0)
        defaults = max(defaults, 0)

        # Lightweight explainable scoring function shaped like logistic regression.
        linear = (
            -0.00008 * income
            + 0.04 * transactions
            - 2.2 * activity
            + 0.8 * defaults
            + 0.35
        )
        risk = 1.0 / (1.0 + math.exp(-linear))
        risk = min(max(risk, 0.0), 1.0)

        reasons: List[str] = []
        if income < 3000:
            reasons.append("income is below resilience threshold")
        if activity < 0.35:
            reasons.append("activity level is low")
        if transactions > 12:
            reasons.append("transaction volume indicates instability")
        if defaults > 0:
            reasons.append("prior default events exist")
        if not reasons:
            reasons.append("financial behavior is stable")

        return risk, reasons

    def score_payload(self, payload: Dict[str, float]) -> Tuple[float, List[str]]:
        return self.score_user(
            income=float(payload.get("income", 0.0)),
            activity=float(payload.get("activity", 0.0)),
            transactions=int(payload.get("transactions", 0)),
            defaults=int(payload.get("defaults", 0)),
        )


def predict_single_user_risk(
    income: float,
    activity: float,
    transaction_variability: float,
) -> float:
    """Probabilistic risk score in [0, 1] using normalized features and sigmoid.

    Effects are monotonic by design:
    - lower income -> higher risk
    - lower activity -> higher risk
    - higher variability -> higher risk
    """
    income_risk, activity_risk, variability_risk = normalized_risk_factors(
        income=income,
        activity=activity,
        transaction_variability=transaction_variability,
    )

    # Logistic probability with interpretable weights.
    bias = -0.25
    linear = (
        bias
        + 1.35 * income_risk
        + 1.10 * activity_risk
        + 0.95 * variability_risk
    )
    probability = 1.0 / (1.0 + math.exp(-linear))
    return min(max(float(probability), 0.0), 1.0)


def normalized_risk_factors(
    income: float,
    activity: float,
    transaction_variability: float,
) -> Tuple[float, float, float]:
    """Return normalized risk-oriented factors for income, activity, variability."""
    income = max(float(income), 0.0)
    activity = min(max(float(activity), 0.0), 1.0)
    transaction_variability = max(float(transaction_variability), 0.0)

    income_floor = 1500.0
    income_ceiling = 9000.0
    income_safe_span = max(income_ceiling - income_floor, 1.0)
    income_component = 1.0 - min(max((income - income_floor) / income_safe_span, 0.0), 1.0)
    activity_component = 1.0 - activity

    variability_cap = 1.0
    variability_component = min(transaction_variability / variability_cap, 1.0)
    return (
        min(max(income_component, 0.0), 1.0),
        min(max(activity_component, 0.0), 1.0),
        min(max(variability_component, 0.0), 1.0),
    )


def risk_probability_breakdown(
    income: float,
    activity: float,
    transaction_variability: float,
) -> Dict[str, float]:
    """Return normalized factors and final probabilistic risk for explainability."""
    income_risk, activity_risk, variability_risk = normalized_risk_factors(
        income=income,
        activity=activity,
        transaction_variability=transaction_variability,
    )
    probability = predict_single_user_risk(
        income=income,
        activity=activity,
        transaction_variability=transaction_variability,
    )
    return {
        "income_risk_factor": income_risk,
        "activity_risk_factor": activity_risk,
        "variability_risk_factor": variability_risk,
        "probability_risk": probability,
    }
