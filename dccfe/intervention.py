from __future__ import annotations

import copy
from typing import Callable, Dict, List, Tuple

import networkx as nx

from .graph_reasoning import propagate_risk_steps


class InterventionEngine:
    def most_critical_node(self, graph: nx.Graph) -> str:
        centrality = nx.degree_centrality(graph) if graph.number_of_nodes() > 1 else {}
        scored_nodes: List[Tuple[str, float]] = []
        for node, data in graph.nodes(data=True):
            risk = float(data.get("risk", 0.0))
            score = risk * (1.0 + float(centrality.get(node, 0.0)))
            scored_nodes.append((node, score))
        scored_nodes.sort(key=lambda item: item[1], reverse=True)
        return scored_nodes[0][0] if scored_nodes else ""

    def rank_interventions(
        self,
        graph: nx.Graph,
        simulation_callback: Callable[[str], float],
        top_k: int = 3,
    ) -> List[Dict[str, float]]:
        baseline_risk = sum(float(data.get("risk", 0.0)) for _, data in graph.nodes(data=True))
        candidates: List[Dict[str, float]] = []

        for node in graph.nodes:
            new_total_risk = simulation_callback(node)
            reduction = baseline_risk - new_total_risk
            candidates.append(
                {
                    "node": node,
                    "systemic_risk_reduction": round(reduction, 6),
                    "expected_total_risk": round(new_total_risk, 6),
                }
            )

        candidates.sort(key=lambda item: item["systemic_risk_reduction"], reverse=True)
        return candidates[:top_k]

    def optimize_intervention(
        self,
        graph: nx.Graph,
        risk_reduction_factor: float = 0.30,
        propagation_factor: float = 0.2,
        steps: int = 4,
    ) -> Dict[str, float | str]:
        """Find node whose temporary risk reduction maximally lowers network risk."""
        if graph.number_of_nodes() == 0:
            return {
                "best_node": "",
                "impact_score": 0.0,
                "baseline_total_risk": 0.0,
                "optimized_total_risk": 0.0,
            }

        baseline = sum(float(data.get("risk", 0.0)) for _, data in graph.nodes(data=True))
        best_node = ""
        best_total = baseline

        for node in graph.nodes:
            simulated = copy.deepcopy(graph)
            current = float(simulated.nodes[node].get("risk", 0.0))
            simulated.nodes[node]["risk"] = max(0.0, current * (1.0 - risk_reduction_factor))
            propagate_risk_steps(
                simulated,
                propagation_factor=propagation_factor,
                steps=steps,
            )
            total = sum(float(data.get("risk", 0.0)) for _, data in simulated.nodes(data=True))
            if total < best_total:
                best_total = total
                best_node = str(node)

        return {
            "best_node": best_node,
            "impact_score": round(baseline - best_total, 6),
            "baseline_total_risk": round(baseline, 6),
            "optimized_total_risk": round(best_total, 6),
        }

    def rank_critical_nodes(self, graph: nx.Graph, top_k: int = 5) -> List[Dict[str, float | str]]:
        """Rank influential nodes using risk and centrality metrics."""
        if graph.number_of_nodes() == 0:
            return []

        degree = nx.degree_centrality(graph)
        between = nx.betweenness_centrality(graph)
        rows: List[Dict[str, float | str]] = []

        for node, data in graph.nodes(data=True):
            risk = float(data.get("risk", 0.0))
            degree_score = float(degree.get(node, 0.0))
            between_score = float(between.get(node, 0.0))
            combined = 0.60 * risk + 0.25 * degree_score + 0.15 * between_score
            rows.append(
                {
                    "node": str(node),
                    "risk": round(risk, 6),
                    "degree_centrality": round(degree_score, 6),
                    "betweenness_centrality": round(between_score, 6),
                    "combined_score": round(combined, 6),
                }
            )

        rows.sort(key=lambda item: float(item["combined_score"]), reverse=True)
        return rows[:top_k]

    def optimize_multi_node_intervention(
        self,
        graph: nx.Graph,
        k: int = 2,
        risk_reduction_factor: float = 0.30,
        propagation_factor: float = 0.2,
        steps: int = 4,
    ) -> Dict[str, float | List[str]]:
        """Greedy multi-node optimization to minimize total network risk."""
        if graph.number_of_nodes() == 0 or k <= 0:
            return {
                "best_nodes": [],
                "improvement_score": 0.0,
                "baseline_total_risk": 0.0,
                "optimized_total_risk": 0.0,
            }

        baseline = sum(float(data.get("risk", 0.0)) for _, data in graph.nodes(data=True))
        selected: List[str] = []
        available = set(str(node) for node in graph.nodes)
        current_best_total = baseline
        iterations = min(k, len(available))

        for _ in range(iterations):
            best_candidate = ""
            best_candidate_total = current_best_total

            for candidate in list(available):
                simulated = copy.deepcopy(graph)
                for node in selected + [candidate]:
                    current = float(simulated.nodes[node].get("risk", 0.0))
                    simulated.nodes[node]["risk"] = max(0.0, current * (1.0 - risk_reduction_factor))

                propagate_risk_steps(
                    simulated,
                    propagation_factor=propagation_factor,
                    steps=steps,
                )
                total = sum(float(data.get("risk", 0.0)) for _, data in simulated.nodes(data=True))
                if total < best_candidate_total:
                    best_candidate_total = total
                    best_candidate = candidate

            if not best_candidate:
                break
            selected.append(best_candidate)
            available.remove(best_candidate)
            current_best_total = best_candidate_total

        return {
            "best_nodes": selected,
            "improvement_score": round(baseline - current_best_total, 6),
            "baseline_total_risk": round(baseline, 6),
            "optimized_total_risk": round(current_best_total, 6),
        }
