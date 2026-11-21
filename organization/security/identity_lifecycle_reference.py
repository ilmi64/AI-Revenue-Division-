"""Synthetic identity and approval lifecycle reference.

HMAC is used only to demonstrate issuer-authenticated claims with injected
fixture keys. Never use fixture keys, this module, or shared HMAC secrets as a
production identity system. Keys are not stored in this repository.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sign(payload: dict[str, Any], key: bytes) -> str:
    return hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()


def _valid_key(key: Any) -> bool:
    return isinstance(key, bytes) and len(key) >= 32


def issue_identity(*, issuer_id: str, agent_id: str, company_id: str, role: str,
                   issued_at: int, expires_at: int, issuer_key: bytes) -> dict[str, Any]:
    """Trusted-issuer demonstration. Caller must represent the issuer, never an agent."""
    if not _valid_key(issuer_key):
        raise ValueError("issuer_key_must_be_at_least_32_bytes")
    if not all(isinstance(x, str) and x.strip() for x in (issuer_id, agent_id, company_id, role)):
        raise ValueError("identity_claims_must_be_nonempty_strings")
    if (isinstance(issued_at, bool) or not isinstance(issued_at, int) or
            isinstance(expires_at, bool) or not isinstance(expires_at, int) or
            issued_at < 0 or expires_at <= issued_at):
        raise ValueError("invalid_identity_lifetime")
    claims = {"kind": "agent_identity", "issuer_id": issuer_id, "agent_id": agent_id,
              "company_id": company_id, "role": role, "issued_at": issued_at,
              "expires_at": expires_at}
    return {"claims": claims, "signature": _sign(claims, issuer_key)}


def verify_identity(envelope: Any, *, issuer_id: str, company_id: str, now: int,
                    issuer_key: bytes, revoked_agents: set[str] | None = None) -> tuple[bool, str]:
    if not _valid_key(issuer_key) or not isinstance(envelope, dict):
        return False, "malformed_identity_envelope"
    claims, signature = envelope.get("claims"), envelope.get("signature")
    if not isinstance(claims, dict) or not isinstance(signature, str):
        return False, "malformed_identity_envelope"
    if not isinstance(now, int) or isinstance(now, bool) or now < 0:
        return False, "invalid_verification_time"
    expected = _sign(claims, issuer_key)
    if not hmac.compare_digest(signature, expected):
        return False, "invalid_identity_signature"
    if claims.get("kind") != "agent_identity" or claims.get("issuer_id") != issuer_id:
        return False, "untrusted_identity_issuer"
    if claims.get("company_id") != company_id:
        return False, "identity_company_mismatch"
    for field in ("agent_id", "company_id", "role"):
        if not isinstance(claims.get(field), str) or not claims[field].strip():
            return False, "invalid_identity_claims"
    issued, expiry = claims.get("issued_at"), claims.get("expires_at")
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (issued, expiry)):
        return False, "invalid_identity_lifetime"
    if issued < 0 or expiry <= issued or issued > now:
        return False, "invalid_identity_lifetime"
    if expiry <= now:
        return False, "identity_expired"
    revoked_agents = revoked_agents if revoked_agents is not None else set()
    if not isinstance(revoked_agents, set) or any(not isinstance(x, str) for x in revoked_agents):
        return False, "invalid_revocation_state"
    if claims["agent_id"] in revoked_agents:
        return False, "identity_revoked"
    return True, "identity_verified"


def issue_owner_approval(*, owner_id: str, company_id: str, task_id: str,
                         operation: str, resource: str, nonce: str,
                         issued_at: int, expires_at: int, owner_key: bytes) -> dict[str, Any]:
    """Create an exact, single-use synthetic approval under a distinct owner key."""
    if not _valid_key(owner_key):
        raise ValueError("owner_key_must_be_at_least_32_bytes")
    fields = (owner_id, company_id, task_id, operation, resource, nonce)
    if not all(isinstance(x, str) and x.strip() for x in fields):
        raise ValueError("approval_claims_must_be_nonempty_strings")
    if (isinstance(issued_at, bool) or not isinstance(issued_at, int) or
            isinstance(expires_at, bool) or not isinstance(expires_at, int) or
            issued_at < 0 or expires_at <= issued_at):
        raise ValueError("invalid_approval_lifetime")
    claims = {"kind": "owner_approval", "issuer_id": owner_id, "company_id": company_id,
              "task_id": task_id, "operation": operation, "resource": resource,
              "nonce": nonce, "issued_at": issued_at, "expires_at": expires_at,
              "single_use": True}
    return {"claims": claims, "signature": _sign(claims, owner_key)}


def verify_owner_approval(envelope: Any, *, owner_id: str, company_id: str,
                          task_id: str, operation: str, resource: str, nonce: str,
                          now: int, owner_key: bytes,
                          consumed_nonces: set[str] | None = None) -> tuple[bool, str]:
    if not _valid_key(owner_key) or not isinstance(envelope, dict):
        return False, "malformed_approval_envelope"
    claims, signature = envelope.get("claims"), envelope.get("signature")
    if not isinstance(claims, dict) or not isinstance(signature, str):
        return False, "malformed_approval_envelope"
    if not isinstance(now, int) or isinstance(now, bool) or now < 0:
        return False, "invalid_verification_time"
    if not hmac.compare_digest(signature, _sign(claims, owner_key)):
        return False, "invalid_approval_signature"
    expected = {"kind": "owner_approval", "issuer_id": owner_id, "company_id": company_id,
                "task_id": task_id, "operation": operation, "resource": resource,
                "nonce": nonce, "single_use": True}
    if any(claims.get(k) != v for k, v in expected.items()):
        return False, "approval_scope_mismatch"
    issued, expiry = claims.get("issued_at"), claims.get("expires_at")
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (issued, expiry)):
        return False, "invalid_approval_lifetime"
    if issued < 0 or expiry <= issued or issued > now:
        return False, "invalid_approval_lifetime"
    if expiry <= now:
        return False, "approval_expired"
    consumed_nonces = consumed_nonces if consumed_nonces is not None else set()
    if not isinstance(consumed_nonces, set) or any(not isinstance(x, str) for x in consumed_nonces):
        return False, "invalid_consumption_state"
    if nonce in consumed_nonces:
        return False, "approval_already_consumed"
    return True, "approval_verified_not_yet_consumed"
