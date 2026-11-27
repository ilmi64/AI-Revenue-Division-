"""Offline evidence custody rehearsal. Not trusted external identity or durable remote custody."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,80}:[0-9]{2}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class EvidenceReceipt:
    sequence: int
    task_id: str
    actor_id: str
    actor_role: str
    artifact_digest: str
    previous_digest: str
    record_digest: str


class LocalEvidenceCustody:
    """Single-host append-only SQLite simulation; cannot grant release authority."""

    def __init__(self, path: Path):
        if not isinstance(path, Path) or str(path) == ":memory:":
            raise ValueError("persistent path required")
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS evidence (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                artifact_digest TEXT NOT NULL,
                previous_digest TEXT NOT NULL,
                record_digest TEXT NOT NULL UNIQUE
            )""")

    @staticmethod
    def _chain_valid(rows) -> bool:
        previous = "0" * 64
        for expected, row in enumerate(rows, 1):
            seq, task, actor, role, artifact, prior, digest = row
            if (seq != expected or prior != previous
                    or not isinstance(artifact, str) or not DIGEST.fullmatch(artifact)):
                return False
            payload = json.dumps([seq, task, actor, role, artifact, prior],
                                 separators=(",", ":"), ensure_ascii=True)
            if hashlib.sha256(payload.encode("ascii")).hexdigest() != digest:
                return False
            previous = digest
        return True

    def append(self, task_id: str, actor_id: str, actor_role: str,
               artifact: bytes) -> EvidenceReceipt:
        if (not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id)
                or not all(isinstance(v, str) and ID.fullmatch(v) for v in
                           (actor_id, actor_role))
                or not isinstance(artifact, bytes) or not 0 < len(artifact) <= 1_000_000):
            raise ValueError("invalid evidence input")
        with sqlite3.connect(self.path, timeout=5) as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT sequence,task_id,actor_id,actor_role,artifact_digest,previous_digest,record_digest FROM evidence ORDER BY sequence").fetchall()
            if not self._chain_valid(rows):
                raise ValueError("existing evidence chain invalid; append blocked")
            last = (rows[-1][0], rows[-1][6]) if rows else None
            seq = last[0] + 1 if last else 1
            previous = last[1] if last else "0" * 64
            artifact_digest = hashlib.sha256(artifact).hexdigest()
            payload = json.dumps([seq, task_id, actor_id, actor_role, artifact_digest, previous],
                                 separators=(",", ":"), ensure_ascii=True)
            digest = hashlib.sha256(payload.encode("ascii")).hexdigest()
            db.execute("INSERT INTO evidence(sequence,task_id,actor_id,actor_role,artifact_digest,previous_digest,record_digest) VALUES (?,?,?,?,?,?,?)",
                       (seq, task_id, actor_id, actor_role, artifact_digest, previous, digest))
        return EvidenceReceipt(seq, task_id, actor_id, actor_role, artifact_digest, previous, digest)

    def head(self) -> tuple[int, str]:
        """Export a checkpoint for independent custody; does not attest to it."""
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT sequence,record_digest FROM evidence ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        return (row[0], row[1]) if row else (0, "0" * 64)

    def verify_anchor(self, expected_sequence: int, expected_digest: str) -> bool:
        """Compare to a separately held, independently authenticated checkpoint.

        Caller MUST establish provenance independently. A self-supplied anchor
        offers no protection against full-chain rewriting or truncation.
        """
        if (type(expected_sequence) is not int or expected_sequence < 0
                or not isinstance(expected_digest, str)
                or not DIGEST.fullmatch(expected_digest)):
            return False
        return self.verify_chain() and self.head() == (expected_sequence, expected_digest)

    def verify_chain(self) -> bool:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT sequence,task_id,actor_id,actor_role,artifact_digest,previous_digest,record_digest FROM evidence ORDER BY sequence").fetchall()
        return self._chain_valid(rows)
