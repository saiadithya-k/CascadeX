from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Dict, List, Sequence, Tuple

import networkx as nx

from .cognitive import predict_single_user_risk


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return min(max(float(v), lo), hi)


def _safe_div(a: float, b: float, eps: float = 1e-9) -> float:
    return a / max(b, eps)


@dataclass
class BayesianConfig:
    prior_risk: float = 0.5
    learning_rate: float = 0.05


class BayesianCausalNetwork:
    """Lightweight Bayesian causal model with adaptive likelihood updates."""

    def __init__(self, config: BayesianConfig | None = None) -> None:
        self.config = config or BayesianConfig()
        # P(factor=1 | risk=1) and P(factor=1 | risk=0)
        self.likelihood_risk = {
            "income_low": 0.78,
            "activity_low": 0.72,
            "neighbor_high": 0.75,
            "trend_up": 0.70,
        }
        self.likelihood_safe = {
            "income_low": 0.30,
            "activity_low": 0.35,
            "neighbor_high": 0.25,
            "trend_up": 0.28,
        }

    def _features_for_node(self, graph: nx.Graph, node: str) -> Dict[str, float]:
        attrs = graph.nodes[node]
        income = float(attrs.get("income", 0.0))
        activity = float(attrs.get("activity", 0.0))
        history = list(attrs.get("risk_history", [float(attrs.get("risk", 0.0))]))

        income_low = 1.0 - _clamp((income - 1500.0) / 7500.0)
        activity_low = 1.0 - _clamp(activity)

        neighbors = list(graph.neighbors(node))
        if neighbors:
            weighted_sum = 0.0
            weight_total = 0.0
            for n in neighbors:
                w = float(graph.edges[node, n].get("weight", 1.0))
                weighted_sum += w * float(graph.nodes[n].get("risk", 0.0))
                weight_total += w
            neighbor_high = _safe_div(weighted_sum, weight_total)
        else:
            neighbor_high = float(attrs.get("risk", 0.0))

        trend_up = 0.5
        if len(history) >= 2:
            trend = (history[-1] - history[max(0, len(history) - 4)]) / max(min(3, len(history) - 1), 1)
            trend_up = _clamp(0.5 + trend)

        return {
            "income_low": _clamp(income_low),
            "activity_low": _clamp(activity_low),
            "neighbor_high": _clamp(neighbor_high),
            "trend_up": _clamp(trend_up),
        }

    def infer_node(self, graph: nx.Graph, node: str) -> Dict[str, Any]:
        factors = self._features_for_node(graph, node)
        prior = _clamp(self.config.prior_risk, 0.01, 0.99)

        p_f_given_risk = 1.0
        p_f_given_safe = 1.0
        contributions: Dict[str, float] = {}

        for name, value in factors.items():
            pr = _clamp(self.likelihood_risk[name])
            ps = _clamp(self.likelihood_safe[name])
            # Soft Bernoulli likelihood for continuous factor intensity in [0,1]
            l_risk = (pr ** value) * ((1.0 - pr) ** (1.0 - value))
            l_safe = (ps ** value) * ((1.0 - ps) ** (1.0 - value))
            p_f_given_risk *= l_risk
            p_f_given_safe *= l_safe
            contributions[name] = value

        numerator = p_f_given_risk * prior
        denominator = numerator + p_f_given_safe * (1.0 - prior)
        posterior = _safe_div(numerator, denominator)
        confidence = abs(posterior - 0.5) * 2.0

        return {
            "node": node,
            "posterior_risk": _clamp(posterior),
            "confidence": _clamp(confidence),
            "factors": factors,
            "contributions": contributions,
        }

    def infer_all(self, graph: nx.Graph) -> Dict[str, Dict[str, Any]]:
        return {node: self.infer_node(graph, str(node)) for node in graph.nodes}

    def update_from_observations(self, inferences: Dict[str, Dict[str, Any]], graph: nx.Graph) -> None:
        lr = _clamp(self.config.learning_rate, 0.0, 1.0)
        for node, info in inferences.items():
            observed_risk = float(graph.nodes[node].get("risk", 0.0))
            inferred = float(info["posterior_risk"])
            error = observed_risk - inferred
            for name, value in info["factors"].items():
                self.likelihood_risk[name] = _clamp(self.likelihood_risk[name] + lr * error * value)
                self.likelihood_safe[name] = _clamp(self.likelihood_safe[name] - lr * error * value)


