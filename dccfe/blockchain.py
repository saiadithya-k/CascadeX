from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class Block:
    index: int
    timestamp: float
    event_type: str
    payload: Dict[str, Any]
    previous_hash: str
    hash: str


class EventBlockchain:
    def __init__(self) -> None:
        self.chain: List[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            timestamp=time.time(),
            event_type="GENESIS",
            payload={"message": "DCCFE chain initialized"},
            previous_hash="0",
            hash="",
        )
        genesis.hash = self._hash_block(genesis)
        self.chain.append(genesis)

    def _hash_block(self, block: Block) -> str:
        body = {
            "index": block.index,
            "timestamp": block.timestamp,
            "event_type": block.event_type,
            "payload": block.payload,
            "previous_hash": block.previous_hash,
        }
        encoded = json.dumps(body, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def add_event(self, event_type: str, payload: Dict[str, Any]) -> Block:
        previous = self.chain[-1]
        block = Block(
            index=previous.index + 1,
            timestamp=time.time(),
            event_type=event_type,
            payload=payload,
            previous_hash=previous.hash,
            hash="",
        )
        block.hash = self._hash_block(block)
        self.chain.append(block)
        return block

    def validate(self) -> bool:
        for idx in range(1, len(self.chain)):
            current = self.chain[idx]
            previous = self.chain[idx - 1]
            if current.previous_hash != previous.hash:
                return False
            if current.hash != self._hash_block(current):
                return False
        return True

    def tail(self, count: int = 10) -> List[Dict[str, Any]]:
        return [asdict(block) for block in self.chain[-count:]]


class SimpleHashBlockchain:
    """Simple blockchain-style logger for generic data records."""

    def __init__(self) -> None:
        self.chain: List[Dict[str, Any]] = []
        self.add_block({"message": "GENESIS"})

    def _hash_content(self, payload: Dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def create_block(self, data: Dict[str, Any], previous_hash: str) -> Dict[str, Any]:
        block = {
            "data": data,
            "timestamp": time.time(),
            "previous_hash": previous_hash,
            "hash": "",
        }
        body = {
            "data": block["data"],
            "timestamp": block["timestamp"],
            "previous_hash": block["previous_hash"],
        }
        block["hash"] = self._hash_content(body)
        return block

    def add_block(self, data: Dict[str, Any]) -> Dict[str, Any]:
        previous_hash = self.chain[-1]["hash"] if self.chain else "0"
        block = self.create_block(data=data, previous_hash=previous_hash)
        self.chain.append(block)
        return block

    def verify_chain_integrity(self) -> bool:
        for idx, current in enumerate(self.chain):
            expected_body = {
                "data": current["data"],
                "timestamp": current["timestamp"],
                "previous_hash": current["previous_hash"],
            }
            if current["hash"] != self._hash_content(expected_body):
                return False
            if idx == 0:
                if current["previous_hash"] != "0":
                    return False
                continue
            if current["previous_hash"] != self.chain[idx - 1]["hash"]:
                return False
        return True
