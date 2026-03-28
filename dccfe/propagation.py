from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import networkx as nx


class RiskPropagationEngine:
    def propagate(
        self,
        graph: nx.Graph,
        alpha: float = 0.2,
        steps: int = 4,
        shock_nodes: Optional[Iterable[str]] = None,
    ) -> List[Dict[str, float]]:
        alpha = min(max(float(alpha), 0.1), 0.3)
        history: List[Dict[str, float]] = []
        shocks = set(shock_nodes or [])

        for _ in range(max(steps, 1)):
            next_scores: Dict[str, float] = {}
            for node in graph.nodes:
                own_risk = float(graph.nodes[node].get("risk", 0.0))
                neighbors = list(graph.neighbors(node))
                if neighbors:
                    weighted_sum = 0.0
                    weight_total = 0.0
                    for neighbor in neighbors:
                        edge_weight = float(graph.edges[node, neighbor].get("weight", 1.0))
                        weighted_sum += edge_weight * float(graph.nodes[neighbor].get("risk", 0.0))
                        weight_total += edge_weight
                    neighbor_risk = weighted_sum / max(weight_total, 1e-9)
                else:
                    neighbor_risk = own_risk

                # Graph diffusion: blend own risk with average neighbor risk.
                blended = (1.0 - alpha) * own_risk + alpha * neighbor_risk
                if node in shocks:
                    blended = max(blended, 0.9)
                next_scores[node] = min(max(blended, 0.0), 1.0)

            for node, value in next_scores.items():
                graph.nodes[node]["risk"] = value
            history.append(next_scores)

        return history
