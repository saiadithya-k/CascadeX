from __future__ import annotations

import copy
import random
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .blockchain import EventBlockchain
from .causal_engine import CausalEngine
from .cognitive import CognitiveEngine
from .intervention import InterventionEngine
from .models import Relationship, UserRecord
from .network_layer import NetworkLayer
from .propagation import RiskPropagationEngine


class DCCFEEngine:
    def __init__(
        self,
        min_users_for_compute: int = 5,
        max_users: int | None = None,
        max_logged_risk_updates: int = 100,
    ) -> None:
        self.network = NetworkLayer()
        self.cognitive = CognitiveEngine()
        self.causal = CausalEngine()
        self.propagation = RiskPropagationEngine()
        self.intervention = InterventionEngine()
        self.blockchain = EventBlockchain()
        self.min_users_for_compute = max(1, int(min_users_for_compute))
        self.max_users = int(max_users) if max_users is not None else None
        self.max_logged_risk_updates = max(1, int(max_logged_risk_updates))

    @property
    def graph(self):
        return self.network.graph

    def load_users(self, users: Iterable[UserRecord]) -> None:
        users = list(users)
        if len(users) < self.min_users_for_compute:
            raise ValueError(f"DCCFE requires at least {self.min_users_for_compute} users")
        if self.max_users is not None and len(users) > self.max_users:
            raise ValueError(f"DCCFE supports up to {self.max_users} users")
        self.network.add_users(users)
        self.blockchain.add_event("USERS_LOADED", {"count": len(users)})

    def load_relationships(self, relationships: Iterable[Relationship]) -> None:
        relationships = list(relationships)
        self.network.add_relationships(relationships)
        self.blockchain.add_event("RELATIONSHIPS_LOADED", {"count": len(relationships)})

    def upsert_user(self, user: UserRecord) -> None:
        is_new = user.user_id not in self.graph
        if is_new and self.max_users is not None and self.graph.number_of_nodes() >= self.max_users:
            raise ValueError(f"DCCFE supports up to {self.max_users} users")
        self.network.upsert_user(user)
        self.blockchain.add_event(
            "USER_UPSERTED",
            {
                "user_id": user.user_id,
                "income": float(user.income),
                "activity": float(user.activity),
                "transactions": int(user.transactions),
                "defaults": int(user.defaults),
                "is_new": is_new,
            },
        )

    def upsert_relationship(self, relationship: Relationship) -> None:
        self.network.upsert_relationship(relationship)
        self.blockchain.add_event(
            "RELATIONSHIP_UPSERTED",
            {
                "source": relationship.source,
                "target": relationship.target,
                "weight": float(relationship.weight),
                "relation_type": relationship.relation_type,
            },
        )

    def process_realtime_event(self, event: Dict[str, Any]) -> None:
        event_type = str(event.get("type", "")).upper()
        payload = dict(event.get("payload", {}))

        if event_type == "USER_UPSERT":
            self.upsert_user(
                UserRecord(
                    user_id=str(payload["user_id"]),
                    income=float(payload["income"]),
                    activity=float(payload["activity"]),
                    transactions=int(payload["transactions"]),
                    defaults=int(payload.get("defaults", 0)),
                )
            )
        elif event_type == "RELATIONSHIP_UPSERT":
            self.upsert_relationship(
                Relationship(
                    source=str(payload["source"]),
                    target=str(payload["target"]),
                    weight=float(payload.get("weight", 1.0)),
                    relation_type=str(payload.get("relation_type", "similarity")),
                )
            )
        elif event_type == "IOT_UPDATE":
            self.apply_iot_update(
                user_id=str(payload["user_id"]),
                income_delta=float(payload.get("income_delta", 0.0)),
                activity_delta=float(payload.get("activity_delta", 0.0)),
                transaction_delta=int(payload.get("transaction_delta", 0)),
                default_event=bool(payload.get("default_event", False)),
            )
            return
        else:
            raise ValueError(f"Unsupported event type: {event_type}")

        if self.graph.number_of_nodes() >= self.min_users_for_compute:
            self.recompute()

    def _score_cognitive_layer(self) -> Dict[str, List[str]]:
        all_reasons: Dict[str, List[str]] = {}
        for node, data in self.graph.nodes(data=True):
            risk, reasons = self.cognitive.score_user(
                income=float(data.get("income", 0.0)),
                activity=float(data.get("activity", 0.0)),
                transactions=int(data.get("transactions", 0)),
                defaults=int(data.get("defaults", 0)),
            )
            self.graph.nodes[node]["base_risk"] = risk
            self.graph.nodes[node]["risk"] = risk
            all_reasons[node] = list(reasons)
        return all_reasons

    def recompute(self, propagation_steps: int = 3) -> Dict[str, List[str]]:
        if self.graph.number_of_nodes() < self.min_users_for_compute:
            raise ValueError(f"DCCFE requires at least {self.min_users_for_compute} users before risk computation")
        cognitive_reasons = self._score_cognitive_layer()
        causal_reasons = self.causal.apply(self.graph)
        self.propagation.propagate(self.graph, steps=min(max(int(propagation_steps), 1), 10))

        explanations: Dict[str, List[str]] = {}
        nodes = list(self.graph.nodes)
        log_targets = set(nodes[: self.max_logged_risk_updates])
        for node in nodes:
            combined = cognitive_reasons.get(node, []) + causal_reasons.get(node, [])
            explanations[node] = combined
            self.graph.nodes[node]["explanation"] = combined
            if node in log_targets:
                self.blockchain.add_event(
                    "RISK_UPDATED",
                    {
                        "node": node,
                        "risk": round(float(self.graph.nodes[node].get("risk", 0.0)), 6),
                        "reasons": combined,
                    },
                )

        if len(nodes) > self.max_logged_risk_updates:
            self.blockchain.add_event(
                "RISK_UPDATE_SUMMARY",
                {
                    "logged_nodes": self.max_logged_risk_updates,
                    "total_nodes": len(nodes),
                },
            )
        return explanations

    def apply_iot_update(
        self,
        user_id: str,
        income_delta: float = 0.0,
        activity_delta: float = 0.0,
        transaction_delta: int = 0,
        default_event: bool = False,
    ) -> None:
        if user_id not in self.graph:
            raise KeyError(f"Unknown user: {user_id}")

        node = self.graph.nodes[user_id]
        node["income"] = max(float(node.get("income", 0.0)) + float(income_delta), 0.0)
        node["activity"] = min(max(float(node.get("activity", 0.0)) + float(activity_delta), 0.0), 1.0)
        node["transactions"] = max(int(node.get("transactions", 0)) + int(transaction_delta), 0)
        if default_event:
            node["defaults"] = int(node.get("defaults", 0)) + 1

        self.blockchain.add_event(
            "IOT_UPDATE",
            {
                "node": user_id,
                "income_delta": income_delta,
                "activity_delta": activity_delta,
                "transaction_delta": transaction_delta,
                "default_event": default_event,
            },
        )
        self.recompute()

    def random_iot_tick(self) -> Optional[str]:
        nodes = list(self.graph.nodes)
        if not nodes:
            return None
        selected = random.choice(nodes)
        self.apply_iot_update(
            selected,
            income_delta=random.uniform(-200.0, 120.0),
            activity_delta=random.uniform(-0.06, 0.04),
            transaction_delta=random.randint(-1, 2),
            default_event=random.random() < 0.05,
        )
        return selected

    def explain_user(self, user_id: str) -> List[str]:
        if user_id not in self.graph:
            return []
        return list(self.graph.nodes[user_id].get("explanation", []))

    def export_risk_table(self) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for node, data in self.graph.nodes(data=True):
            rows.append(
                {
                    "user_id": node,
                    "income": float(data.get("income", 0.0)),
                    "activity": float(data.get("activity", 0.0)),
                    "transactions": int(data.get("transactions", 0)),
                    "defaults": int(data.get("defaults", 0)),
                    "base_risk": round(float(data.get("base_risk", 0.0)), 6),
                    "risk": round(float(data.get("risk", 0.0)), 6),
                }
            )
        return pd.DataFrame(rows).sort_values(by="risk", ascending=False).reset_index(drop=True)

    def simulate_what_if(self, updates: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        scenario_graph = copy.deepcopy(self.graph)

        for user_id, attrs in updates.items():
            if user_id not in scenario_graph:
                continue
            node = scenario_graph.nodes[user_id]
            if "income" in attrs:
                node["income"] = max(float(attrs["income"]), 0.0)
            if "activity" in attrs:
                node["activity"] = min(max(float(attrs["activity"]), 0.0), 1.0)
            if "transactions" in attrs:
                node["transactions"] = max(int(attrs["transactions"]), 0)

        for node, data in scenario_graph.nodes(data=True):
            risk, _ = self.cognitive.score_user(
                income=float(data.get("income", 0.0)),
                activity=float(data.get("activity", 0.0)),
                transactions=int(data.get("transactions", 0)),
                defaults=int(data.get("defaults", 0)),
            )
            scenario_graph.nodes[node]["risk"] = risk

        self.causal.apply(scenario_graph)
        self.propagation.propagate(scenario_graph, steps=3)

        rows: List[Dict[str, Any]] = []
        for node, data in scenario_graph.nodes(data=True):
            rows.append(
                {
                    "user_id": node,
                    "scenario_risk": round(float(data.get("risk", 0.0)), 6),
                }
            )

        self.blockchain.add_event("WHAT_IF_SIMULATION", {"updates": updates})
        return pd.DataFrame(rows).sort_values(by="scenario_risk", ascending=False).reset_index(drop=True)

    def suggest_interventions(self, top_k: int = 3) -> List[Dict[str, float]]:
        def simulate_support(node_id: str) -> float:
            simulated = copy.deepcopy(self.graph)
            node = simulated.nodes[node_id]
            node["income"] = float(node.get("income", 0.0)) + 400.0
            node["activity"] = min(float(node.get("activity", 0.0)) + 0.12, 1.0)

            for n, data in simulated.nodes(data=True):
                risk, _ = self.cognitive.score_user(
                    income=float(data.get("income", 0.0)),
                    activity=float(data.get("activity", 0.0)),
                    transactions=int(data.get("transactions", 0)),
                    defaults=int(data.get("defaults", 0)),
                )
                simulated.nodes[n]["risk"] = risk
            self.causal.apply(simulated)
            self.propagation.propagate(simulated, steps=2)
            return float(sum(float(data.get("risk", 0.0)) for _, data in simulated.nodes(data=True)))

        ranked = self.intervention.rank_interventions(self.graph, simulate_support, top_k=top_k)
        critical = self.intervention.most_critical_node(self.graph)
        self.blockchain.add_event(
            "INTERVENTIONS_SUGGESTED",
            {
                "critical_node": critical,
                "recommendations": ranked,
            },
        )
        return ranked
