from dataclasses import dataclass


@dataclass
class UserRecord:
    user_id: str
    income: float
    activity: float
    transactions: int
    defaults: int = 0


@dataclass
class Relationship:
    source: str
    target: str
    weight: float = 1.0
    relation_type: str = "similarity"
