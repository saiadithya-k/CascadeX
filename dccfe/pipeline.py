from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import networkx as nx
import pandas as pd

from .blockchain import SimpleHashBlockchain
from .cognitive import predict_single_user_risk
from .ml_risk import (
    MLRiskModel,
    combine_risk,
    generate_dataset,
    predict_risk,
    train_model,
)
from .graph_reasoning import (
    apply_causal_updates,
    compute_system_stability_metrics,
    create_user_graph,
    detect_failure_signals,
    generate_structured_explanations,
    propagate_risk_steps,
    simulate_shock_event,
    simulate_user_modification,
    simulate_risk_trajectory,
)
from .intervention import InterventionEngine
from .visualization import render_risk_graph


def create_initial_dataset() -> Tuple[List[Dict[str, float]], List[Tuple[str, str, float]]]:
    """Create a small interpretable dataset with 6 users and relationships."""
    users: List[Dict[str, float]] = [
        {"user_id": "U1", "income": 2200.0, "activity": 0.28, "transaction_variability": 0.82},
        {"user_id": "U2", "income": 3600.0, "activity": 0.63, "transaction_variability": 0.41},
        {"user_id": "U3", "income": 5200.0, "activity": 0.84, "transaction_variability": 0.17},
        {"user_id": "U4", "income": 2700.0, "activity": 0.37, "transaction_variability": 0.67},
        {"user_id": "U5", "income": 4600.0, "activity": 0.71, "transaction_variability": 0.36},
        {"user_id": "U6", "income": 1900.0, "activity": 0.22, "transaction_variability": 0.91},
    ]
    edges: List[Tuple[str, str, float]] = [
        ("U1", "U2", 1.2),
        ("U2", "U3", 0.9),
        ("U2", "U4", 1.1),
        ("U4", "U5", 0.8),
        ("U5", "U6", 1.3),
        ("U1", "U6", 0.7),
        ("U3", "U5", 1.0),
    ]
    return users, edges


def compute_risk_for_users(users: Sequence[Dict[str, float]]) -> List[Dict[str, float]]:
    """Compute base cognitive risk and return enriched user rows."""
    x, y, _ = generate_dataset(n_samples=400, random_seed=42)
    ml_bundle: MLRiskModel = train_model(x=x, y=y, random_seed=42)

    enriched: List[Dict[str, float]] = []
    for user in users:
        row = dict(user)
        rule_risk = predict_single_user_risk(
            income=float(row["income"]),
            activity=float(row["activity"]),
            transaction_variability=float(row["transaction_variability"]),
        )
        ml_pred = predict_risk(
            ml_bundle,
            {
                "income": float(row["income"]),
                "activity": float(row["activity"]),
                "transaction_variability": float(row["transaction_variability"]),
            },
        )

        ml_risk = float(ml_pred["ml_risk_probability"])
        final_risk = combine_risk(ml_risk, rule_risk, alpha=0.55)

        row["risk"] = final_risk
        row["ml_risk"] = ml_risk
        row["rule_risk"] = rule_risk
        row["dominant_factor"] = str(ml_pred["dominant_factor"])
        row["feature_contributions"] = dict(ml_pred["feature_contributions"])
        row["ml_backend"] = ml_bundle.backend
        row["ml_test_accuracy"] = float(ml_bundle.test_accuracy)
        enriched.append(row)
    return enriched


def _graph_state(graph: nx.Graph) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for node_id, attrs in graph.nodes(data=True):
        rows.append(
            {
                "user_id": node_id,
                "income": float(attrs.get("income", 0.0)),
                "activity": float(attrs.get("activity", 0.0)),
                "transaction_variability": float(attrs.get("transaction_variability", 0.0)),
                "risk": float(attrs.get("risk", 0.0)),
                "instability": float(attrs.get("instability", 0.0)),
                "ml_risk": float(attrs.get("ml_risk", 0.0)),
                "rule_risk": float(attrs.get("rule_risk", 0.0)),
                "dominant_factor": str(attrs.get("dominant_factor", "")),
                "risk_history": list(attrs.get("risk_history", [])),
                "explanation": list(attrs.get("explanation", [])),
            }
        )
    return sorted(rows, key=lambda item: item["risk"], reverse=True)


