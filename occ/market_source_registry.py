"""Validation of an externally supplied market-source review registry.

Entries and approval states are claims from the caller's registry. This module
does not authenticate reviewers, evidence, endpoints, transports or sources.
"""
from __future__ import annotations
import math
from collections.abc import Mapping, Sequence
from typing import Any
from .instrument_identity import InstrumentIdentityError, validate_instrument_identity

STATES = {"UNREVIEWED", "REVIEW_REQUIRED", "APPROVED_FOR_PAPER", "REVOKED"}

class MarketSourceRegistryError(ValueError):
    """The source registry is malformed or internally inconsistent."""

def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketSourceRegistryError(f"{field} must be a non-empty string")
    return value.strip()

def _epoch(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketSourceRegistryError(f"{field} must be a finite non-negative timestamp")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MarketSourceRegistryError(f"{field} must be a finite non-negative timestamp") from exc
    if not math.isfinite(result) or result < 0:
        raise MarketSourceRegistryError(f"{field} must be a finite non-negative timestamp")
    return result

def _identity_key(identity: Mapping[str, Any]) -> tuple[Any, ...]:
    fields = ("market_class","product_type","venue","symbol","base_currency",
      "quote_currency","contract_unit","contract_multiplier","settlement_method",
      "expiry","custody_model","financing_model")
    return tuple(identity.get(field) for field in fields)

def validate_source_registry(entries: Sequence[Mapping[str, Any]], *,
        now_epoch: int | float) -> dict[str, Any]:
    """Validate registry shape and return status summaries; never authenticate it."""
    if isinstance(entries, (str, bytes, bytearray)) or not isinstance(entries, Sequence):
        raise MarketSourceRegistryError("entries must be a sequence of registry records")
    now = _epoch(now_epoch, "now_epoch")
    seen = set()
    normalized = []
    counts = {state: 0 for state in sorted(STATES)}
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise MarketSourceRegistryError(f"entry {index} must be a mapping")
        source_id = _text(entry.get("source_id"), "source_id")
        adapter_id = _text(entry.get("adapter_id"), "adapter_id")
        venue = _text(entry.get("venue"), "venue")
        endpoint = _text(entry.get("endpoint"), "endpoint")
        transport = _text(entry.get("transport"), "transport").upper()
        parser_version = _text(entry.get("parser_version"), "parser_version")
        independence_group = _text(entry.get("independence_group"), "independence_group")
        if transport not in {"HTTPS", "WSS", "LOCAL_FILE", "MANUAL"}:
            raise MarketSourceRegistryError("unsupported transport")
        try:
            identity = validate_instrument_identity(entry.get("instrument_identity"))
        except InstrumentIdentityError as exc:
            raise MarketSourceRegistryError(f"invalid instrument identity: {exc}") from exc
        if identity["venue"] != venue:
            raise MarketSourceRegistryError("registry venue does not match instrument identity")
        state = _text(entry.get("review_state"), "review_state").upper()
        if state not in STATES:
            raise MarketSourceRegistryError("unsupported review_state")
        key = (source_id, adapter_id, _identity_key(identity))
        if key in seen:
            raise MarketSourceRegistryError("duplicate source/adapter/instrument registry identity")
        seen.add(key)

        reviewer = entry.get("reviewer_id")
        evidence = entry.get("review_evidence_ref")
        reviewed_at = entry.get("reviewed_at_epoch")
        revocation_reason = entry.get("revocation_reason")
        if state == "APPROVED_FOR_PAPER":
            reviewer = _text(reviewer, "reviewer_id")
            evidence = _text(evidence, "review_evidence_ref")
            reviewed_at = _epoch(reviewed_at, "reviewed_at_epoch")
            if reviewed_at > now:
                raise MarketSourceRegistryError("review timestamp cannot be in the future")
        elif state == "REVOKED":
            revocation_reason = _text(revocation_reason, "revocation_reason")
        normalized_entry = dict(entry)
        normalized_entry.update({"source_id":source_id,"adapter_id":adapter_id,
          "venue":venue,"endpoint":endpoint,"transport":transport,
          "parser_version":parser_version,"independence_group":independence_group,
          "instrument_identity":identity,"review_state":state})
        normalized_entry.update({
          "reviewer_id": reviewer.strip() if isinstance(reviewer,str) else None,
          "review_evidence_ref": evidence.strip() if isinstance(evidence,str) else None,
          "reviewed_at_epoch": reviewed_at,
          "revocation_reason": revocation_reason.strip() if isinstance(revocation_reason,str) else None,
          "approval_claim_structurally_valid": state == "APPROVED_FOR_PAPER",
          "approval_authority_authenticated": False,
          "source_authenticated": False,
          "execution_eligible": False,
        })
        normalized.append(normalized_entry)
        counts[state] += 1
    normalized.sort(key=lambda item: (item["source_id"],item["adapter_id"],
      item["instrument_identity"]["symbol"]))
    return {"entries":normalized,"counts":counts,"entry_count":len(normalized),
      "registry_shape_valid":True,"registry_authority_authenticated":False,
      "any_source_trusted":False,"paper_use_authorized":False,
      "execution_eligible":False}

def compare_source_independence(entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Report distinct declared independence groups; does not prove independence."""
    if isinstance(entries,(str,bytes,bytearray)) or not isinstance(entries,Sequence):
        raise MarketSourceRegistryError("entries must be a sequence")
    approved = [e for e in entries if isinstance(e,Mapping)
      and e.get("review_state") == "APPROVED_FOR_PAPER"]
    groups = sorted({e.get("independence_group") for e in approved
      if isinstance(e.get("independence_group"),str) and e.get("independence_group").strip()})
    return {"approved_entry_count":len(approved),"declared_independence_groups":groups,
      "declared_group_count":len(groups),"independence_verified":False,
      "multi_source_consensus_authorized":False}
