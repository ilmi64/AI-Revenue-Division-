"""Offline document revision capture, fact comparison and profile-staleness checks.

The module consumes caller-supplied document text and extracted facts. It does
not fetch, scrape, authenticate, approve or automatically update venue profiles.
SHA-256 is a change fingerprint, not proof of publisher identity or authenticity.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
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
                "document_text", "content_sha256"):
        if not _nonempty(revision.get(key)):
            errors.append(f"{key} is required")
    # Revision records created from live research manifests use retrieval_method;
    # synthetic/manual captures use extraction_method. Accept either explicit
    # provenance field, but never accept a revision with neither.
    if not any(_nonempty(revision.get(key)) for key in ("extraction_method", "retrieval_method")):
        errors.append("extraction_method or retrieval_method is required")
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
        # Source locators are provenance metadata, not part of a fact's
        # semantic value. A page-layout change must not look like a changed
        # contract term when value and unit remain identical.
        old_unique = {_canonical({"value": item["value"], "unit": item.get("unit")}) for item in old_values}
        new_unique = {_canonical({"value": item["value"], "unit": item.get("unit")}) for item in new_values}
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
    """Flag profiles whose recorded source revision is no longer the latest captured revision.

    Profile source_revision_ids is an array of objects with document_id and
    revision_id; explicit pairing avoids relying on revision-ID naming.
    """
    errors: list[str] = []
    if not isinstance(profile, dict):
        errors.append("profile must be an object")
        profile = {}
    linked = profile.get("source_revision_ids")
    if not isinstance(linked, list) or not linked:
        errors.append("profile.source_revision_ids must be a non-empty array")
        linked = []
    linked_by_document: dict[str, str] = {}
    for index, item in enumerate(linked):
        if not isinstance(item, dict) or not _nonempty(item.get("document_id")) or not _nonempty(item.get("revision_id")):
            errors.append(f"profile.source_revision_ids[{index}] must contain document_id and revision_id")
            continue
        if item["document_id"] in linked_by_document:
            errors.append(f"duplicate profile source document_id {item['document_id']}")
        linked_by_document[item["document_id"]] = item["revision_id"]
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
    stale, missing_latest = [], []
    for document_id, revision_id in sorted(linked_by_document.items()):
        latest = valid_latest.get(document_id)
        if latest is None:
            missing_latest.append(document_id)
        elif latest["revision_id"] != revision_id:
            stale.append({
                "document_id": document_id,
                "profile_revision_id": revision_id,
                "latest_revision_id": latest["revision_id"],
                "content_sha256": latest["content_sha256"],
                "impact": "FACT_DIFF_REQUIRED_BEFORE_PROFILE_REUSE",
            })
    untracked_latest = sorted(set(valid_latest) - set(linked_by_document))
    stale_ids = sorted(set([item["document_id"] for item in stale] + missing_latest + untracked_latest))
    return {
        "status": "STALE_REVIEW_REQUIRED" if stale_ids else "CURRENT_SOURCE_REVISIONS",
        "errors": [], "stale_document_ids": stale_ids,
        "stale_sources": stale, "missing_latest_document_ids": missing_latest,
        "untracked_latest_document_ids": untracked_latest,
        "human_review_required": bool(stale_ids),
        "profile_update_performed": False, "profile_approval_performed": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        "note": "Any new source revision requires fact comparison and human review; profile values are never auto-updated.",
    }



def assess_document_freshness(revisions: Any, as_of_utc: Any, freshness_policy: Any) -> dict[str, Any]:
    """Assess capture age only where an explicit per-document TTL is supplied.

    This measures age since local capture, not age since publisher revision.
    It never invents a universal freshness threshold.
    """
    errors: list[str] = []
    as_of = _utc(as_of_utc)
    if as_of is None:
        errors.append("as_of_utc must be UTC ISO-8601 ending Z")
    if not isinstance(revisions, list):
        errors.append("revisions must be an array")
        revisions = []
    if not isinstance(freshness_policy, list):
        errors.append("freshness_policy must be an array")
        freshness_policy = []
    valid_revisions: dict[str, dict[str, Any]] = {}
    for index, revision in enumerate(revisions):
        revision_errors = validate_revision(revision)
        if revision_errors:
            errors.extend(f"revisions[{index}]: {error}" for error in revision_errors)
        elif revision["document_id"] in valid_revisions:
            errors.append(f"duplicate revision for document_id {revision['document_id']}")
        else:
            valid_revisions[revision["document_id"]] = revision
    policies: dict[str, int] = {}
    for index, item in enumerate(freshness_policy):
        if not isinstance(item, dict) or not _nonempty(item.get("document_id")):
            errors.append(f"freshness_policy[{index}] must include document_id")
            continue
        ttl = item.get("max_age_days")
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or not math.isfinite(ttl) or ttl < 0:
            errors.append(f"freshness_policy[{index}].max_age_days must be a non-negative number")
            continue
        if item["document_id"] in policies:
            errors.append(f"duplicate freshness policy for {item['document_id']}")
        else:
            policies[item["document_id"]] = ttl
    if errors:
        return {
            "status": "INVALID_FRESHNESS_INPUT", "errors": errors, "items": [],
            "human_review_required": True, "trade_authority": False,
            "live_readiness": False, "authority": AUTHORITY,
        }
    items = []
    for document_id, revision in sorted(valid_revisions.items()):
        captured = _utc(revision["captured_at_utc"])
        if captured > as_of:
            errors.append(f"revision {revision['revision_id']} is captured after as_of_utc")
            continue
        ttl = policies.get(document_id)
        if ttl is None:
            status, age_days = "NOT_ASSESSED_NO_TTL", (as_of - captured).total_seconds() / 86400
        else:
            age_days = (as_of - captured).total_seconds() / 86400
            status = "STALE" if age_days > ttl else "WITHIN_POLICY"
        items.append({
            "document_id": document_id, "revision_id": revision["revision_id"],
            "captured_at_utc": revision["captured_at_utc"],
            "age_days": round(age_days, 6), "max_age_days": ttl,
            "status": status,
            "review_required": status == "STALE",
        })
    if errors:
        return {
            "status": "INVALID_FRESHNESS_INPUT", "errors": errors, "items": [],
            "human_review_required": True, "trade_authority": False,
            "live_readiness": False, "authority": AUTHORITY,
        }
    stale = [item for item in items if item["status"] == "STALE"]
    unassessed = [item for item in items if item["status"] == "NOT_ASSESSED_NO_TTL"]
    status = "STALE_EVIDENCE_REVIEW_REQUIRED" if stale else (
        "NOT_ASSESSED_NO_TTL" if unassessed else "FRESHNESS_WITHIN_POLICY"
    )
    return {
        "status": status, "errors": [], "items": items,
        "stale_document_ids": [item["document_id"] for item in stale],
        "unassessed_document_ids": [item["document_id"] for item in unassessed],
        "human_review_required": bool(stale), "policy_supplied": bool(policies),
        "freshness_means_capture_age_only": True,
        "publisher_revision_time_verified": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        "limitations": [
            "Capture age does not establish when the publisher last changed the document.",
            "Freshness is assessed only against explicit per-document max_age_days values.",
            "No universal TTL or publisher timestamp trust is inferred.",
        ],
    }

def build_revision_review_queue(comparison_reports: Any, profile_impact_reports: Any = None, freshness_reports: Any = None) -> dict[str, Any]:
    """Build a deterministic, read-only queue for human review of document changes.

    Critical extracted contract-term changes are ranked before other document
    changes. This is workflow prioritization only; it does not approve evidence,
    update profiles, or grant eligibility.
    """
    errors: list[str] = []
    if not isinstance(comparison_reports, list):
        errors.append("comparison_reports must be an array")
        comparison_reports = []
    if profile_impact_reports is None:
        profile_impact_reports = []
    if not isinstance(profile_impact_reports, list):
        errors.append("profile_impact_reports must be an array when supplied")
        profile_impact_reports = []
    if freshness_reports is None:
        freshness_reports = []
    if not isinstance(freshness_reports, list):
        errors.append("freshness_reports must be an array when supplied")
        freshness_reports = []
    for index, report in enumerate(comparison_reports):
        if not isinstance(report, dict) or report.get("status") == "INVALID_REVISION_COMPARISON":
            errors.append(f"comparison_reports[{index}] is invalid")
    for index, report in enumerate(profile_impact_reports):
        if not isinstance(report, dict) or report.get("status") == "INVALID_PROFILE_REVISION_INPUT":
            errors.append(f"profile_impact_reports[{index}] is invalid")
    for index, report in enumerate(freshness_reports):
        if not isinstance(report, dict) or report.get("status") == "INVALID_FRESHNESS_INPUT":
            errors.append(f"freshness_reports[{index}] is invalid")
    if errors:
        return {
            "status": "INVALID_REVIEW_QUEUE_INPUT", "errors": errors,
            "items": [], "human_review_required": True,
            "profile_update_performed": False, "profile_approval_performed": False,
            "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        }

    items: list[dict[str, Any]] = []
    for report in comparison_reports:
        if report.get("human_review_required") is not True:
            continue
        critical_keys = sorted(set(report.get("critical_changed_fact_keys", [])))
        changed = report.get("changes", [])
        items.append({
            "review_type": "DOCUMENT_REVISION",
            "document_id": report.get("document_id"),
            "previous_revision_id": report.get("previous_revision_id"),
            "current_revision_id": report.get("current_revision_id"),
            "priority": "CRITICAL" if critical_keys else "STANDARD",
            "critical_fact_keys": critical_keys,
            "change_count": len(changed),
            "content_changed": report.get("content_changed") is True,
            "reason": "CRITICAL_CONTRACT_TERM_CHANGE" if critical_keys else "DOCUMENT_CONTENT_OR_FACT_CHANGE",
        })
    for report in profile_impact_reports:
        if report.get("human_review_required") is not True:
            continue
        for document_id in report.get("stale_document_ids", []):
            items.append({
                "review_type": "PROFILE_SOURCE_FRESHNESS",
                "document_id": document_id,
                "priority": "CRITICAL" if document_id in {
                    source.get("document_id") for source in report.get("stale_sources", [])
                    if source.get("impact") == "FACT_DIFF_REQUIRED_BEFORE_PROFILE_REUSE"
                } else "STANDARD",
                "reason": "PROFILE_SOURCE_REVISION_STALE_OR_UNTRACKED",
            })
    for report in freshness_reports:
        if report.get("status") != "STALE_EVIDENCE_REVIEW_REQUIRED":
            continue
        for document_id in report.get("stale_document_ids", []):
            items.append({
                "review_type": "DOCUMENT_CAPTURE_FRESHNESS",
                "document_id": document_id,
                "priority": "CRITICAL",
                "reason": "EXPLICIT_CAPTURE_AGE_TTL_EXCEEDED",
            })
    items.sort(key=lambda item: (
        0 if item["priority"] == "CRITICAL" else 1,
        item.get("document_id") or "",
        item["review_type"],
        item.get("current_revision_id") or "",
    ))
    return {
        "status": "REVIEW_REQUIRED" if items else "NO_REVIEW_ITEMS",
        "errors": [], "items": items,
        "item_count": len(items),
        "critical_item_count": sum(item["priority"] == "CRITICAL" for item in items),
        "human_review_required": bool(items),
        "profile_update_performed": False, "profile_approval_performed": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        "limitations": [
            "Priority is a deterministic review-queue ordering, not a risk score or approval.",
            "The queue depends on caller-supplied comparisons and profile-impact reports.",
            "No profile is changed, approved, or made eligible by queue generation.",
        ],
    }
