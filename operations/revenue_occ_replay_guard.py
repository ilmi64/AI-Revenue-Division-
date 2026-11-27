"""Offline OCC replay protection. Caller must authenticate the source and pin externally."""
from __future__ import annotations

from dataclasses import dataclass
import json
from revenue_occ_pinned_import import verify_pinned_import


@dataclass(frozen=True)
class ReplayState:
    sequence: int
    payload_sha256: str


@dataclass(frozen=True)
class ReplayDecision:
    status: str
    blockers: tuple[str, ...]
    next_state: ReplayState | None
    launch_authorized: bool = False
    execution_authorized: bool = False
    external_actions_authorized: bool = False


def assess_replay(payload: bytes, pinned_digest: str,
                  prior: ReplayState | None) -> ReplayDecision:
    """Pure projection; persistence and authenticated checkpoint custody are external."""
    receipt = verify_pinned_import(payload, pinned_digest)
    if receipt.status != "READ_ONLY_PIN_MATCH":
        return ReplayDecision("REJECT", receipt.blockers, None)
    if prior is not None and (not isinstance(prior, ReplayState)
                              or type(prior.sequence) is not int or prior.sequence < 0
                              or not isinstance(prior.payload_sha256, str)
                              or len(prior.payload_sha256) != 64):
        return ReplayDecision("REJECT", ("prior_checkpoint_invalid",), None)
    document = json.loads(payload)
    sequence = document["evidence"]["records"]
    if prior is not None:
        if sequence < prior.sequence:
            return ReplayDecision("REJECT", ("stale_sequence",), None)
        if sequence == prior.sequence:
            if receipt.payload_sha256 == prior.payload_sha256:
                return ReplayDecision("REJECT", ("replayed_report",), None)
            return ReplayDecision("REJECT", ("same_sequence_conflict",), None)
    return ReplayDecision("READ_ONLY_NEW_REPORT", receipt.blockers,
                          ReplayState(sequence, receipt.payload_sha256))
