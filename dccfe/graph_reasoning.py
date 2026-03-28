from __future__ import annotations

import copy
import random
from math import ceil
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import networkx as nx

from .cognitive import predict_single_user_risk


def clamp_risk(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def create_user_graph(
    users: Iterable[Dict[str, float]],
    edges: Iterable[Tuple[str, str] | Tuple[str, str, float]],
) -> nx.Graph:
    """Create a graph from user rows and relationships.

    Each user row must include: user_id, income, activity, risk.
    Optional: transaction_variability.
    """
    graph = nx.Graph()
    for user in users:
        user_id = str(user["user_id"])
        graph.add_node(
            user_id,
            income=float(user["income"]),
            activity=float(user["activity"]),
            risk=clamp_risk(float(user["risk"])),
            transaction_variability=float(user.get("transaction_variability", 0.0)),
            instability=1.0 - min(max(float(user["activity"]), 0.0), 1.0),
            risk_history=[clamp_risk(float(user["risk"]))],
            explanation=[],
        )

    for edge in edges:
        if len(edge) == 2:
            source, target = edge  # type: ignore[misc]
            weight = 1.0
        else:
            source, target, weight = edge  # type: ignore[misc]
        if source in graph and target in graph:
            graph.add_edge(str(source), str(target), weight=max(float(weight), 0.0))

    return graph


def update_node_risk(graph: nx.Graph, user_id: str, new_risk: float) -> None:
    if user_id not in graph:
        raise KeyError(f"Unknown user: {user_id}")
    graph.nodes[user_id]["risk"] = clamp_risk(new_risk)
    _append_risk_history(graph, user_id)


def get_neighbors(graph: nx.Graph, user_id: str) -> List[str]:
    if user_id not in graph:
        raise KeyError(f"Unknown user: {user_id}")
    return list(graph.neighbors(user_id))


def causal_update_node_risk(
    graph: nx.Graph,
    user_id: str,
    weight_income: float = 0.30,
    weight_neighbor: float = 0.25,
    weight_activity: float = 0.20,
    weight_temporal: float = 0.15,
) -> Tuple[float, List[str]]:
    """Compute weighted causal risk update and explain contribution factors."""
    if user_id not in graph:
        raise KeyError(f"Unknown user: {user_id}")
    if weight_income + weight_neighbor + weight_activity + weight_temporal > 1.0:
        raise ValueError("Causal weights must sum to <= 1.0")

    node_data = graph.nodes[user_id]
    base_risk = clamp_risk(float(node_data.get("risk", 0.0)))
    reasons: List[str] = []

    income_min = 1500.0
    income_max = 9000.0
    income = float(node_data.get("income", 0.0))
    income_norm = min(max((income - income_min) / max(income_max - income_min, 1.0), 0.0), 1.0)
    income_effect = 1.0 - income_norm

    activity = float(node_data.get("activity", 0.0))
    activity_effect = 1.0 - min(max(activity, 0.0), 1.0)

    neighbors = get_neighbors(graph, user_id)
    neighbor_effect = 0.0
    if neighbors:
        weighted_sum = 0.0
        weight_total = 0.0
        for neighbor in neighbors:
            edge_weight = float(graph.edges[user_id, neighbor].get("weight", 1.0))
            weighted_sum += edge_weight * clamp_risk(float(graph.nodes[neighbor].get("risk", 0.0)))
            weight_total += edge_weight
        neighbor_effect = weighted_sum / max(weight_total, 1e-9)

    temporal_effect = min(max(float(node_data.get("instability", 0.0)), 0.0), 1.0)

    income_contrib = weight_income * income_effect
    neighbor_contrib = weight_neighbor * neighbor_effect
    activity_contrib = weight_activity * activity_effect
    temporal_contrib = weight_temporal * temporal_effect
    adjusted_risk = clamp_risk(base_risk + income_contrib + neighbor_contrib + activity_contrib + temporal_contrib)

    reasons.append(
        f"base={base_risk:.4f}; income={income_contrib:.4f}; neighbor={neighbor_contrib:.4f}; "
        f"activity={activity_contrib:.4f}; temporal={temporal_contrib:.4f}"
    )
    reasons.append(
        f"effects -> income:{income_effect:.4f}, neighbor:{neighbor_effect:.4f}, "
        f"activity:{activity_effect:.4f}, temporal:{temporal_effect:.4f}"
    )

    return adjusted_risk, reasons


def apply_causal_updates(
    graph: nx.Graph,
    weight_income: float = 0.30,
    weight_neighbor: float = 0.25,
    weight_activity: float = 0.20,
    weight_temporal: float = 0.15,
) -> Dict[str, List[str]]:
    """Apply causal updates to every node and return per-node explanations."""
    updates: Dict[str, float] = {}
    explanations: Dict[str, List[str]] = {}

    for user_id in graph.nodes:
        _refresh_temporal_instability(graph, user_id)

    for user_id in graph.nodes:
        risk, reasons = causal_update_node_risk(
            graph,
            user_id,
            weight_income=weight_income,
            weight_neighbor=weight_neighbor,
            weight_activity=weight_activity,
            weight_temporal=weight_temporal,
        )
        updates[user_id] = risk
        explanations[user_id] = reasons

    for user_id, risk in updates.items():
        graph.nodes[user_id]["risk"] = risk
        graph.nodes[user_id]["explanation"] = explanations[user_id]

    return explanations


def propagate_risk_once(graph: nx.Graph, propagation_factor: float = 0.1) -> Dict[str, float]:
    """Propagate a small fraction of each node risk through edges once."""
    factor = min(max(float(propagation_factor), 0.1), 0.3)
    next_risk: Dict[str, float] = {}

    for user_id in graph.nodes:
        own_risk = float(graph.nodes[user_id].get("risk", 0.0))
        neighbors = get_neighbors(graph, user_id)

        if not neighbors:
            next_risk[user_id] = clamp_risk(own_risk)
            continue

        weighted_sum = 0.0
        weight_total = 0.0
        for neighbor in neighbors:
            edge_weight = float(graph.edges[user_id, neighbor].get("weight", 1.0))
            weighted_sum += edge_weight * float(graph.nodes[neighbor].get("risk", 0.0))
            weight_total += edge_weight
        avg_neighbor_risk = weighted_sum / max(weight_total, 1e-9)
        updated = (1.0 - factor) * own_risk + factor * avg_neighbor_risk
        next_risk[user_id] = clamp_risk(updated)

    for user_id, risk in next_risk.items():
        graph.nodes[user_id]["risk"] = risk

    return next_risk


def propagate_risk_steps(
    graph: nx.Graph,
    propagation_factor: float = 0.2,
    steps: int = 4,
) -> List[Dict[str, float]]:
    """Run iterative propagation and return risk snapshots for each step."""
    history: List[Dict[str, float]] = []
    iterations = max(int(steps), 1)
    for _ in range(iterations):
        history.append(propagate_risk_once(graph, propagation_factor=propagation_factor))
        _append_all_risk_history(graph)
        for user_id in graph.nodes:
            _refresh_temporal_instability(graph, user_id)
    return history


def simulate_user_modification(
    graph: nx.Graph,
    user_id: str,
    income: float | None = None,
    activity: float | None = None,
    propagation_factor: float = 0.2,
    propagation_steps: int = 4,
) -> nx.Graph:
    """Simulate user attribute changes and recompute causal plus propagated risk.

    Returns a new graph state, leaving the original graph unchanged.
    """
    if user_id not in graph:
        raise KeyError(f"Unknown user: {user_id}")

    simulated = copy.deepcopy(graph)
    node = simulated.nodes[user_id]

    if income is not None:
        node["income"] = max(float(income), 0.0)
    if activity is not None:
        node["activity"] = min(max(float(activity), 0.0), 1.0)

    # Recompute base risk first so the simulation follows: risk model -> causal -> propagation.
    for current_id, attrs in simulated.nodes(data=True):
        recomputed = predict_single_user_risk(
            income=float(attrs.get("income", 0.0)),
            activity=float(attrs.get("activity", 0.0)),
            transaction_variability=float(attrs.get("transaction_variability", 0.0)),
        )
        simulated.nodes[current_id]["risk"] = clamp_risk(recomputed)

    simulate_risk_trajectory(
        simulated,
        steps=propagation_steps,
        propagation_factor=propagation_factor,
    )
    return simulated


def simulate_risk_trajectory(
    graph: nx.Graph,
    steps: int = 4,
    propagation_factor: float = 0.2,
) -> List[Dict[str, Dict[str, Any]]]:
    """Run multi-step system simulation and return node-level risk trajectory."""
    trajectory: List[Dict[str, Dict[str, Any]]] = []
    iterations = max(int(steps), 1)

    for step in range(iterations):
        pre_step_risk = {node: float(graph.nodes[node].get("risk", 0.0)) for node in graph.nodes}
        causal_details = apply_causal_updates(graph)
        diffuse = propagate_risk_once(graph, propagation_factor=propagation_factor)
        _append_all_risk_history(graph)
        for node in graph.nodes:
            _refresh_temporal_instability(graph, node)

        snapshot: Dict[str, Dict[str, Any]] = {}
        for node in graph.nodes:
            snapshot[node] = {
                "step": step + 1,
                "risk_before": pre_step_risk[node],
                "risk_after": float(graph.nodes[node].get("risk", 0.0)),
                "diffusion_risk": diffuse[node],
                "causal_explanation": causal_details.get(node, []),
                "neighbor_influence": _neighbor_influence(graph, node),
                "instability": float(graph.nodes[node].get("instability", 0.0)),
            }
        trajectory.append(snapshot)

    return trajectory


def _neighbor_influence(graph: nx.Graph, user_id: str) -> float:
    neighbors = get_neighbors(graph, user_id)
    if not neighbors:
        return 0.0
    weighted_sum = 0.0
    weight_total = 0.0
    for neighbor in neighbors:
        edge_weight = float(graph.edges[user_id, neighbor].get("weight", 1.0))
        weighted_sum += edge_weight * float(graph.nodes[neighbor].get("risk", 0.0))
        weight_total += edge_weight
    return weighted_sum / max(weight_total, 1e-9)


def generate_structured_explanations(
    graph: nx.Graph,
    trajectory: List[Dict[str, Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
    """Generate human-readable structured explanation for each node."""
    explanations: Dict[str, Dict[str, Any]] = {}
    if not trajectory:
        for node in graph.nodes:
            explanations[node] = {
                "final_risk": float(graph.nodes[node].get("risk", 0.0)),
                "summary": "no propagation steps were executed",
                "factor_contributions": list(graph.nodes[node].get("explanation", [])),
            }
        return explanations

    last_snapshot = trajectory[-1]
    for node in graph.nodes:
        node_trace = [step[node] for step in trajectory if node in step]
        risk_series = [round(float(item["risk_after"]), 6) for item in node_trace]
        last = last_snapshot[node]
        explanations[node] = {
            "final_risk": round(float(graph.nodes[node].get("risk", 0.0)), 6),
            "factor_contributions": list(graph.nodes[node].get("explanation", [])),
            "neighbor_influence": round(float(last.get("neighbor_influence", 0.0)), 6),
            "instability": round(float(graph.nodes[node].get("instability", 0.0)), 6),
            "trajectory": risk_series,
            "summary": (
                f"risk moved from {node_trace[0]['risk_before']:.4f} to {node_trace[-1]['risk_after']:.4f} "
                f"over {len(node_trace)} steps"
            ),
        }
    return explanations


def simulate_shock_event(
    graph: nx.Graph,
    node_id: str | None = None,
    shock_type: str = "income_drop",
    income_drop_ratio: float = 0.35,
    risk_spike: float = 0.35,
    shock_alpha: float = 0.3,
    steps: int = 3,
    random_seed: int | None = None,
) -> Dict[str, Any]:
    """Trigger shock event and measure cascade impact through the network."""
    if graph.number_of_nodes() == 0:
        return {
            "shock_node": "",
            "shock_type": shock_type,
            "cascade_size": 0,
            "total_risk_increase": 0.0,
            "affected_nodes": [],
            "history": [],
        }

    rng = random.Random(random_seed)
    shock_node = node_id if node_id in graph else rng.choice(list(graph.nodes))
    before = {node: float(graph.nodes[node].get("risk", 0.0)) for node in graph.nodes}

    if shock_type == "income_drop":
        original_income = float(graph.nodes[shock_node].get("income", 0.0))
        graph.nodes[shock_node]["income"] = max(original_income * (1.0 - income_drop_ratio), 0.0)
        recomputed = predict_single_user_risk(
            income=float(graph.nodes[shock_node].get("income", 0.0)),
            activity=float(graph.nodes[shock_node].get("activity", 0.0)),
            transaction_variability=float(graph.nodes[shock_node].get("transaction_variability", 0.0)),
        )
        graph.nodes[shock_node]["risk"] = clamp_risk(max(recomputed, before[shock_node] + 0.15))
    elif shock_type == "risk_spike":
        graph.nodes[shock_node]["risk"] = clamp_risk(before[shock_node] + risk_spike)
    else:
        raise ValueError("shock_type must be 'income_drop' or 'risk_spike'")

    neighbors = get_neighbors(graph, shock_node)
    for neighbor in neighbors:
        edge_weight = float(graph.edges[shock_node, neighbor].get("weight", 1.0))
        graph.nodes[neighbor]["risk"] = clamp_risk(
            float(graph.nodes[neighbor].get("risk", 0.0)) + 0.12 * edge_weight
        )

    _append_all_risk_history(graph)
    cascade_history = propagate_risk_steps(
        graph,
        propagation_factor=min(max(shock_alpha, 0.1), 0.3),
        steps=max(int(steps), 1),
    )

    after = {node: float(graph.nodes[node].get("risk", 0.0)) for node in graph.nodes}
    affected_nodes = [node for node in graph.nodes if after[node] - before[node] > 0.05]
    total_risk_increase = sum(max(after[node] - before[node], 0.0) for node in graph.nodes)

    return {
        "shock_node": shock_node,
        "shock_type": shock_type,
        "cascade_size": len(affected_nodes),
        "total_risk_increase": round(total_risk_increase, 6),
        "affected_nodes": sorted(affected_nodes),
        "history": cascade_history,
    }


def compute_system_stability_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """Compute global stability metrics and classify system condition."""
    if graph.number_of_nodes() == 0:
        return {
            "average_network_risk": 0.0,
            "risk_variance": 0.0,
            "high_risk_nodes": 0,
            "system_stability_score": 1.0,
            "classification": "stable",
        }

    risks = [clamp_risk(float(data.get("risk", 0.0))) for _, data in graph.nodes(data=True)]
    n = len(risks)
    avg = sum(risks) / n
    variance = sum((r - avg) ** 2 for r in risks) / n
    high = sum(1 for r in risks if r > 0.7)

    high_ratio = high / max(n, 1)
    variance_norm = min(variance * 4.0, 1.0)
    stability = 1.0 - min(0.55 * avg + 0.25 * variance_norm + 0.20 * high_ratio, 1.0)

    if stability >= 0.65:
        cls = "stable"
    elif stability >= 0.40:
        cls = "fragile"
    else:
        cls = "critical"

    return {
        "average_network_risk": round(avg, 6),
        "risk_variance": round(variance, 6),
        "high_risk_nodes": high,
        "system_stability_score": round(stability, 6),
        "classification": cls,
    }


def detect_failure_signals(
    graph: nx.Graph,
    previous_avg_risk: float | None = None,
    recent_cascade_size: int = 0,
    high_risk_ratio_threshold: float = 0.5,
    rapid_increase_threshold: float = 0.08,
    cascade_threshold_ratio: float = 0.4,
) -> Dict[str, Any]:
    """Detect early warning conditions and top contributing nodes."""
    metrics = compute_system_stability_metrics(graph)
    n = max(graph.number_of_nodes(), 1)
    high_ratio = float(metrics["high_risk_nodes"]) / n
    avg_risk = float(metrics["average_network_risk"])

    rapid_increase = (
        previous_avg_risk is not None
        and (avg_risk - float(previous_avg_risk)) >= rapid_increase_threshold
    )
    large_cascade = recent_cascade_size >= ceil(cascade_threshold_ratio * n)
    too_many_high_risk = high_ratio >= high_risk_ratio_threshold

    warning = bool(too_many_high_risk or rapid_increase or large_cascade)
    signals: List[str] = []
    if too_many_high_risk:
        signals.append("too many high-risk nodes")
    if rapid_increase:
        signals.append("rapid increase in global risk")
    if large_cascade:
        signals.append("strong cascade detected")

    centrality = nx.degree_centrality(graph) if graph.number_of_nodes() > 1 else {node: 0.0 for node in graph.nodes}
    contributors = []
    for node, data in graph.nodes(data=True):
        risk = float(data.get("risk", 0.0))
        score = risk * (1.0 + float(centrality.get(node, 0.0)))
        contributors.append((str(node), score))
    contributors.sort(key=lambda item: item[1], reverse=True)

    return {
        "early_warning": warning,
        "signals": signals,
        "contributing_nodes": [node for node, _ in contributors[:3]],
        "stability_classification": metrics["classification"],
        "average_network_risk": metrics["average_network_risk"],
    }


def _append_risk_history(graph: nx.Graph, user_id: str, max_length: int = 100) -> None:
    history = list(graph.nodes[user_id].get("risk_history", []))
    history.append(clamp_risk(float(graph.nodes[user_id].get("risk", 0.0))))
    if len(history) > max_length:
        history = history[-max_length:]
    graph.nodes[user_id]["risk_history"] = history


def _append_all_risk_history(graph: nx.Graph, max_length: int = 100) -> None:
    for user_id in graph.nodes:
        _append_risk_history(graph, user_id, max_length=max_length)


def _refresh_temporal_instability(graph: nx.Graph, user_id: str) -> None:
    node = graph.nodes[user_id]
    history = list(node.get("risk_history", []))
    if len(history) < 2:
        return

    window = history[-4:]
    trend = (window[-1] - window[0]) / max(len(window) - 1, 1)
    current_instability = float(node.get("instability", 0.0))

    if trend > 0.01:
        current_instability = min(current_instability + min(0.20, trend * 1.5), 1.0)
    elif trend < -0.01:
        current_instability = max(current_instability - min(0.15, (-trend) * 1.2), 0.0)

    node["instability"] = current_instability


def identify_most_critical_node(
    graph: nx.Graph,
    include_connectivity: bool = True,
) -> Dict[str, str | float]:
    """Identify the node with highest systemic criticality and explain why."""
    if graph.number_of_nodes() == 0:
        return {
            "node_id": "",
            "reason": "graph is empty",
            "suggestion": "add users and relationships before intervention analysis",
            "score": 0.0,
        }

    centrality = nx.degree_centrality(graph) if include_connectivity else {n: 0.0 for n in graph.nodes}
    best_node = ""
    best_score = -1.0

    for node, data in graph.nodes(data=True):
        risk = float(data.get("risk", 0.0))
        connectivity = float(centrality.get(node, 0.0))
        score = risk * (1.0 + connectivity)
        if score > best_score:
            best_node = str(node)
            best_score = score

    best_risk = float(graph.nodes[best_node].get("risk", 0.0))
    best_connectivity = float(centrality.get(best_node, 0.0))

    if include_connectivity:
        reason = (
            f"node {best_node} has highest combined score from risk ({best_risk:.3f}) "
            f"and connectivity ({best_connectivity:.3f})"
        )
    else:
        reason = f"node {best_node} has highest risk score ({best_risk:.3f})"

    suggestion = f"prioritize intervention on {best_node} to reduce local and systemic risk"
    return {
        "node_id": best_node,
        "reason": reason,
        "suggestion": suggestion,
        "score": round(best_score, 6),
    }
