from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Sequence, Tuple

import networkx as nx
import numpy as np


NetworkMode = Literal["random", "preferential_attachment"]


@dataclass
class ScalingConfig:
    user_count: int = 100
    network_mode: NetworkMode = "preferential_attachment"
    random_seed: int = 42
    average_degree: int = 6
    alpha: float = 0.22
    steps: int = 6
    intervention_top_k: int = 25
    critical_report_count: int = 5
    max_log_events: int = 250


class KeyEventChain:
    """Lightweight hash chain that stores only key events for scalable runs."""

    def __init__(self, max_events: int = 250) -> None:
        self.max_events = max(10, int(max_events))
        self.chain: List[Dict[str, Any]] = []
        self._append("GENESIS", {"message": "Scaling chain initialized"})

    def _hash(self, payload: Dict[str, Any]) -> str:
        body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def _append(self, event_type: str, payload: Dict[str, Any]) -> None:
        previous_hash = self.chain[-1]["hash"] if self.chain else "0"
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "event_type": str(event_type),
            "payload": payload,
            "previous_hash": previous_hash,
            "hash": "",
        }
        block["hash"] = self._hash(
            {
                "index": block["index"],
                "timestamp": block["timestamp"],
                "event_type": block["event_type"],
                "payload": block["payload"],
                "previous_hash": block["previous_hash"],
            }
        )
        self.chain.append(block)

        # Keep only key recent events while preserving continuity.
        if len(self.chain) > self.max_events:
            head = self.chain[:1]
            tail = self.chain[-(self.max_events - 1) :]
            merged = head + tail
            # Reindex and relink to keep chain valid after pruning.
            relinked: List[Dict[str, Any]] = []
            previous = "0"
            for idx, item in enumerate(merged):
                rebuilt = {
                    "index": idx,
                    "timestamp": item["timestamp"],
                    "event_type": item["event_type"],
                    "payload": item["payload"],
                    "previous_hash": previous,
                    "hash": "",
                }
                rebuilt["hash"] = self._hash(
                    {
                        "index": rebuilt["index"],
                        "timestamp": rebuilt["timestamp"],
                        "event_type": rebuilt["event_type"],
                        "payload": rebuilt["payload"],
                        "previous_hash": rebuilt["previous_hash"],
                    }
                )
                previous = rebuilt["hash"]
                relinked.append(rebuilt)
            self.chain = relinked

    def add_key_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._append(event_type=event_type, payload=payload)


def generate_scaled_users(count: int, random_seed: int = 42) -> List[Dict[str, float]]:
    """Generate realistic user attributes for large-scale simulations."""
    rng = np.random.default_rng(random_seed)
    count = max(10, int(count))

    incomes = rng.lognormal(mean=8.05, sigma=0.38, size=count)
    incomes = np.clip(incomes, 900.0, 18000.0)

    activity = rng.beta(a=2.5, b=2.0, size=count)
    variability = rng.beta(a=2.0, b=2.8, size=count)

    users: List[Dict[str, float]] = []
    for idx in range(count):
        users.append(
            {
                "user_id": f"U{idx+1}",
                "income": float(incomes[idx]),
                "activity": float(activity[idx]),
                "transaction_variability": float(variability[idx]),
            }
        )
    return users


def _edges_from_graph(graph: nx.Graph) -> List[Tuple[str, str, float]]:
    edges: List[Tuple[str, str, float]] = []
    for source, target in graph.edges:
        edges.append((str(source), str(target), float(graph.edges[source, target].get("weight", 1.0))))
    return edges


