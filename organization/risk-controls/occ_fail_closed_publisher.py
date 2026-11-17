"""Conservative OCC publisher for the current draft governance baseline.

This module intentionally has NO automatic CLEAR path. Until a separately
approved operational control-state workflow exists, the only snapshot it can
publish is HALT. It does not start a service or publish on import.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import stat
from pathlib import Path
import time
from typing import Any

from occ_snapshot_publisher import (
    SnapshotPublisherError,
    SnapshotSequenceStore,
    write_envelope_atomic,
)


class FailClosedPublicationError(RuntimeError):
    """The current OCC governance state cannot be safely published."""


@contextmanager
def _inbox_publication_lock(inbox_path: str | Path):
    """Lock the stable adjacent lock file shared with the PolyBot receiver."""
    try:
        import fcntl
    except ImportError as exc:
        raise FailClosedPublicationError("platform lacks POSIX advisory file locking") from exc
    path = Path(str(Path(inbox_path)) + ".lock")
    if not path.is_absolute() or not hasattr(os, "O_NOFOLLOW"):
        raise FailClosedPublicationError("inbox lock requires an absolute path and no-follow support")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise FailClosedPublicationError("inbox lock is not a regular file")
        if stat.S_IMODE(metadata.st_mode) & 0o077:
            raise FailClosedPublicationError("inbox lock permissions allow group/other access")
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)

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
        policy_bytes = policy_file.read_bytes()
        policy = json.loads(policy_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FailClosedPublicationError(
            f"cannot read authoritative OCC policy ({type(exc).__name__})"
        ) from exc
    if not isinstance(policy, dict):
        raise FailClosedPublicationError("authoritative OCC policy must be a JSON object")

    policy_status = policy.get("status")
    if not isinstance(policy_status, str) or len(policy_status) > 100:
        policy_status = "invalid_or_unrecognised"
    # Bind the snapshot to the exact same bytes that were parsed above.
    policy_digest = hashlib.sha256(policy_bytes).hexdigest()
    timestamp = time.time() if now_epoch is None else now_epoch

    # This policy is deliberately a draft baseline, not an operational
    # clearance. Unexpected status changes are also treated as HALT.
    evidence_ref = (
        f"{policy_file.as_posix()}#status={policy_status!s};"
        "clearance=not-established"
    )
    with _inbox_publication_lock(inbox_path):
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
