"""Read-only commissioning snapshot for OCC; never authorizes company operations."""
from __future__ import annotations

from dataclasses import dataclass
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_release_gate import assess_release


@dataclass(frozen=True)
class CommissioningSnapshot:
    company: str
    evidence_records: int
    evidence_head_sha256: str
    local_chain_valid: bool
    identity_status: str
    gate_status: str
    blockers: tuple[str, ...]
    launch_authorized: bool = False
    agent_execution_authorized: bool = False
    external_actions_authorized: bool = False


def snapshot(identity: IdentityAssessment, custody: LocalEvidenceCustody,
             *, anchor_sequence: int | None = None,
             anchor_digest: str | None = None) -> CommissioningSnapshot:
    """Untrusted checkpoint arguments are diagnostic, not proof of custody."""
    gate = assess_release(identity, custody, anchor_sequence=anchor_sequence,
                          anchor_digest=anchor_digest)
    valid = custody.verify_chain()
    sequence, digest = custody.head()
    blockers = list(gate.blockers)
    if not valid:
        blockers.append("local_evidence_chain_invalid")
    return CommissioningSnapshot(
        company="Aevora AI Revenue",
        evidence_records=sequence,
        evidence_head_sha256=digest,
        local_chain_valid=valid,
        identity_status=identity.status,
        gate_status=gate.status,
        blockers=tuple(dict.fromkeys(blockers)),
    )