def generate_scaled_relationships(
    user_ids: Sequence[str],
    mode: NetworkMode = "preferential_attachment",
    average_degree: int = 6,
    random_seed: int = 42,
) -> List[Tuple[str, str, float]]:
    """Generate random or scale-free graph relationships with weighted edges."""
    count = len(user_ids)
    if count < 2:
        return []

    avg_degree = max(2, int(average_degree))
    rng = random.Random(random_seed)

    if mode == "preferential_attachment":
        m = max(1, min(avg_degree // 2, count - 1))
        base = nx.barabasi_albert_graph(n=count, m=m, seed=random_seed)
    else:
        p = min(max(avg_degree / max(count - 1, 1), 0.01), 0.25)
        base = nx.erdos_renyi_graph(n=count, p=p, seed=random_seed)
        if not nx.is_connected(base):
            nodes = list(base.nodes)
            for idx in range(len(nodes) - 1):
                if not nx.has_path(base, nodes[idx], nodes[idx + 1]):
                    base.add_edge(nodes[idx], nodes[idx + 1])

    remapped = nx.Graph()
    for u, v in base.edges:
        source = user_ids[int(u)]
        target = user_ids[int(v)]
        weight = round(rng.uniform(0.5, 1.6), 3)
        remapped.add_edge(source, target, weight=weight)
    return _edges_from_graph(remapped)


def _initial_risk_vector(income: np.ndarray, activity: np.ndarray, variability: np.ndarray) -> np.ndarray:
    """Vectorized explainable risk baseline (logistic-like, no deep model)."""
    income_effect = 1.0 - np.clip(income / 9000.0, 0.0, 1.0)
    activity_effect = 1.0 - np.clip(activity, 0.0, 1.0)
    variability_effect = np.clip(variability, 0.0, 1.0)

    linear = 1.5 * income_effect + 1.25 * activity_effect + 1.35 * variability_effect - 1.8
    risk = 1.0 / (1.0 + np.exp(-linear))
    return np.clip(risk, 0.0, 1.0)


def _build_graph(
    users: Sequence[Dict[str, float]],
    relationships: Sequence[Tuple[str, str, float]],
) -> nx.Graph:
    graph = nx.Graph()
    for user in users:
        graph.add_node(
            str(user["user_id"]),
            income=float(user["income"]),
            activity=float(user["activity"]),
            transaction_variability=float(user["transaction_variability"]),
            risk=0.0,
        )
    for source, target, weight in relationships:
        if source in graph and target in graph and source != target:
            graph.add_edge(str(source), str(target), weight=max(float(weight), 0.05))
    return graph


def _adjacency_cache(graph: nx.Graph, node_index: Dict[str, int]) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
    """Cache neighbor index and edge weights for fast iterative propagation."""
    cache: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}
    for node in graph.nodes:
        idx = node_index[str(node)]
        neighbors = list(graph.neighbors(node))
        if not neighbors:
            cache[idx] = (np.array([], dtype=np.int64), np.array([], dtype=np.float64))
            continue
        n_idx = np.array([node_index[str(n)] for n in neighbors], dtype=np.int64)
        weights = np.array([float(graph.edges[node, n].get("weight", 1.0)) for n in neighbors], dtype=np.float64)
        cache[idx] = (n_idx, weights)
    return cache


def _batch_propagate(
    risk: np.ndarray,
    adj_cache: Dict[int, Tuple[np.ndarray, np.ndarray]],
    alpha: float,
    steps: int,
) -> np.ndarray:
    alpha = min(max(float(alpha), 0.05), 0.45)
    steps = max(1, min(int(steps), 10))

    current = np.array(risk, dtype=np.float64)
    next_risk = np.zeros_like(current)
    for _ in range(steps):
        for idx in range(current.shape[0]):
            neighbors, weights = adj_cache[idx]
            own = current[idx]
            if neighbors.size == 0:
                next_risk[idx] = own
                continue
            weighted_neighbor_avg = float(np.dot(weights, current[neighbors]) / max(np.sum(weights), 1e-9))
            next_risk[idx] = (1.0 - alpha) * own + alpha * weighted_neighbor_avg
        np.clip(next_risk, 0.0, 1.0, out=next_risk)
        current, next_risk = next_risk, current
    return current


def _select_visual_subgraph(graph: nx.Graph, top_risk: int = 25, top_central: int = 25) -> nx.Graph:
    """Avoid full rendering for large networks by focusing on risky and central nodes."""
    if graph.number_of_nodes() <= max(top_risk + top_central, 80):
        return graph.copy()

    risks = sorted(graph.nodes, key=lambda n: float(graph.nodes[n].get("risk", 0.0)), reverse=True)
    centrality = nx.degree_centrality(graph)
    central = sorted(centrality, key=lambda n: float(centrality[n]), reverse=True)
    keep = set([str(n) for n in risks[:top_risk]] + [str(n) for n in central[:top_central]])
    return graph.subgraph(keep).copy()


def _risk_histogram(risk: np.ndarray) -> Dict[str, int]:
    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.01]
    labels = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
    counts, _ = np.histogram(risk, bins=bins)
    return {labels[idx]: int(counts[idx]) for idx in range(len(labels))}


