"""Offline, read-only OCC commissioning export. No network or operational actions."""
from __future__ import annotations

import json
import re
from revenue_commissioning_snapshot import CommissioningSnapshot

HEX = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "aevora.occ.commissioning.v1"


def export_occ_snapshot(snapshot: CommissioningSnapshot) -> bytes:
    """Canonical JSON for audit handover; digest is NOT an authenticated signature."""
    if not isinstance(snapshot, CommissioningSnapshot):
        raise TypeError("commissioning snapshot required")
    if (snapshot.company != "Aevora AI Revenue"
            or type(snapshot.evidence_records) is not int or snapshot.evidence_records < 0
            or not isinstance(snapshot.evidence_head_sha256, str)
            or not HEX.fullmatch(snapshot.evidence_head_sha256)
            or type(snapshot.local_chain_valid) is not bool
            or snapshot.gate_status != "BLOCKED"
            or any((snapshot.launch_authorized, snapshot.agent_execution_authorized,
                    snapshot.external_actions_authorized))
            or not isinstance(snapshot.blockers, tuple)
            or not all(isinstance(x, str) and x for x in snapshot.blockers)):
        raise ValueError("invalid or unsafe commissioning snapshot")
    document = {
        "schema": SCHEMA,
        "company": snapshot.company,
        "evidence": {
            "records": snapshot.evidence_records,
            "head_sha256": snapshot.evidence_head_sha256,
            "local_chain_valid": snapshot.local_chain_valid,
        },
        "identity_status": snapshot.identity_status,
        "gate_status": snapshot.gate_status,
        "blockers": sorted(set(snapshot.blockers)),
        "permissions": {
            "launch": False,
            "agent_execution": False,
            "external_actions": False,
        },
        "trust": {
            "authenticated_signature": False,
            "independent_custody": False,
            "read_only_projection": True,
        },
    }
    return (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