class TemporalDynamicsModel:
    """Time-indexed risk transitions with trend/acceleration/volatility tracking."""

    def __init__(self, base_alpha: float = 0.2) -> None:
        self.base_alpha = _clamp(base_alpha, 0.1, 0.3)

    def _append_history(self, graph: nx.Graph, node: str) -> None:
        history = list(graph.nodes[node].get("risk_history", []))
        history.append(_clamp(float(graph.nodes[node].get("risk", 0.0))))
        graph.nodes[node]["risk_history"] = history[-200:]

    def _temporal_stats(self, history: List[float]) -> Dict[str, float]:
        if len(history) < 2:
            return {"trend": 0.0, "acceleration": 0.0, "volatility": 0.0, "oscillation": 0.0}

        diffs = [history[i] - history[i - 1] for i in range(1, len(history))]
        trend = sum(diffs[-5:]) / max(len(diffs[-5:]), 1)
        acceleration = 0.0
        if len(diffs) >= 2:
            acceleration = diffs[-1] - diffs[-2]
        mean = sum(history[-8:]) / max(len(history[-8:]), 1)
        volatility = (sum((x - mean) ** 2 for x in history[-8:]) / max(len(history[-8:]), 1)) ** 0.5

        sign_changes = 0
        for i in range(1, len(diffs)):
            if diffs[i] == 0.0:
                continue
            if diffs[i - 1] == 0.0:
                continue
            if diffs[i] * diffs[i - 1] < 0:
                sign_changes += 1
        oscillation = _safe_div(sign_changes, max(len(diffs) - 1, 1))

        return {
            "trend": trend,
            "acceleration": acceleration,
            "volatility": volatility,
            "oscillation": oscillation,
        }

    def step(
        self,
        graph: nx.Graph,
        bayes_inference: Dict[str, Dict[str, Any]],
        external_shocks: Dict[str, float] | None = None,
        alpha: float | None = None,
    ) -> Dict[str, Dict[str, float]]:
        used_alpha = _clamp(alpha if alpha is not None else self.base_alpha, 0.1, 0.3)
        shocks = external_shocks or {}
        next_risk: Dict[str, float] = {}
        diagnostics: Dict[str, Dict[str, float]] = {}

        for node in graph.nodes:
            node_id = str(node)
            attrs = graph.nodes[node_id]
            current = float(attrs.get("risk", 0.0))

            neighbors = list(graph.neighbors(node_id))
            if neighbors:
                weighted_sum = 0.0
                weight_total = 0.0
                for nb in neighbors:
                    w = float(graph.edges[node_id, nb].get("weight", 1.0))
                    weighted_sum += w * float(graph.nodes[nb].get("risk", 0.0))
                    weight_total += w
                neighbor_component = _safe_div(weighted_sum, weight_total)
            else:
                neighbor_component = current

            causal = float(bayes_inference[node_id]["posterior_risk"])
            shock = float(shocks.get(node_id, 0.0))
            updated = (1.0 - used_alpha) * current + used_alpha * neighbor_component
            updated = _clamp(0.55 * updated + 0.35 * causal + 0.10 * shock)
            next_risk[node_id] = updated

        for node_id, value in next_risk.items():
            graph.nodes[node_id]["risk"] = value
            self._append_history(graph, node_id)

            history = list(graph.nodes[node_id].get("risk_history", []))
            stats = self._temporal_stats(history)
            instability = _clamp(float(graph.nodes[node_id].get("instability", 0.0)))
            if stats["trend"] > 0.01:
                instability = _clamp(instability + min(0.18, stats["trend"] * 2.0))
            elif stats["trend"] < -0.01:
                instability = _clamp(instability - min(0.12, abs(stats["trend"]) * 1.8))
            if stats["oscillation"] > 0.5:
                instability = _clamp(instability + 0.08)

            graph.nodes[node_id]["instability"] = instability
            diagnostics[node_id] = {
                "trend": stats["trend"],
                "acceleration": stats["acceleration"],
                "volatility": stats["volatility"],
                "oscillation": stats["oscillation"],
                "instability": instability,
            }

        return diagnostics


