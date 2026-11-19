"""Offline reference for canonical, hash-linked audit events. Not a production log store."""
from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass
from typing import Any

GENESIS = "0" * 64
SECRET_KEY = re.compile(r"(password|secret|api[_-]?key|private[_-]?key|seed|mnemonic|token|authorization|cookie|signature|credential)", re.I)

class AuditError(ValueError): pass

def _clean(value: Any, path: str = "$") -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if SECRET_KEY.search(str(k)):
                raise AuditError(f"secret-like field forbidden at {path}.{k}")
            out[str(k)] = _clean(v, f"{path}.{k}")
        return out
    if isinstance(value, (list, tuple)):
        return [_clean(v, f"{path}[{i}]") for i, v in enumerate(value)]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        raise AuditError(f"floating-point values forbidden at {path}; use integer minor units or strings")
    raise AuditError(f"unsupported value at {path}: {type(value).__name__}")

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(_clean(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def event_hash(event: dict) -> str:
    return hashlib.sha256(canonical_bytes(event)).hexdigest()

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    sequence: int
    occurred_at: str
    company_id: str
    actor_id: str
    event_type: str
    payload: dict
    previous_hash: str
    hash: str

class InMemoryAuditChain:
    """Deterministic demo only; process memory is neither durable nor tamper-proof."""
    def __init__(self):
        self._events = []

    def append(self, *, event_id: str, occurred_at: str, company_id: str,
               actor_id: str, event_type: str, payload: dict) -> AuditEvent:
        if not all(isinstance(x, str) and x.strip() for x in
                   (event_id, occurred_at, company_id, actor_id, event_type)):
            raise AuditError("required event fields must be non-empty strings")
        if not isinstance(payload, dict):
            raise AuditError("payload must be an object")
        if any(e.event_id == event_id for e in self._events):
            raise AuditError("duplicate event_id")
        prev = self._events[-1].hash if self._events else GENESIS
        body = {"event_id": event_id, "sequence": len(self._events) + 1,
                "occurred_at": occurred_at, "company_id": company_id,
                "actor_id": actor_id, "event_type": event_type,
                "payload": _clean(payload), "previous_hash": prev,
                "hash_algorithm": "sha256"}
        digest = event_hash(body)
        item = AuditEvent(hash=digest, **{k:v for k,v in body.items() if k != "hash_algorithm"})
        self._events.append(item)
        return item

    def export(self) -> list[dict]:
        return [dict(event_id=e.event_id, sequence=e.sequence, occurred_at=e.occurred_at,
                     company_id=e.company_id, actor_id=e.actor_id, event_type=e.event_type,
                     payload=e.payload, previous_hash=e.previous_hash, hash=e.hash)
                for e in self._events]

def verify_chain(events: list[dict]) -> tuple[bool, str]:
    previous = GENESIS
    seen_ids, seen_sequences = set(), set()
    for index, event in enumerate(events, 1):
        try:
            if event.get("sequence") != index: return False, f"sequence_gap_or_reorder:{index}"
            if event.get("event_id") in seen_ids: return False, "duplicate_event_id"
            if event.get("sequence") in seen_sequences: return False, "duplicate_sequence"
            if event.get("previous_hash") != previous: return False, f"previous_hash_mismatch:{index}"
            body = {k:event[k] for k in ("event_id","sequence","occurred_at","company_id","actor_id","event_type","payload","previous_hash")}
            expected = event_hash({**body, "hash_algorithm":"sha256"})
            if event.get("hash") != expected: return False, f"event_hash_mismatch:{index}"
            seen_ids.add(event["event_id"]); seen_sequences.add(event["sequence"]); previous = expected
        except (KeyError, TypeError, AuditError, ValueError):
            return False, f"invalid_event:{index}"
    return True, "ok"
