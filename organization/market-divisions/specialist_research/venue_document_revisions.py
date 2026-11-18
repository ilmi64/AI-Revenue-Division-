"""Offline document revision capture, fact comparison and profile-staleness checks.

The module consumes caller-supplied document text and extracted facts. It does
not fetch, scrape, authenticate, approve or automatically update venue profiles.
SHA-256 is a change fingerprint, not proof of publisher identity or authenticity.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
SCHEMA_VERSION = "1.0.0"
SOURCE_CLASSES = {
    "official_contract_specification", "official_margin_schedule",
    "official_financing_policy", "official_product_page",
    "official_help_centre", "regulator_notice", "exchange_rulebook",
    "broker_client_agreement", "third_party_reference", "research_note",
}
CRITICAL_FACTS = {
    "contract_multiplier", "quote_currency", "settlement_currency",
    "initial_margin_rate", "maintenance_tiers", "mark_price_rule",
    "expiry_utc", "contract_code", "settlement_method", "last_trade_time_utc",
    "financing_convention", "financing_rate_basis", "funding_convention",
    "funding_interval", "liquidation_fee_rate", "margin_closeout_policy",
    "triple_swap_policy", "roll_method", "price_tick", "tick_value",
    "contract_unit", "partial_liquidation_policy",
}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timezone.utc.utcoffset(parsed) else None


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_revision(revision: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(revision, dict):
        return ["revision must be an object"]
    for key in ("revision_id", "document_id", "canonical_uri", "title",
                "publisher", "source_class", "captured_at_utc",
                "extraction_method", "document_text", "content_sha256"):
        if not _nonempty(revision.get(key)):
            errors.append(f"{key} is required")
    if revision.get("source_class") not in SOURCE_CLASSES:
        errors.append("source_class is unsupported")
    uri = revision.get("canonical_uri")
    if isinstance(uri, str) and not uri.startswith("https://"):
        errors.append("canonical_uri must use HTTPS")
    if _utc(revision.get("captured_at_utc")) is None:
        errors.append("captured_at_utc must be UTC ISO-8601 ending Z")
    if revision.get("published_at_utc") is not None and _utc(revision.get("published_at_utc")) is None:
        errors.append("published_at_utc must be UTC ISO-8601 ending Z when supplied")
    text = revision.get("document_text")
    digest = revision.get("content_sha256")
    if isinstance(text, str) and isinstance(digest, str):
        actual = sha256(text.encode("utf-8")).hexdigest()
        if digest != actual:
            errors.append("content_sha256 does not match document_text")
    if isinstance(digest, str) and (
        len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest)
    ):
        errors.append("content_sha256 must be lowercase SHA-256 hex")
    facts = revision.get("extracted_facts")
    if not isinstance(facts, list):
        errors.append("extracted_facts must be an array")
    else:
        for index, fact in enumerate(facts):
            if not isinstance(fact, dict):
                errors.append(f"extracted_facts[{index}] must be an object")
                continue
            if not _nonempty(fact.get("fact_key")):
                errors.append(f"extracted_facts[{index}].fact_key is required")
            if "value" not in fact or fact.get("value") is None:
                errors.append(f"extracted_facts[{index}].value is required")
    return errors


def capture_document_revision(document: Any) -> dict[str, Any]:
    """Create a deterministic revision record from explicitly supplied text."""
    if not isinstance(document, dict):
        return {"status": "INVALID_REVISION", "errors": ["document must be an object"]}
    text = document.get("document_text")
    if not isinstance(text, str) or not text:
        return {"status": "INVALID_REVISION", "errors": ["document_text is required"]}
    digest = sha256(text.encode("utf-8")).hexdigest()
    captured = dict(document)
    captured.setdefault("revision_id", "")
    captured["content_sha256"] = digest
    identity = {
        "document_id": captured.get("document_id"),
        "canonical_uri": captured.get("canonical_uri"),
        "captured_at_utc": captured.get("captured_at_utc"),
        "content_sha256": digest,
        "extracted_facts": captured.get("extracted_facts"),
    }
    if not captured["revision_id"]:
        captured["revision_id"] = f"{captured.get('document_id', 'document')}:{_digest(identity)[:20]}"
    errors = validate_revision(captured)
    return {
        "status": "REVISION_CAPTURED_UNAUTHENTICATED" if not errors else "INVALID_REVISION",
        "errors": errors, "revision": captured if not errors else None,
        "authority": AUTHORITY, "research_only": True,
        "source_authentication": "NOT_PERFORMED",
        "profile_approval_performed": False, "trade_authority": False,
        "live_readiness": False,
    }


def _fact_values(revision: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for fact in revision["extracted_facts"]:
        result.setdefault(fact["fact_key"], []).append({
            "value": fact["value"], "unit": fact.get("unit"),
            "source_locator": fact.get("source_locator"),
        })
    return result


def compare_document_revisions(previous: Any, current: Any) -> dict[str, Any]:
    """Compare two consecutive revisions; conflicting extractions never get resolved by guess."""
    errors = [f"previous: {e}" for e in validate_revision(previous)]
    errors.extend(f"current: {e}" for e in validate_revision(current))
    if not errors:
        if previous["document_id"] != current["document_id"]:
            errors.append("revisions must refer to the same document_id")
        if previous["canonical_uri"] != current["canonical_uri"]:
            errors.append("revisions must use the same canonical_uri")
        old_time, new_time = _utc(previous["captured_at_utc"]), _utc(current["captured_at_utc"])
        if old_time and new_time and new_time <= old_time:
            errors.append("current captured_at_utc must be later than previous")
        if previous["revision_id"] == current["revision_id"]:
            errors.append("revision_id values must differ")
    if errors:
        return {
            "status": "INVALID_REVISION_COMPARISON", "errors": errors,
            "changes": [], "profile_update_performed": False,
            "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        }

    old, new = _fact_values(previous), _fact_values(current)
    changes = []
    for key in sorted(set(old) | set(new)):
        old_values, new_values = old.get(key, []), new.get(key, [])
        old_unique = {_canonical(item) for item in old_values}
        new_unique = {_canonical(item) for item in new_values}
        if len(old_unique) > 1 or len(new_unique) > 1:
            status = "CONFLICTED"
        elif not old_values:
            status = "ADDED"
        elif not new_values:
            status = "REMOVED"
        elif old_unique == new_unique:
            status = "UNCHANGED"
        else:
            status = "CHANGED"
        if status != "UNCHANGED":
            changes.append({
                "fact_key": key, "change_type": status,
                "critical": key in CRITICAL_FACTS,
                "previous_values": old_values, "current_values": new_values,
                "review_required": True,
            })
    critical = [item["fact_key"] for item in changes if item["critical"]]
    content_changed = previous["content_sha256"] != current["content_sha256"]
    status = "REVISION_CHANGED_REVIEW_REQUIRED" if content_changed or changes else "NO_CHANGE"
    return {
        "status": status, "errors": [],
        "document_id": current["document_id"],
        "previous_revision_id": previous["revision_id"],
        "current_revision_id": current["revision_id"],
        "content_changed": content_changed,
        "changes": changes, "critical_changed_fact_keys": critical,
        "human_review_required": bool(content_changed or changes),
        "profile_update_performed": False, "profile_approval_performed": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        "limitations": [
            "Extracted facts are caller-supplied and are not independently verified.",
            "A document hash detects byte changes only; it does not authenticate publisher or source.",
            "An unchanged extraction does not prove that the underlying terms are unchanged.",
            "No profile is automatically updated, approved or made eligible for simulation.",
        ],
    }


def assess_profile_revision_impact(profile: Any, latest_revisions: Any) -> dict[str, Any]:
    """Flag profiles whose recorded source revision is no longer the latest captured revision."""
    errors: list[str] = []
    if not isinstance(profile, dict):
        errors.append("profile must be an object")
        profile = {}
    linked = profile.get("source_revision_ids")
    if not isinstance(linked, list) or not linked or any(not _nonempty(x) for x in linked):
        errors.append("profile.source_revision_ids must be a non-empty string array")
        linked = []
    if not isinstance(latest_revisions, list):
        errors.append("latest_revisions must be an array")
        latest_revisions = []
    valid_latest = {}
    for index, revision in enumerate(latest_revisions):
        revision_errors = validate_revision(revision)
        if revision_errors:
            errors.extend(f"latest_revisions[{index}]: {e}" for e in revision_errors)
        elif revision["document_id"] in valid_latest:
            errors.append(f"duplicate latest revision for document_id {revision['document_id']}")
        else:
            valid_latest[revision["document_id"]] = revision
    if errors:
        return {
            "status": "INVALID_PROFILE_REVISION_INPUT", "errors": errors,
            "stale_document_ids": [], "human_review_required": True,
            "profile_update_performed": False, "trade_authority": False,
            "live_readiness": False, "authority": AUTHORITY,
        }
    linked_set = set(linked)
    stale, untracked = [], []
    for document_id, revision in sorted(valid_latest.items()):
        if revision["revision_id"] not in linked_set:
            stale.append({
                "document_id": document_id,
                "profile_revision_ids_for_document": [
                    item for item in linked if item.startswith(document_id + ":")
                ],
                "latest_revision_id": revision["revision_id"],
                "content_sha256": revision["content_sha256"],
                "impact": "FACT_DIFF_REQUIRED_BEFORE_PROFILE_REUSE",
            })
    known_docs = set(valid_latest)
    for revision_id in linked:
        if not any(revision_id.startswith(doc_id + ":") for doc_id in known_docs):
            untracked.append(revision_id)
    return {
        "status": "STALE_REVIEW_REQUIRED" if stale or untracked else "CURRENT_SOURCE_REVISIONS",
        "errors": [], "stale_document_ids": [item["document_id"] for item in stale],
        "stale_sources": stale, "untracked_profile_revision_ids": untracked,
        "human_review_required": bool(stale or untracked),
        "profile_update_performed": False, "profile_approval_performed": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        "note": "Any new source revision requires fact comparison and human review; profile values are never auto-updated.",
    }