class QLearningInterventionAgent:
    """Simple tabular Q-learning agent for intervention choices."""

    def __init__(self, lr: float = 0.15, gamma: float = 0.9, epsilon: float = 0.2) -> None:
        self.lr = _clamp(lr, 0.0, 1.0)
        self.gamma = _clamp(gamma, 0.0, 1.0)
        self.epsilon = _clamp(epsilon, 0.0, 1.0)
        self.q: Dict[Tuple[str, str], float] = {}

    def _state(self, graph: nx.Graph) -> str:
        risks = [float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes]
        avg = sum(risks) / max(len(risks), 1)
        high = sum(1 for r in risks if r > 0.7)
        return f"avg:{round(avg,1)}|high:{high}"

    def _actions(self, graph: nx.Graph) -> List[str]:
        nodes = list(graph.nodes)
        acts: List[str] = []
        for n in nodes:
            acts.append(f"reduce_risk:{n}")
            acts.append(f"increase_income:{n}")
        # adjust strongest existing connection by reducing influence a bit
        for u, v in graph.edges:
            acts.append(f"adjust_connection:{u}:{v}")
        return acts

    def _apply_action(self, graph: nx.Graph, action: str) -> float:
        parts = action.split(":")
        cost = 0.0
        if parts[0] == "reduce_risk":
            n = parts[1]
            graph.nodes[n]["risk"] = _clamp(float(graph.nodes[n].get("risk", 0.0)) - 0.12)
            cost = 0.08
        elif parts[0] == "increase_income":
            n = parts[1]
            graph.nodes[n]["income"] = float(graph.nodes[n].get("income", 0.0)) + 350.0
            # reflect income improvement in immediate risk signal
            graph.nodes[n]["risk"] = predict_single_user_risk(
                income=float(graph.nodes[n].get("income", 0.0)),
                activity=float(graph.nodes[n].get("activity", 0.0)),
                transaction_variability=float(graph.nodes[n].get("transaction_variability", 0.0)),
            )
            cost = 0.12
        elif parts[0] == "adjust_connection" and len(parts) == 3:
            u, v = parts[1], parts[2]
            if graph.has_edge(u, v):
                w = float(graph.edges[u, v].get("weight", 1.0))
                graph.edges[u, v]["weight"] = max(0.1, w * 0.85)
                cost = 0.10
        return cost

    def train(
        self,
        graph: nx.Graph,
        temporal_model: TemporalDynamicsModel,
        bayes: BayesianCausalNetwork,
        episodes: int = 40,
        steps_per_episode: int = 3,
    ) -> Dict[str, Any]:
        for _ in range(max(episodes, 1)):
            sim = copy.deepcopy(graph)
            for _ in range(max(steps_per_episode, 1)):
                s = self._state(sim)
                actions = self._actions(sim)
                if random.random() < self.epsilon:
                    a = random.choice(actions)
                else:
                    a = max(actions, key=lambda x: self.q.get((s, x), 0.0))

                cost = self._apply_action(sim, a)
                inf = bayes.infer_all(sim)
                temporal_model.step(sim, inf)
                total_risk = sum(float(sim.nodes[n].get("risk", 0.0)) for n in sim.nodes)
                reward = -total_risk - cost

                s2 = self._state(sim)
                future = max((self.q.get((s2, na), 0.0) for na in self._actions(sim)), default=0.0)
                old = self.q.get((s, a), 0.0)
                self.q[(s, a)] = old + self.lr * (reward + self.gamma * future - old)

        return {"states_learned": len({s for s, _ in self.q.keys()}), "q_entries": len(self.q)}

    def recommend(self, graph: nx.Graph, top_k: int = 5) -> List[Dict[str, Any]]:
        s = self._state(graph)
        actions = self._actions(graph)
        ranked = sorted(actions, key=lambda a: self.q.get((s, a), 0.0), reverse=True)
        return [
            {"action": a, "value": round(self.q.get((s, a), 0.0), 6)}
            for a in ranked[: max(top_k, 1)]
        ]


