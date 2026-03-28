from __future__ import annotations

from typing import Dict, List

import networkx as nx


class CausalEngine:
    def apply(
        self,
        graph: nx.Graph,
        weight_income: float = 0.30,
        weight_neighbor: float = 0.25,
        weight_activity: float = 0.20,
    ) -> Dict[str, List[str]]:
        weight_sum = weight_income + weight_neighbor + weight_activity
        if weight_sum > 1.0:
            raise ValueError("Causal weights must sum to <= 1.0")

        explanations: Dict[str, List[str]] = {}
        updates: Dict[str, float] = {}

        for node, data in graph.nodes(data=True):
            reasons: List[str] = []
            base_risk = min(max(float(data.get("risk", 0.0)), 0.0), 1.0)

            # Income effect: lower income -> higher normalized contribution.
            income = float(data.get("income", 0.0))
            income_min = 1500.0
            income_max = 9000.0
            income_norm = min(max((income - income_min) / max(income_max - income_min, 1.0), 0.0), 1.0)
            income_effect = 1.0 - income_norm

            # Activity effect: lower activity -> higher normalized contribution.
            activity = float(data.get("activity", 0.0))
            activity_effect = 1.0 - min(max(activity, 0.0), 1.0)

            # Neighbor effect: average neighbor risk as normalized pressure.
            neighbors = list(graph.neighbors(node))
            neighbor_effect = 0.0
            if neighbors:
                neighbor_effect = sum(float(graph.nodes[n].get("risk", 0.0)) for n in neighbors) / len(neighbors)
                neighbor_effect = min(max(neighbor_effect, 0.0), 1.0)

            contrib_income = weight_income * income_effect
            contrib_neighbor = weight_neighbor * neighbor_effect
            contrib_activity = weight_activity * activity_effect

            adjusted_risk = base_risk + contrib_income + contrib_neighbor + contrib_activity
            updates[node] = min(max(adjusted_risk, 0.0), 1.0)

            reasons.append(
                f"base={base_risk:.4f}, income_contrib={contrib_income:.4f}, "
                f"neighbor_contrib={contrib_neighbor:.4f}, activity_contrib={contrib_activity:.4f}"
            )
            reasons.append(
                f"income_effect={income_effect:.4f}, neighbor_effect={neighbor_effect:.4f}, activity_effect={activity_effect:.4f}"
            )
            explanations[node] = reasons

        for node, value in updates.items():
            graph.nodes[node]["risk"] = value
            graph.nodes[node]["instability"] = 1.0 - min(max(float(graph.nodes[node].get("activity", 0.0)), 0.0), 1.0)

        return explanations