def _intervention_shortlist(
    graph: nx.Graph,
    node_order: Sequence[str],
    risk: np.ndarray,
    adj_cache: Dict[int, Tuple[np.ndarray, np.ndarray]],
    top_k: int,
    alpha: float,
) -> Dict[str, Any]:
    """Evaluate intervention only on shortlisted high-risk nodes."""
    top_k = max(3, min(int(top_k), len(node_order)))
    ranked_idx = np.argsort(-risk)
    shortlist = [int(i) for i in ranked_idx[:top_k]]
    baseline_total = float(np.sum(risk))

    best_node = ""
    best_total = baseline_total
    for idx in shortlist:
        simulated = np.array(risk, copy=True)
        simulated[idx] = max(0.0, simulated[idx] * 0.72)
        simulated = _batch_propagate(simulated, adj_cache, alpha=alpha, steps=3)
        total = float(np.sum(simulated))
        if total < best_total:
            best_total = total
            best_node = str(node_order[idx])

    return {
        "recommended_node": best_node,
        "shortlist_size": top_k,
        "baseline_total_risk": round(baseline_total, 6),
        "optimized_total_risk": round(best_total, 6),
        "estimated_reduction": round(baseline_total - best_total, 6),
    }


def _critical_node_reports(graph: nx.Graph, top_n: int = 5) -> Dict[str, str]:
    sorted_nodes = sorted(graph.nodes, key=lambda n: float(graph.nodes[n].get("risk", 0.0)), reverse=True)
    selected = sorted_nodes[: max(1, int(top_n))]
    reports: Dict[str, str] = {}
    for node in selected:
        risk = float(graph.nodes[node].get("risk", 0.0))
        activity = float(graph.nodes[node].get("activity", 0.0))
        income = float(graph.nodes[node].get("income", 0.0))
        neighbors = list(graph.neighbors(node))
        neighbor_risk = 0.0
        if neighbors:
            neighbor_risk = sum(float(graph.nodes[n].get("risk", 0.0)) for n in neighbors) / len(neighbors)
        reports[str(node)] = (
            f"{node} is in the critical tier due to combined personal vulnerability and network pressure. "
            f"Income and activity signals indicate persistent fragility, while connected peers keep the risk level elevated. "
            f"Prioritize targeted support and closer monitoring to prevent wider contagion. "
            f"Current profile: risk={risk:.3f}, activity={activity:.3f}, income={income:.0f}, neighbor influence={neighbor_risk:.3f}."
        )
    return reports