class GameTheoryInteractionModel:
    """Strategic node behavior via repeated best-response dynamics."""

    def simulate(
        self,
        graph: nx.Graph,
        max_rounds: int = 10,
    ) -> Dict[str, Any]:
        decisions = {str(n): "cooperate" for n in graph.nodes}

        def payoff(node: str, action: str) -> float:
            own = float(graph.nodes[node].get("risk", 0.0))
            neighbors = list(graph.neighbors(node))
            if neighbors:
                neigh = sum(float(graph.nodes[n].get("risk", 0.0)) for n in neighbors) / len(neighbors)
            else:
                neigh = own
            system_stability = 1.0 - min(1.0, sum(float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes) / max(len(graph.nodes), 1))

            if action == "cooperate":
                return -own - 0.4 * neigh + 0.3 * system_stability
            return 0.2 - own - 0.1 * neigh - 0.2 * system_stability

        stable_round = 0
        for _ in range(max(max_rounds, 1)):
            changed = 0
            new_decisions: Dict[str, str] = {}
            for node in graph.nodes:
                node_id = str(node)
                coop = payoff(node_id, "cooperate")
                defect = payoff(node_id, "defect")
                best = "cooperate" if coop >= defect else "defect"
                new_decisions[node_id] = best
                if best != decisions[node_id]:
                    changed += 1

            decisions = new_decisions
            for node_id, choice in decisions.items():
                risk = float(graph.nodes[node_id].get("risk", 0.0))
                if choice == "cooperate":
                    graph.nodes[node_id]["risk"] = _clamp(risk - 0.04)
                else:
                    graph.nodes[node_id]["risk"] = _clamp(risk + 0.04)

            if changed == 0:
                stable_round += 1
                if stable_round >= 2:
                    break

        avg_risk = sum(float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes) / max(len(graph.nodes), 1)
        return {
            "decisions": decisions,
            "nash_like_equilibrium": stable_round >= 1,
            "post_game_average_risk": round(avg_risk, 6),
        }


class StochasticShockModel:
    """Randomized income/default/external shock process."""

    def apply_random_shocks(
        self,
        graph: nx.Graph,
        seed: int | None = None,
        p_income_drop: float = 0.20,
        p_default: float = 0.10,
        p_external: float = 0.15,
    ) -> Dict[str, Any]:
        rng = random.Random(seed)
        base = {str(n): float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes}
        shock_map: Dict[str, float] = {str(n): 0.0 for n in graph.nodes}

        for node in graph.nodes:
            node_id = str(node)
            if rng.random() < p_income_drop:
                graph.nodes[node_id]["income"] = max(0.0, float(graph.nodes[node_id].get("income", 0.0)) * rng.uniform(0.55, 0.85))
                shock_map[node_id] += 0.10
            if rng.random() < p_default:
                shock_map[node_id] += 0.18
            if rng.random() < p_external:
                shock_map[node_id] += 0.08

            graph.nodes[node_id]["risk"] = _clamp(float(graph.nodes[node_id].get("risk", 0.0)) + shock_map[node_id])

        affected = [n for n in graph.nodes if float(graph.nodes[n].get("risk", 0.0)) - base[str(n)] > 0.05]
        total_inc = sum(max(float(graph.nodes[n].get("risk", 0.0)) - base[str(n)], 0.0) for n in graph.nodes)
        return {
            "shock_map": shock_map,
            "cascade_size": len(affected),
            "expected_system_impact": round(total_inc, 6),
            "affected_nodes": [str(n) for n in affected],
        }


