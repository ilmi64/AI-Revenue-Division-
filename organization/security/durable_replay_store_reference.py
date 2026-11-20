"""SQLite durable replay-store prototype for trusted receiver evidence.

Offline reference only. Production must use a shared transactional database,
durable backups, restricted roles and tested failover.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

class ReplayError(ValueError):
    pass

class SQLiteReplayStore:
    def __init__(self, path):
        self.path=str(path)
        self.db=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("""
          CREATE TABLE IF NOT EXISTS receiver_evidence_replay (
            issuer TEXT NOT NULL,
            nonce TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            observed_at INTEGER NOT NULL,
            accepted_at INTEGER NOT NULL,
            PRIMARY KEY (issuer, nonce),
            UNIQUE (issuer, evidence_id)
          )
        """)

    def claim(self, *, issuer, nonce, evidence_id, payload_sha256, observed_at, accepted_at):
        fields=(issuer,nonce,evidence_id,payload_sha256)
        if any(not isinstance(x,str) or not x.strip() for x in fields):
            raise ReplayError("invalid_replay_claim")
        if isinstance(observed_at,bool) or not isinstance(observed_at,int):
            raise ReplayError("invalid_observed_at")
        if isinstance(accepted_at,bool) or not isinstance(accepted_at,int):
            raise ReplayError("invalid_accepted_at")
        try:
            self.db.execute("BEGIN IMMEDIATE")
            self.db.execute("""
              INSERT INTO receiver_evidence_replay
              (issuer,nonce,evidence_id,payload_sha256,observed_at,accepted_at)
              VALUES (?,?,?,?,?,?)
            """,(issuer,nonce,evidence_id,payload_sha256,observed_at,accepted_at))
            self.db.execute("COMMIT")
            return True
        except sqlite3.IntegrityError as exc:
            self.db.execute("ROLLBACK")
            raise ReplayError("evidence_nonce_or_id_replayed") from exc
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()
