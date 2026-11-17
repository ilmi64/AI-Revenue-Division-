"""Conservative OCC publisher for the current draft governance baseline.

This module intentionally has NO automatic CLEAR path. Until a separately
approved operational control-state workflow exists, the only snapshot it can
publish is HALT. It does not start a service or publish on import.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Any

from occ_snapshot_publisher import (
    SnapshotPublisherError,
    SnapshotSequenceStore,
    policy_file_sha256,
    write_envelope_atomic,
)


class FailClosedPublicationError(RuntimeError):
    """The current OCC governance state cannot be safely published."""


def publish_draft_baseline_halt(
    *,
    policy_path: str | Path,
    sequence_db_path: str | Path,
    inbox_path: str | Path,
    portfolio_version: int,
    secret: bytes,
    now_epoch: float | None = None,
    ttl_seconds: float = 60.0,
) -> dict[str, Any]:
    """Publish a short-lived HALT while the governance baseline is draft.

    A CLEAR snapshot cannot be emitted by this function, regardless of caller
    input. The receiver independently enforces expiry and portfolio version.
    """
    policy_file = Path(policy_path)
    try:
        policy = json.loads(policy_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FailClosedPublicationError(
            f"cannot read authoritative OCC policy ({type(exc).__name__})"
        ) from exc
    if not isinstance(policy, dict):
        raise FailClosedPublicationError("authoritative OCC policy must be a JSON object")

    policy_status = policy.get("status")
    policy_digest = policy_file_sha256(policy_file)
    timestamp = time.time() if now_epoch is None else now_epoch

    # This policy is deliberately a draft baseline, not an operational
    # clearance. Unexpected status changes are also treated as HALT.
    evidence_ref = (
        f"{policy_file.as_posix()}#status={policy_status!s};"
        "clearance=not-established"
    )
    envelope = SnapshotSequenceStore(sequence_db_path).issue(
        status="HALT",
        stop_conditions=["required_owner_approval_missing"],
        evidence_refs=[evidence_ref],
        policy_sha256=policy_digest,
        portfolio_version=portfolio_version,
        now_epoch=timestamp,
        ttl_seconds=ttl_seconds,
        secret=secret,
    )
    write_envelope_atomic(envelope, inbox_path)
    return envelope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish a conservative OCC HALT snapshot to the trusted local PolyBot inbox"
    )
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--sequence-db", type=Path, required=True)
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--portfolio-version", type=int, required=True)
    args = parser.parse_args(argv)

    secret_hex = os.environ.get("OCC_HMAC_SECRET_HEX", "")
    try:
        secret = bytes.fromhex(secret_hex)
    except ValueError:
        parser.error("OCC_HMAC_SECRET_HEX must contain hexadecimal secret material")
    if len(secret) < 32:
        parser.error("OCC_HMAC_SECRET_HEX must decode to at least 32 bytes")

    try:
        envelope = publish_draft_baseline_halt(
            policy_path=args.policy,
            sequence_db_path=args.sequence_db,
            inbox_path=args.inbox,
            portfolio_version=args.portfolio_version,
            secret=secret,
        )
    except (FailClosedPublicationError, SnapshotPublisherError, OSError, ValueError) as exc:
        parser.error(f"publication refused: {type(exc).__name__}: {exc}")
    print(
        "Published OCC HALT snapshot "
        f"{envelope['snapshot']['snapshot_id']} "
        f"for portfolio version {args.portfolio_version}; no CLEAR path exists."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