def compute_advanced_graph_metrics(graph: nx.Graph) -> List[Dict[str, Any]]:
    if graph.number_of_nodes() == 0:
        return []

    degree = nx.degree_centrality(graph)
    between = nx.betweenness_centrality(graph)
    if graph.number_of_edges() > 0:
        try:
            pagerank = nx.pagerank(graph, weight="weight")
        except Exception:
            # Fallback when scipy backend is unavailable.
            total_degree = sum(float(d) for _, d in graph.degree())
            pagerank = {
                n: _safe_div(float(graph.degree(n)), total_degree) if total_degree > 0 else 0.0
                for n in graph.nodes
            }
    else:
        pagerank = {n: 0.0 for n in graph.nodes}
    try:
        eigen = nx.eigenvector_centrality(graph, max_iter=500, weight="weight")
    except Exception:
        eigen = {n: 0.0 for n in graph.nodes}
    clustering = nx.clustering(graph, weight="weight")

    rows = []
    for node in graph.nodes:
        nid = str(node)
        risk = float(graph.nodes[nid].get("risk", 0.0))
        hub = 0.45 * risk + 0.20 * float(eigen.get(nid, 0.0)) + 0.20 * float(pagerank.get(nid, 0.0)) + 0.15 * float(between.get(nid, 0.0))
        rows.append(
            {
                "node": nid,
                "risk": round(risk, 6),
                "degree_centrality": round(float(degree.get(nid, 0.0)), 6),
                "betweenness_centrality": round(float(between.get(nid, 0.0)), 6),
                "eigenvector_centrality": round(float(eigen.get(nid, 0.0)), 6),
                "pagerank": round(float(pagerank.get(nid, 0.0)), 6),
                "clustering_coefficient": round(float(clustering.get(nid, 0.0)), 6),
                "risk_hub_score": round(hub, 6),
            }
        )

    rows.sort(key=lambda x: x["risk_hub_score"], reverse=True)
    return rows


def compute_global_stability(graph: nx.Graph) -> Dict[str, Any]:
    if graph.number_of_nodes() == 0:
        return {
            "average_risk": 0.0,
            "risk_variance": 0.0,
            "high_risk_nodes": 0,
            "stability_score": 1.0,
            "classification": "stable",
        }

    risks = [float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes]
    avg = sum(risks) / len(risks)
    var = sum((r - avg) ** 2 for r in risks) / len(risks)
    high = sum(1 for r in risks if r > 0.7)
    high_ratio = high / len(risks)
    stability = 1.0 - min(0.55 * avg + 0.25 * min(var * 4.0, 1.0) + 0.20 * high_ratio, 1.0)

    if stability >= 0.65:
        cls = "stable"
    elif stability >= 0.40:
        cls = "fragile"
    else:
        cls = "critical"

    return {
        "average_risk": round(avg, 6),
        "risk_variance": round(var, 6),
        "high_risk_nodes": high,
        "stability_score": round(stability, 6),
        "classification": cls,
    }


def detect_system_criticality(
    graph: nx.Graph,
    previous_average_risk: float | None,
    cascade_size: int,
    avg_threshold: float = 0.68,
    rapid_threshold: float = 0.08,
    cascade_ratio_threshold: float = 0.45,
) -> Dict[str, Any]:
    metrics = compute_global_stability(graph)
    avg_risk = float(metrics["average_risk"])
    node_count = max(graph.number_of_nodes(), 1)

    rapid = previous_average_risk is not None and (avg_risk - previous_average_risk) >= rapid_threshold
    large_cascade = cascade_size >= int(cascade_ratio_threshold * node_count)
    high_avg = avg_risk > avg_threshold

    warning = bool(rapid or large_cascade or high_avg)
    signals = []
    if high_avg:
        signals.append("average risk above threshold")
    if rapid:
        signals.append("rapid risk increase")
    if large_cascade:
        signals.append("large cascade detected")

    ranked = compute_advanced_graph_metrics(graph)
    critical_nodes = [row["node"] for row in ranked[:5]]
    return {
        "early_warning": warning,
        "signals": signals,
        "critical_nodes": critical_nodes,
        "classification": metrics["classification"],
    }