def run_full_scaling_mode(
    dataset: Sequence[Dict[str, float]] | None = None,
    config: ScalingConfig | None = None,
) -> Dict[str, Any]:
    """Run scalable DCCFE pipeline for 50 to 500+ nodes with aggregated outputs."""
    cfg = config or ScalingConfig()
    chain = KeyEventChain(max_events=cfg.max_log_events)

    users = list(dataset) if dataset is not None else generate_scaled_users(cfg.user_count, cfg.random_seed)
    if len(users) < 50:
        raise ValueError("FULL SCALING MODE requires at least 50 users")

    user_ids = [str(u["user_id"]) for u in users]
    edges = generate_scaled_relationships(
        user_ids,
        mode=cfg.network_mode,
        average_degree=cfg.average_degree,
        random_seed=cfg.random_seed,
    )
    graph = _build_graph(users=users, relationships=edges)
    chain.add_key_event("DATA_PREPARED", {"users": len(users), "edges": len(edges), "mode": cfg.network_mode})

    node_order = [str(n) for n in graph.nodes]
    node_index = {node_id: idx for idx, node_id in enumerate(node_order)}

    income = np.array([float(graph.nodes[n].get("income", 0.0)) for n in node_order], dtype=np.float64)
    activity = np.array([float(graph.nodes[n].get("activity", 0.0)) for n in node_order], dtype=np.float64)
    variability = np.array(
        [float(graph.nodes[n].get("transaction_variability", 0.0)) for n in node_order],
        dtype=np.float64,
    )

    base_risk = _initial_risk_vector(income, activity, variability)
    adj_cache = _adjacency_cache(graph, node_index)
    propagated_risk = _batch_propagate(base_risk, adj_cache, alpha=cfg.alpha, steps=cfg.steps)
    chain.add_key_event("PROPAGATION_COMPLETE", {"alpha": cfg.alpha, "steps": cfg.steps})

    for idx, node in enumerate(node_order):
        graph.nodes[node]["risk"] = float(propagated_risk[idx])

    avg_risk = float(np.mean(propagated_risk)) if propagated_risk.size else 0.0
    variance = float(np.var(propagated_risk)) if propagated_risk.size else 0.0
    high_risk_count = int(np.sum(propagated_risk >= 0.7))

    centrality = nx.degree_centrality(graph)
    top_risky_idx = np.argsort(-propagated_risk)[:10]
    top_risky_nodes = [
        {
            "user_id": node_order[int(i)],
            "risk": round(float(propagated_risk[int(i)]), 6),
            "degree_centrality": round(float(centrality.get(node_order[int(i)], 0.0)), 6),
        }
        for i in top_risky_idx
    ]

    top_central = sorted(centrality.items(), key=lambda item: float(item[1]), reverse=True)[:10]
    centrality_ranking = [
        {"user_id": str(node), "degree_centrality": round(float(score), 6)}
        for node, score in top_central
    ]

    intervention = _intervention_shortlist(
        graph=graph,
        node_order=node_order,
        risk=propagated_risk,
        adj_cache=adj_cache,
        top_k=cfg.intervention_top_k,
        alpha=cfg.alpha,
    )
    chain.add_key_event(
        "INTERVENTION_SHORTLIST",
        {
            "shortlist_size": intervention["shortlist_size"],
            "recommended_node": intervention["recommended_node"],
            "estimated_reduction": intervention["estimated_reduction"],
        },
    )

    visual_subgraph = _select_visual_subgraph(graph)
    stability = {
        "classification": "critical" if avg_risk >= 0.65 else ("fragile" if avg_risk >= 0.4 else "stable"),
        "average_risk": round(avg_risk, 6),
        "risk_variance": round(variance, 6),
        "high_risk_nodes": high_risk_count,
        "risk_distribution": _risk_histogram(propagated_risk),
        "centrality_ranking": centrality_ranking,
    }

    system_summary = {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "network_mode": cfg.network_mode,
        "average_risk": round(avg_risk, 6),
        "high_risk_nodes": high_risk_count,
        "render_mode": "partial_subgraph" if visual_subgraph.number_of_nodes() < graph.number_of_nodes() else "full_graph",
        "visual_nodes": visual_subgraph.number_of_nodes(),
        "visual_edges": visual_subgraph.number_of_edges(),
    }

    critical_reports = _critical_node_reports(graph, top_n=cfg.critical_report_count)
    chain.add_key_event("REPORTS_GENERATED", {"critical_nodes_reported": len(critical_reports)})

    return {
        "system_summary": system_summary,
        "top_risky_nodes": top_risky_nodes,
        "intervention": intervention,
        "stability": stability,
        "system_level_report": (
            "System risk is computed in batch mode with cached adjacency for scalable performance. "
            "The current state is summarized using distribution, concentration, and centrality indicators, "
            "with interventions prioritized on a high-risk shortlist to reduce computational overhead."
        ),
        "critical_node_reports": critical_reports,
        "visual_subgraph": visual_subgraph,
        "key_event_log": chain.chain,
    }
