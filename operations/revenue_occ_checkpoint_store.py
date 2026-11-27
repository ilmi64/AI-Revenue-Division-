"""Offline local OCC checkpoint persistence; NOT independent trusted custody."""
from __future__ import annotations

from pathlib import Path
import re
import sqlite3

from revenue_occ_replay_guard import ReplayState, assess_replay

HEX = re.compile(r"[0-9a-f]{64}\Z")


class LocalOCCCheckpointStore:
    """Single-host SQLite compare-and-swap rehearsal, no network or authorization."""

    def __init__(self, path: Path):
        if not isinstance(path, Path) or str(path) == ":memory:":
            raise ValueError("persistent SQLite path required")
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("""CREATE TABLE IF NOT EXISTS checkpoint (
                company TEXT PRIMARY KEY,
                sequence INTEGER NOT NULL,
                payload_sha256 TEXT NOT NULL
            )""")

    def read(self) -> ReplayState | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT sequence,payload_sha256 FROM checkpoint WHERE company=?",
                ("Aevora AI Revenue",)
            ).fetchone()
        return ReplayState(*row) if row else None

    def accept(self, payload: bytes, pinned_digest: str) -> tuple[str, tuple[str, ...]]:
        """Atomically reject replay/rollback. The pin MUST come from trusted custody."""
        with sqlite3.connect(self.path, timeout=5) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT sequence,payload_sha256 FROM checkpoint WHERE company=?",
                ("Aevora AI Revenue",)
            ).fetchone()
            if row is not None and (
                type(row[0]) is not int or row[0] < 0
                or not isinstance(row[1], str) or not HEX.fullmatch(row[1])
            ):
                return "REJECT", ("stored_checkpoint_invalid",)
            prior = ReplayState(*row) if row else None
            decision = assess_replay(payload, pinned_digest, prior)
            if decision.status != "READ_ONLY_NEW_REPORT" or decision.next_state is None:
                return "REJECT", decision.blockers
            next_state = decision.next_state
            db.execute(
                """INSERT INTO checkpoint(company,sequence,payload_sha256)
                   VALUES (?,?,?)
                   ON CONFLICT(company) DO UPDATE SET
                     sequence=excluded.sequence,payload_sha256=excluded.payload_sha256""",
                ("Aevora AI Revenue", next_state.sequence, next_state.payload_sha256)
            )
        return "READ_ONLY_STORED", decision.blockers