def multi_objective_optimize_interventions(
    graph: nx.Graph,
    top_candidates: int = 6,
    max_set_size: int = 2,
    weight_risk: float = 0.75,
    weight_cost: float = 0.25,
) -> Dict[str, Any]:
    ranked = compute_advanced_graph_metrics(graph)[: max(top_candidates, 1)]
    nodes = [row["node"] for row in ranked]
    baseline = sum(float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes)

    candidates: List[Dict[str, Any]] = []

    for k in range(1, max(max_set_size, 1) + 1):
        for combo in combinations(nodes, k):
            sim = copy.deepcopy(graph)
            cost = 0.0
            for n in combo:
                risk = float(sim.nodes[n].get("risk", 0.0))
                sim.nodes[n]["risk"] = _clamp(risk * 0.72)
                cost += 0.10 + 0.04 * k

            # one weighted diffusion pass
            next_risk: Dict[str, float] = {}
            alpha = 0.2
            for n in sim.nodes:
                own = float(sim.nodes[n].get("risk", 0.0))
                neigh = list(sim.neighbors(n))
                if neigh:
                    ws = 0.0
                    wt = 0.0
                    for nb in neigh:
                        w = float(sim.edges[n, nb].get("weight", 1.0))
                        ws += w * float(sim.nodes[nb].get("risk", 0.0))
                        wt += w
                    avg = _safe_div(ws, wt)
                else:
                    avg = own
                next_risk[n] = _clamp((1.0 - alpha) * own + alpha * avg)
            for n, rv in next_risk.items():
                sim.nodes[n]["risk"] = rv

            total = sum(float(sim.nodes[n].get("risk", 0.0)) for n in sim.nodes)
            reduction = baseline - total
            objective = weight_risk * reduction - weight_cost * cost
            candidates.append(
                {
                    "nodes": list(combo),
                    "total_risk": round(total, 6),
                    "risk_reduction": round(reduction, 6),
                    "cost": round(cost, 6),
                    "objective": round(objective, 6),
                }
            )

    # Pareto front: maximize reduction, minimize cost
    pareto: List[Dict[str, Any]] = []
    for c in candidates:
        dominated = False
        for other in candidates:
            if other is c:
                continue
            if (
                float(other["risk_reduction"]) >= float(c["risk_reduction"])
                and float(other["cost"]) <= float(c["cost"])
                and (
                    float(other["risk_reduction"]) > float(c["risk_reduction"])
                    or float(other["cost"]) < float(c["cost"])
                )
            ):
                dominated = True
                break
        if not dominated:
            pareto.append(c)

    candidates.sort(key=lambda x: x["objective"], reverse=True)
    pareto.sort(key=lambda x: (x["risk_reduction"], -x["cost"]), reverse=True)

    return {
        "best_weighted_solution": candidates[0] if candidates else {},
        "pareto_solutions": pareto[:10],
        "evaluated_candidates": len(candidates),
    }