def run_dccfe_pipeline(
    simulation_user_id: str = "U2",
    simulation_income: float = 5200.0,
    simulation_activity: float = 0.82,
    propagation_factor: float = 0.1,
    propagation_steps: int = 3,
    shock_enabled: bool = True,
) -> Dict[str, Any]:
    """Run complete DCCFE pipeline from data to intervention with blockchain logs."""
    chain = SimpleHashBlockchain()

    # 1) Data handling
    users, edges = create_initial_dataset()
    chain.add_block({"event": "DATA_LOADED", "user_count": len(users), "edge_count": len(edges)})
    intervention_engine = InterventionEngine()

    # 2) Cognitive risk model
    users_with_risk = compute_risk_for_users(users)
    chain.add_block({"event": "RISK_COMPUTED", "users": [u["user_id"] for u in users_with_risk]})

    # 3) Graph system
    graph = create_user_graph(users_with_risk, edges)

    # 4) Initial visualization
    figure_initial = render_risk_graph(graph)

    # 5) Causal engine with explanations
    causal_explanations = apply_causal_updates(graph)
    chain.add_block(
        {
            "event": "CAUSAL_APPLIED",
            "changed_nodes": [node for node, reasons in causal_explanations.items() if reasons],
        }
    )

    # 6) Risk propagation
    propagation_history = propagate_risk_steps(
        graph,
        propagation_factor=propagation_factor,
        steps=propagation_steps,
    )
    chain.add_block(
        {
            "event": "PROPAGATION",
            "factor": propagation_factor,
            "steps": propagation_steps,
            "last_snapshot": propagation_history[-1] if propagation_history else {},
        }
    )

    pre_shock_avg = compute_system_stability_metrics(graph)["average_network_risk"]
    shock_result: Dict[str, Any] = {
        "shock_node": "",
        "shock_type": "none",
        "cascade_size": 0,
        "total_risk_increase": 0.0,
        "affected_nodes": [],
        "history": [],
    }
    if shock_enabled:
        shock_result = simulate_shock_event(
            graph,
            shock_type="income_drop",
            shock_alpha=min(max(propagation_factor + 0.1, 0.1), 0.3),
            steps=max(2, propagation_steps),
        )
        chain.add_block(
            {
                "event": "SHOCK",
                "node": shock_result["shock_node"],
                "cascade_size": shock_result["cascade_size"],
                "total_risk_increase": shock_result["total_risk_increase"],
            }
        )

    # 7) Update and re-render
    figure_after_propagation = render_risk_graph(graph)

    # 8) Counterfactual simulation (risk model -> causal -> propagation)
    simulated_graph = simulate_user_modification(
        graph,
        user_id=simulation_user_id,
        income=simulation_income,
        activity=simulation_activity,
        propagation_factor=propagation_factor,
        propagation_steps=propagation_steps,
    )
    trajectory = simulate_risk_trajectory(
        simulated_graph,
        steps=propagation_steps,
        propagation_factor=propagation_factor,
    )
    structured_explanations = generate_structured_explanations(simulated_graph, trajectory)
    chain.add_block(
        {
            "event": "SIMULATION",
            "user_id": simulation_user_id,
            "income": simulation_income,
            "activity": simulation_activity,
            "steps": propagation_steps,
        }
    )

    # 9) Intervention engine and centrality-aware critical ranking
    intervention = intervention_engine.optimize_intervention(
        simulated_graph,
        risk_reduction_factor=0.30,
        propagation_factor=propagation_factor,
        steps=propagation_steps,
    )
    critical_nodes = intervention_engine.rank_critical_nodes(simulated_graph, top_k=5)
    multi_node_intervention = intervention_engine.optimize_multi_node_intervention(
        simulated_graph,
        k=2,
        risk_reduction_factor=0.30,
        propagation_factor=propagation_factor,
        steps=propagation_steps,
    )

    stability_metrics = compute_system_stability_metrics(simulated_graph)
    failure_warning = detect_failure_signals(
        simulated_graph,
        previous_avg_risk=float(pre_shock_avg),
        recent_cascade_size=int(shock_result.get("cascade_size", 0)),
    )
    chain.add_block(
        {
            "event": "INTERVENTION",
            "critical_node": intervention["best_node"],
            "impact_score": intervention["impact_score"],
        }
    )
    chain.add_block(
        {
            "event": "CENTRALITY_RANKING",
            "top_node": critical_nodes[0]["node"] if critical_nodes else "",
        }
    )
    chain.add_block(
        {
            "event": "MULTI_NODE_INTERVENTION",
            "nodes": multi_node_intervention["best_nodes"],
            "improvement": multi_node_intervention["improvement_score"],
        }
    )
    chain.add_block(
        {
            "event": "STABILITY",
            "classification": stability_metrics["classification"],
            "score": stability_metrics["system_stability_score"],
        }
    )
    chain.add_block(
        {
            "event": "FAILURE_WARNING",
            "early_warning": failure_warning["early_warning"],
            "signals": failure_warning["signals"],
        }
    )

    result = {
        "initial_state": pd.DataFrame(_graph_state(create_user_graph(users_with_risk, edges))),
        "post_propagation_state": pd.DataFrame(_graph_state(graph)),
        "simulated_state": pd.DataFrame(_graph_state(simulated_graph)),
        "causal_explanations": causal_explanations,
        "propagation_history": propagation_history,
        "risk_trajectory": trajectory,
        "structured_explanations": structured_explanations,
        "shock_result": shock_result,
        "stability_metrics": stability_metrics,
        "failure_warning": failure_warning,
        "intervention": intervention,
        "multi_node_intervention": multi_node_intervention,
        "critical_node_ranking": critical_nodes,
        "blockchain_chain": chain.chain,
        "blockchain_valid": chain.verify_chain_integrity(),
        "figure_initial": figure_initial,
        "figure_after_propagation": figure_after_propagation,
        "figure_simulated": render_risk_graph(simulated_graph),
    }
    return result
