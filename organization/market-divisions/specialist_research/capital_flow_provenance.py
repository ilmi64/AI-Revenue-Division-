"""Evidence provenance annotations for Capital Flow research records.

This module validates supplied metadata and distinguishes declared source
relationships from independently verified provenance. It does not authenticate
URLs, publishers, timestamps, or ownership.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def assess_event_provenance(event: dict[str, Any], now_utc: str) -> dict[str, Any]:
    """Assess evidence metadata completeness; never claim authenticity."""
    now = _utc(now_utc)
    refs = event.get("evidence_refs")
    refs = refs if isinstance(refs, list) and all(isinstance(x, str) for x in refs) else []
    source_ids = event.get("source_ids")
    source_ids = source_ids if isinstance(source_ids, list) and all(isinstance(x, str) for x in source_ids) else []
    items = event.get("evidence_items")
    items = items if isinstance(items, list) else []
    errors: list[str] = []
    seen_refs: set[str] = set()
    normalized = []
    independence_groups: set[str] = set()
    source_families: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"evidence_items[{index}] must be an object")
            continue
        ref = item.get("evidence_ref")
        source_id = item.get("source_id")
        publisher = item.get("publisher")
        canonical_source_id = item.get("canonical_source_id")
        family = item.get("source_family")
        group = item.get("independence_group")
        timestamp = _utc(item.get("published_at_utc"))
        if not isinstance(ref, str) or ref not in refs or ref in seen_refs:
            errors.append(f"evidence_items[{index}] has missing, unknown or duplicate evidence_ref")
            continue
        seen_refs.add(ref)
        if source_id not in source_ids:
            errors.append(f"{ref}: source_id is not declared on event")
        if not isinstance(publisher, str) or not publisher.strip():
            errors.append(f"{ref}: publisher identity missing")
        if not isinstance(canonical_source_id, str) or not canonical_source_id.strip():
            errors.append(f"{ref}: canonical_source_id missing")
        if not isinstance(family, str) or not family.strip():
            errors.append(f"{ref}: source_family missing")
        if timestamp is None:
            errors.append(f"{ref}: published_at_utc must be an ISO-8601 UTC timestamp")
        elif now is not None and timestamp > now:
            errors.append(f"{ref}: evidence publication timestamp is in the future")
        if isinstance(group, str) and group.strip():
            independence_groups.add(group)
        if isinstance(family, str) and family.strip():
            source_families.add(family)
        normalized.append({
            "evidence_ref": ref,
            "source_id": source_id,
            "publisher": publisher,
            "canonical_source_id": canonical_source_id,
            "source_family": family,
            "published_at_utc": item.get("published_at_utc"),
            "declared_independence_group": group,
        })
    missing_refs = sorted(set(refs) - seen_refs)
    if missing_refs:
        errors.append("evidence metadata missing for: " + ",".join(missing_refs))
    declared_independent = len(independence_groups)
    return {
        "status": "metadata_complete_unverified" if not errors and normalized else "incomplete",
        "evidence_item_count": len(normalized),
        "evidence_refs_without_metadata": missing_refs,
        "metadata_errors": errors,
        "distinct_declared_publishers": len({x["publisher"] for x in normalized if isinstance(x["publisher"], str)}),
        "distinct_canonical_sources": len({x["canonical_source_id"] for x in normalized if isinstance(x["canonical_source_id"], str)}),
        "distinct_source_families": len(source_families),
        "declared_independence_groups": declared_independent,
        "independent_corroboration_established": False,
        "independence_assessment": (
            "multiple_declared_groups_require_external_ownership_verification"
            if declared_independent > 1 else
            "no_independent_group_claim_established"
        ),
        "evidence": normalized,
        "authentication_status": "not_authenticated",
        "timestamp_trust_status": "publisher_claim_not_independently_verified",
    }
