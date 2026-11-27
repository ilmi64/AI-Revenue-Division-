"""Offline pinned OCC handover: integrity check only, not identity authentication."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import re
from revenue_occ_import import ImportDecision, validate_occ_export

HEX = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class PinnedImport:
    status: str
    blockers: tuple[str, ...]
    payload_sha256: str
    launch_authorized: bool = False
    agent_execution_authorized: bool = False
    external_actions_authorized: bool = False


def verify_pinned_import(payload: bytes, independently_obtained_sha256: str) -> PinnedImport:
    """Digest must be obtained via a separate authenticated channel.

    This function cannot establish that channel or prevent a malicious
    sender from supplying both the payload and a matching digest.
    """
    if not isinstance(payload, bytes) or not 0 < len(payload) <= 32768:
        return PinnedImport("REJECT", ("payload_invalid",), "")
    digest = hashlib.sha256(payload).hexdigest()
    if (not isinstance(independently_obtained_sha256, str)
            or not HEX.fullmatch(independently_obtained_sha256)):
        return PinnedImport("REJECT", ("pin_invalid",), digest)
    if not hmac.compare_digest(digest, independently_obtained_sha256):
        return PinnedImport("REJECT", ("pin_mismatch",), digest)
    decision = validate_occ_export(payload)
    if decision.status != "READ_ONLY_ACCEPTED":
        return PinnedImport("REJECT", decision.blockers, digest)
    return PinnedImport("READ_ONLY_PIN_MATCH", decision.blockers, digest)
