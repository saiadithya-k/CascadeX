from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, List, Tuple

import numpy as np

from .cognitive import predict_single_user_risk


@dataclass
class MLRiskModel:
    model: Any
    scaler: Any
    feature_names: List[str]
    test_accuracy: float
    backend: str


def generate_dataset(
    n_samples: int = 400,
    random_seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Generate synthetic financial samples and binary risk targets."""
    n_samples = min(max(int(n_samples), 200), 500)
    rng = np.random.default_rng(random_seed)

    income = rng.uniform(1200.0, 9500.0, size=n_samples)
    activity = rng.uniform(0.0, 1.0, size=n_samples)
    variability = rng.uniform(0.0, 1.0, size=n_samples)

    x = np.column_stack([income, activity, variability])

    # Target rule: high risk if low income OR low activity OR high variability.
    y = (
        (income < 3000.0)
        | (activity < 0.35)
        | (variability > 0.65)
    ).astype(int)

    # Add small label noise for realism.
    flip_idx = rng.choice(n_samples, size=max(1, n_samples // 25), replace=False)
    y[flip_idx] = 1 - y[flip_idx]

    features = ["income", "activity", "transaction_variability"]
    return x, y, features


def train_model(
    x: np.ndarray | None = None,
    y: np.ndarray | None = None,
    random_seed: int = 42,
) -> MLRiskModel:
    """Train logistic regression with normalized inputs and report test accuracy."""
    if x is None or y is None:
        x, y, feature_names = generate_dataset(random_seed=random_seed)
    else:
        feature_names = ["income", "activity", "transaction_variability"]

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=int)

    try:
        LogisticRegression = import_module("sklearn.linear_model").LogisticRegression
        accuracy_score = import_module("sklearn.metrics").accuracy_score
        train_test_split = import_module("sklearn.model_selection").train_test_split
        StandardScaler = import_module("sklearn.preprocessing").StandardScaler

        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=0.2,
            random_state=random_seed,
            stratify=y,
        )

        scaler = StandardScaler()
        x_train_scaled = scaler.fit_transform(x_train)
        x_test_scaled = scaler.transform(x_test)

        model = LogisticRegression(max_iter=1000, random_state=random_seed)
        model.fit(x_train_scaled, y_train)
        y_pred = model.predict(x_test_scaled)
        acc = float(accuracy_score(y_test, y_pred))

        return MLRiskModel(
            model=model,
            scaler=scaler,
            feature_names=feature_names,
            test_accuracy=acc,
            backend="scikit-learn",
        )

    except Exception:
        # Fallback logistic regression trainer for environments without scikit-learn wheels.
        scaler = _SimpleStandardScaler()
        x_train, x_test, y_train, y_test = _train_test_split_np(x, y, test_size=0.2, seed=random_seed)
        x_train_scaled = scaler.fit_transform(x_train)
        x_test_scaled = scaler.transform(x_test)

        model = _NumpyLogisticRegression(lr=0.1, epochs=1200)
        model.fit(x_train_scaled, y_train)
        y_pred = model.predict(x_test_scaled)
        acc = float((y_pred == y_test).mean())

        return MLRiskModel(
            model=model,
            scaler=scaler,
            feature_names=feature_names,
            test_accuracy=acc,
            backend="numpy-fallback",
        )


def predict_risk(
    model_bundle: MLRiskModel,
    user_data: Dict[str, float],
) -> Dict[str, Any]:
    """Predict risk probability and provide feature contribution explainability."""
    income = float(user_data.get("income", 0.0))
    activity = float(user_data.get("activity", 0.0))
    variability = float(user_data.get("transaction_variability", 0.0))

    x = np.asarray([[income, activity, variability]], dtype=float)
    x_scaled = model_bundle.scaler.transform(x)

    proba = float(model_bundle.model.predict_proba(x_scaled)[0, 1])
    coefs = _extract_coefficients(model_bundle.model)

    # Contribution proxy in linear logit space.
    linear_parts = {
        model_bundle.feature_names[i]: float(coefs[i] * x_scaled[0, i])
        for i in range(len(model_bundle.feature_names))
    }
    dominant = max(linear_parts.items(), key=lambda kv: abs(kv[1]))[0]

    return {
        "ml_risk_probability": min(max(proba, 0.0), 1.0),
        "feature_contributions": linear_parts,
        "dominant_factor": dominant,
    }


def combine_risk(
    ml_risk: float,
    rule_risk: float,
    alpha: float = 0.55,
) -> float:
    """Hybrid risk score from ML and rule/sigmoid risk."""
    alpha = min(max(float(alpha), 0.4), 0.7)
    ml_risk = min(max(float(ml_risk), 0.0), 1.0)
    rule_risk = min(max(float(rule_risk), 0.0), 1.0)
    return min(max(alpha * ml_risk + (1.0 - alpha) * rule_risk, 0.0), 1.0)


def hybrid_predict_single_user(
    model_bundle: MLRiskModel,
    user_data: Dict[str, float],
    alpha: float = 0.55,
) -> Dict[str, Any]:
    rule_risk = predict_single_user_risk(
        income=float(user_data.get("income", 0.0)),
        activity=float(user_data.get("activity", 0.0)),
        transaction_variability=float(user_data.get("transaction_variability", 0.0)),
    )
    ml = predict_risk(model_bundle, user_data)
    final = combine_risk(float(ml["ml_risk_probability"]), rule_risk, alpha=alpha)

    return {
        "final_risk": final,
        "ml_risk": float(ml["ml_risk_probability"]),
        "rule_risk": rule_risk,
        "feature_contributions": ml["feature_contributions"],
        "dominant_factor": ml["dominant_factor"],
        "alpha": min(max(float(alpha), 0.4), 0.7),
    }


class _SimpleStandardScaler:
    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None

    def fit(self, x: np.ndarray) -> "_SimpleStandardScaler":
        self.mean_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0)
        self.scale_[self.scale_ == 0.0] = 1.0
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.scale_ is None:
            raise ValueError("Scaler not fitted")
        return (x - self.mean_) / self.scale_

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        return self.fit(x).transform(x)


class _NumpyLogisticRegression:
    def __init__(self, lr: float = 0.1, epochs: int = 1200) -> None:
        self.lr = lr
        self.epochs = epochs
        self.coef_: np.ndarray | None = None
        self.intercept_: float = 0.0

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        n_samples, n_features = x.shape
        self.coef_ = np.zeros(n_features, dtype=float)
        self.intercept_ = 0.0

        for _ in range(self.epochs):
            z = x @ self.coef_ + self.intercept_
            p = 1.0 / (1.0 + np.exp(-z))
            err = p - y

            grad_w = (x.T @ err) / n_samples
            grad_b = float(err.mean())

            self.coef_ -= self.lr * grad_w
            self.intercept_ -= self.lr * grad_b

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.coef_ is None:
            raise ValueError("Model not fitted")
        z = x @ self.coef_ + self.intercept_
        p1 = 1.0 / (1.0 + np.exp(-z))
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


def _train_test_split_np(
    x: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = np.arange(len(x))
    rng.shuffle(idx)
    split = int((1.0 - test_size) * len(x))
    tr = idx[:split]
    te = idx[split:]
    return x[tr], x[te], y[tr], y[te]


def _extract_coefficients(model: Any) -> np.ndarray:
    coef = getattr(model, "coef_", None)
    if coef is None:
        raise ValueError("Model coefficients unavailable")
    coef_arr = np.asarray(coef, dtype=float)
    if coef_arr.ndim == 2:
        return coef_arr[0]
    return coef_arr
