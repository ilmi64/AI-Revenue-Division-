"""Offline OCC-side contract validator for Aevora commissioning exports.

Validation is structural only: JSON has no trusted signature or transport identity.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import re

HEX = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "aevora.occ.commissioning.v1"
TOP = {"schema", "company", "evidence", "identity_status", "gate_status", "blockers", "permissions", "trust"}


@dataclass(frozen=True)
class ImportDecision:
    status: str
    blockers: tuple[str, ...]
    launch_authorized: bool = False
    agent_execution_authorized: bool = False
    external_actions_authorized: bool = False


def validate_occ_export(payload: bytes) -> ImportDecision:
    if not isinstance(payload, bytes) or not 0 < len(payload) <= 32768:
        return ImportDecision("REJECT", ("payload_invalid",))
    try:
        document = json.loads(payload.decode("ascii"))
    except (UnicodeError, ValueError):
        return ImportDecision("REJECT", ("json_invalid",))
    if not isinstance(document, dict) or set(document) != TOP:
        return ImportDecision("REJECT", ("schema_fields_invalid",))
    if document["schema"] != SCHEMA or document["company"] != "Aevora AI Revenue":
        return ImportDecision("REJECT", ("source_scope_invalid",))
    evidence = document["evidence"]
    permissions = document["permissions"]
    trust = document["trust"]
    if (not isinstance(evidence, dict)
            or set(evidence) != {"records", "head_sha256", "local_chain_valid"}
            or type(evidence["records"]) is not int or evidence["records"] < 0
            or not isinstance(evidence["head_sha256"], str)
            or not HEX.fullmatch(evidence["head_sha256"])
            or type(evidence["local_chain_valid"]) is not bool):
        return ImportDecision("REJECT", ("evidence_invalid",))
    if (not isinstance(permissions, dict)
            or set(permissions) != {"launch", "agent_execution", "external_actions"}
            or any(value is not False for value in permissions.values())):
        return ImportDecision("REJECT", ("permissions_invalid",))
    if (not isinstance(trust, dict)
            or set(trust) != {"authenticated_signature", "independent_custody", "read_only_projection"}
            or trust != {"authenticated_signature": False, "independent_custody": False,
                         "read_only_projection": True}):
        return ImportDecision("REJECT", ("trust_claim_invalid",))
    if (document["gate_status"] != "BLOCKED"
            or not isinstance(document["identity_status"], str)
            or not isinstance(document["blockers"], list)
            or not all(isinstance(x, str) and x for x in document["blockers"])):
        return ImportDecision("REJECT", ("gate_invalid",))
    return ImportDecision("READ_ONLY_ACCEPTED", tuple(document["blockers"]))
