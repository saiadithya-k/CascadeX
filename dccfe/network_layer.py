from __future__ import annotations

from typing import Iterable

import networkx as nx

from .models import Relationship, UserRecord


class NetworkLayer:
    def __init__(self) -> None:
        self.graph = nx.Graph()

    def add_users(self, users: Iterable[UserRecord]) -> None:
        for user in users:
            self.graph.add_node(
                user.user_id,
                income=float(user.income),
                activity=float(user.activity),
                transactions=int(user.transactions),
                defaults=int(user.defaults),
                base_risk=0.0,
                risk=0.0,
                instability=0.0,
                explanation=[],
            )

    def upsert_user(self, user: UserRecord) -> None:
        self.graph.add_node(
            user.user_id,
            income=float(user.income),
            activity=float(user.activity),
            transactions=int(user.transactions),
            defaults=int(user.defaults),
            base_risk=float(self.graph.nodes[user.user_id].get("base_risk", 0.0)) if user.user_id in self.graph else 0.0,
            risk=float(self.graph.nodes[user.user_id].get("risk", 0.0)) if user.user_id in self.graph else 0.0,
            instability=float(self.graph.nodes[user.user_id].get("instability", 0.0)) if user.user_id in self.graph else 0.0,
            explanation=list(self.graph.nodes[user.user_id].get("explanation", [])) if user.user_id in self.graph else [],
        )

    def add_relationships(self, relationships: Iterable[Relationship]) -> None:
        for rel in relationships:
            if rel.source not in self.graph or rel.target not in self.graph:
                continue
            self.graph.add_edge(
                rel.source,
                rel.target,
                weight=max(float(rel.weight), 0.0),
                relation_type=rel.relation_type,
            )

    def upsert_relationship(self, rel: Relationship) -> None:
        if rel.source not in self.graph or rel.target not in self.graph:
            raise KeyError("Both users must exist before creating a relationship")
        self.graph.add_edge(
            rel.source,
            rel.target,
            weight=max(float(rel.weight), 0.0),
            relation_type=rel.relation_type,
        )

    def update_user(self, user_id: str, **attrs: float) -> None:
        if user_id not in self.graph:
            raise KeyError(f"Unknown user: {user_id}")
        for key, value in attrs.items():
            self.graph.nodes[user_id][key] = value