def generate_advanced_explanations(
    graph: nx.Graph,
    bayes_results: Dict[str, Dict[str, Any]],
    temporal_stats: Dict[str, Dict[str, float]],
    recommended_actions: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    explanations: Dict[str, Dict[str, Any]] = {}
    action_text = [a["action"] for a in recommended_actions[:3]]

    for node in graph.nodes:
        nid = str(node)
        b = bayes_results.get(nid, {})
        t = temporal_stats.get(nid, {})
        factors = b.get("factors", {})

        explanations[nid] = {
            "causal_probability_explanation": {
                "posterior_risk": round(float(b.get("posterior_risk", 0.0)), 6),
                "confidence": round(float(b.get("confidence", 0.0)), 6),
                "factors": factors,
            },
            "contribution_breakdown": {
                "income_low": round(float(factors.get("income_low", 0.0)), 6),
                "activity_low": round(float(factors.get("activity_low", 0.0)), 6),
                "neighbor_high": round(float(factors.get("neighbor_high", 0.0)), 6),
                "trend_up": round(float(factors.get("trend_up", 0.0)), 6),
            },
            "temporal_trend_explanation": {
                "trend": round(float(t.get("trend", 0.0)), 6),
                "acceleration": round(float(t.get("acceleration", 0.0)), 6),
                "volatility": round(float(t.get("volatility", 0.0)), 6),
                "oscillation": round(float(t.get("oscillation", 0.0)), 6),
                "instability": round(float(graph.nodes[nid].get("instability", 0.0)), 6),
            },
            "intervention_impact_explanation": {
                "recommended_actions_context": action_text,
                "current_risk": round(float(graph.nodes[nid].get("risk", 0.0)), 6),
            },
        }

    return explanations


class ResearchDCCFESystem:
    """Research-grade DCCFE orchestration with adaptive probabilistic dynamics."""

    def __init__(self) -> None:
        self.bayesian = BayesianCausalNetwork()
        self.temporal = TemporalDynamicsModel()
        self.rl_agent = QLearningInterventionAgent()
        self.game_model = GameTheoryInteractionModel()
        self.shock_model = StochasticShockModel()
        self.last_average_risk: float | None = None

    def run_cycle(
        self,
        graph: nx.Graph,
        shock_seed: int | None = None,
        manual_shocks: Dict[str, float] | None = None,
        rl_episodes: int = 30,
    ) -> Dict[str, Any]:
        # Bayesian causal inference
        bayes_before = self.bayesian.infer_all(graph)

        # Stochastic shock process
        shock_result = self.shock_model.apply_random_shocks(graph, seed=shock_seed)
        external = dict(shock_result.get("shock_map", {}))
        if manual_shocks:
            for k, v in manual_shocks.items():
                external[str(k)] = external.get(str(k), 0.0) + float(v)

        # Temporal update with adaptive shocks
        temporal_stats = self.temporal.step(graph, bayes_before, external_shocks=external)

        # Game-theory strategic interaction
        game_result = self.game_model.simulate(graph)

        # Adaptive Bayesian update
        bayes_after = self.bayesian.infer_all(graph)
        self.bayesian.update_from_observations(bayes_after, graph)

        # RL learning and policy extraction
        rl_train = self.rl_agent.train(graph, self.temporal, self.bayesian, episodes=rl_episodes)
        recommendations = self.rl_agent.recommend(graph, top_k=6)

        # Advanced metrics and criticality
        graph_metrics = compute_advanced_graph_metrics(graph)
        stability = compute_global_stability(graph)
        criticality = detect_system_criticality(
            graph,
            previous_average_risk=self.last_average_risk,
            cascade_size=int(shock_result.get("cascade_size", 0)),
        )
        self.last_average_risk = float(stability["average_risk"])

        # Multi-objective optimization
        optimization = multi_objective_optimize_interventions(graph)

        # Explainability bundle
        explanations = generate_advanced_explanations(
            graph,
            bayes_results=bayes_after,
            temporal_stats=temporal_stats,
            recommended_actions=recommendations,
        )

        return {
            "bayesian_inference": bayes_after,
            "bayesian_confidence": {n: bayes_after[n]["confidence"] for n in bayes_after},
            "temporal_stats": temporal_stats,
            "shock_result": shock_result,
            "game_theory": game_result,
            "rl_training": rl_train,
            "learned_policy": recommendations,
            "advanced_graph_metrics": graph_metrics,
            "stability_metrics": stability,
            "criticality": criticality,
            "multi_objective": optimization,
            "explanations": explanations,
        }
