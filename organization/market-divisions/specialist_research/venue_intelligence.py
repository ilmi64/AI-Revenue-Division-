"""Offline venue intelligence intake, evidence assessment and profile preparation.

No web fetching, scraping, venue connectivity, credential use or auto-approval.
All evidence is explicitly supplied by a researcher and remains unauthenticated.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
SCHEMA_VERSION = "1.0.0"
REQUIRED_FACTS = {
    "crypto_perpetual": {
        "contract_multiplier", "quote_currency", "settlement_currency",
        "initial_margin_rate", "maintenance_tiers", "mark_price_rule",
        "liquidation_fee_rate", "funding_convention", "funding_interval",
        "partial_liquidation_policy", "liquidation_fee_basis",
    },
    "forex_cfd": {
        "contract_multiplier", "quote_currency", "settlement_currency",
        "initial_margin_rate", "maintenance_tiers", "mark_price_rule",
        "financing_convention", "financing_rate_basis", "triple_swap_policy",
        "margin_closeout_policy", "minimum_lot", "lot_step",
    },
    "index_future": {
        "contract_multiplier", "quote_currency", "settlement_currency",
        "initial_margin_rate", "maintenance_tiers", "expiry_utc",
        "contract_code", "settlement_method", "last_trade_time_utc",
        "price_tick", "tick_value", "roll_method",
    },
    "index_cfd": {
        "contract_multiplier", "quote_currency", "settlement_currency",
        "initial_margin_rate", "maintenance_tiers", "mark_price_rule",
        "financing_convention", "financing_rate_basis", "trading_hours",
        "margin_closeout_policy", "corporate_action_policy",
    },
    "gold_future": {
        "contract_multiplier", "quote_currency", "settlement_currency",
        "initial_margin_rate", "maintenance_tiers", "expiry_utc",
        "contract_code", "settlement_method", "last_trade_time_utc",
        "price_tick", "tick_value", "roll_method",
    },
    "gold_cfd": {
        "contract_multiplier", "quote_currency", "settlement_currency",
        "initial_margin_rate", "maintenance_tiers", "mark_price_rule",
        "financing_convention", "financing_rate_basis", "trading_hours",
        "margin_closeout_policy", "contract_unit",
    },
}
SOURCE_CLASSES = {
    "official_contract_specification", "official_margin_schedule",
    "official_financing_policy", "official_product_page",
    "official_help_centre", "regulator_notice", "exchange_rulebook",
    "broker_client_agreement", "third_party_reference", "research_note",
}
CRITICAL_FACTS = {
    "contract_multiplier", "quote_currency", "settlement_currency",
    "initial_margin_rate", "maintenance_tiers", "mark_price_rule",
    "expiry_utc", "settlement_method", "financing_convention",
    "funding_convention", "margin_closeout_policy",
}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timezone.utc.utcoffset(parsed) else None


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_source_record(source: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(source, dict):
        return ["source record must be an object"]
    for field in ("source_id", "source_uri", "source_class", "publisher",
                  "published_at_utc", "captured_at_utc", "content_sha256"):
        if not _nonempty(source.get(field)):
            errors.append(f"{field} is required")
    if source.get("source_class") not in SOURCE_CLASSES:
        errors.append("source_class is unsupported")
    for field in ("published_at_utc", "captured_at_utc"):
        if source.get(field) is not None and _utc(source.get(field)) is None:
            errors.append(f"{field} must be UTC ISO-8601 ending Z")
    digest = source.get("content_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        errors.append("content_sha256 must be a lowercase SHA-256 hex digest")
    return errors


def assess_evidence_bundle(bundle: Any, as_of_utc: str) -> dict[str, Any]:
    """Assess coverage, conflicts and freshness without deciding truth."""
    errors: list[str] = []
    if not isinstance(bundle, dict):
        bundle = {}
        errors.append("evidence bundle must be an object")
    instrument_type = bundle.get("instrument_type")
    required = REQUIRED_FACTS.get(instrument_type)
    if required is None:
        errors.append("instrument_type is unsupported")
        required = set()
    as_of = _utc(as_of_utc)
    if as_of is None:
        errors.append("as_of_utc must be UTC ISO-8601 ending Z")
    sources = bundle.get("sources", [])
    facts = bundle.get("facts", [])
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        sources = []
    if not isinstance(facts, list):
        errors.append("facts must be an array")
        facts = []
    source_by_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        source_errors = validate_source_record(source)
        errors.extend(f"sources[{index}]: {e}" for e in source_errors)
        if isinstance(source, dict) and _nonempty(source.get("source_id")):
            if source["source_id"] in source_by_id:
                errors.append(f"duplicate source_id: {source['source_id']}")
            source_by_id[source["source_id"]] = source

    values_by_fact: dict[str, list[dict[str, Any]]] = {}
    for index, fact in enumerate(facts):
        prefix = f"facts[{index}]"
        if not isinstance(fact, dict):
            errors.append(f"{prefix} must be an object")
            continue
        key = fact.get("fact_key")
        if not _nonempty(key):
            errors.append(f"{prefix}.fact_key is required")
            continue
        if "value" not in fact or fact.get("value") is None:
            errors.append(f"{prefix}.value is required")
            continue
        source_id = fact.get("source_id")
        if source_id not in source_by_id:
            errors.append(f"{prefix} references an unknown source_id")
            continue
        source = source_by_id[source_id]
        observed = fact.get("observed_at_utc")
        if _utc(observed) is None:
            errors.append(f"{prefix}.observed_at_utc must be UTC ISO-8601 ending Z")
        elif as_of is not None and _utc(observed) > as_of:
            errors.append(f"{prefix}.observed_at_utc is after assessment time")
        values_by_fact.setdefault(key, []).append({
            "value": fact["value"], "source_id": source_id,
            "source_class": source.get("source_class"),
            "source_uri": source.get("source_uri"),
            "observed_at_utc": observed,
        })

    missing = sorted(required - set(values_by_fact))
    conflicts = []
    stale_facts = []
    fact_assessments = []
    for key, entries in sorted(values_by_fact.items()):
        canonical = {_digest(entry["value"]) for entry in entries}
        conflict = len(canonical) > 1
        if conflict:
            conflicts.append(key)
        official_count = sum(
            1 for entry in entries
            if str(entry.get("source_class", "")).startswith("official_")
            or entry.get("source_class") in {"regulator_notice", "exchange_rulebook", "broker_client_agreement"}
        )
        policy = next((item for item in facts
                       if isinstance(item, dict) and item.get("fact_key") == key
                       and item.get("max_age_days") is not None), None)
        max_age_days = policy.get("max_age_days") if policy else None
        if max_age_days is not None:
            if (not isinstance(max_age_days, (int, float))
                    or isinstance(max_age_days, bool) or max_age_days < 0):
                errors.append(f"fact {key} max_age_days must be non-negative")
            elif as_of is not None:
                for entry in entries:
                    observed_at = _utc(entry["observed_at_utc"])
                    if observed_at is not None and (as_of - observed_at).total_seconds() > max_age_days * 86400:
                        if key not in stale_facts:
                            stale_facts.append(key)
        fact_assessments.append({
            "fact_key": key, "source_count": len(entries),
            "official_class_source_count": official_count,
            "conflict": conflict, "values": entries,
            "critical": key in CRITICAL_FACTS,
            "max_age_days": max_age_days,
            "freshness": "STALE" if key in stale_facts else ("POLICY_DEFINED" if max_age_days is not None else "NOT_ASSESSED_NO_TTL"),
        })
    critical_missing = sorted(CRITICAL_FACTS.intersection(missing))
    if errors:
        status = "INVALID_EVIDENCE_BUNDLE"
    elif conflicts:
        status = "BLOCKED_CONFLICTING_EVIDENCE"
    elif stale_facts:
        status = "BLOCKED_STALE_EVIDENCE"
    elif missing:
        status = "INCOMPLETE_EVIDENCE_COVERAGE"
    else:
        status = "EVIDENCE_COVERAGE_COMPLETE_UNVERIFIED"
    return {
        "status": status, "instrument_type": instrument_type,
        "required_fact_count": len(required), "covered_fact_count": len(required.intersection(values_by_fact)),
        "missing_fact_keys": missing, "critical_missing_fact_keys": critical_missing,
        "conflicting_fact_keys": conflicts, "stale_fact_keys": sorted(stale_facts),
        "fact_assessments": fact_assessments,
        "source_count": len(sources), "evidence_authenticity": "NOT_AUTHENTICATED",
        "source_independence_verified": False,
        "authority": AUTHORITY, "research_only": True,
        "profile_approval_performed": False, "trade_authority": False,
        "live_readiness": False,
        "limitations": [
            "Source metadata and extracted values are supplied by the caller.",
            "A content hash does not authenticate a publisher, URL, capture process or document.",
            "Matching values do not prove independent corroboration.",
            "Coverage completeness is not factual correctness or operational approval.",
        ],
    }


def prepare_profile_draft(bundle: Any, as_of_utc: str) -> dict[str, Any]:
    """Prepare a non-approved draft only when evidence coverage is complete and conflict-free."""
    assessment = assess_evidence_bundle(bundle, as_of_utc)
    if assessment["status"] != "EVIDENCE_COVERAGE_COMPLETE_UNVERIFIED":
        return {
            "status": "BLOCKED_PROFILE_DRAFT",
            "errors": assessment.get("missing_fact_keys", []) + assessment.get("conflicting_fact_keys", []),
            "evidence_assessment": assessment, "profile_draft": None,
            "profile_approval_performed": False, "trade_authority": False,
            "live_readiness": False, "authority": AUTHORITY,
        }
    facts = bundle["facts"]
    extracted = {}
    for fact in facts:
        extracted[fact["fact_key"]] = fact["value"]
    source_records = []
    for source in bundle["sources"]:
        source_records.append({
            "source_id": source["source_id"],
            "source_uri": source["source_uri"],
            "source_type": source["source_class"],
            "captured_at_utc": source["captured_at_utc"],
            "evidence_sha256": source["content_sha256"],
        })
    draft = {
        "venue_id": bundle.get("venue_id"),
        "instrument_id": bundle.get("instrument_id"),
        "instrument_type": bundle.get("instrument_type"),
        "extracted_facts": extracted,
        "provenance": source_records,
        "profile_state": "under_review",
        "verification_state": "unverified",
        "review_state": "pending",
        "effective_from_utc": as_of_utc,
        "venue_spec_candidate": {
            key: extracted[key] for key in (
                "contract_multiplier", "quote_currency", "initial_margin_rate",
                "maintenance_tiers", "mark_price_rule", "liquidation_fee_rate",
                "max_impact_bps", "impact_coefficient", "liquidation_buffer_ratio",
                "partial_liquidation_supported",
            ) if key in extracted
        },
        "contract_profile_candidate": {
            key: extracted[key] for key in (
                "settlement_currency", "expiry_utc", "contract_code",
                "settlement_method", "roll_method", "financing_convention",
            ) if key in extracted
        },
    }
    return {
        "status": "PROFILE_DRAFT_PREPARED_NOT_APPROVED",
        "errors": [], "evidence_assessment": assessment,
        "profile_draft": draft, "profile_approval_performed": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
    }


def build_research_intake_report(bundles: list[dict[str, Any]], as_of_utc: str) -> dict[str, Any]:
    """Aggregate per-instrument evidence readiness; never rank trade opportunities."""
    results = []
    for bundle in bundles if isinstance(bundles, list) else []:
        if not isinstance(bundle, dict):
            results.append({"status": "INVALID_EVIDENCE_BUNDLE", "errors": ["bundle must be an object"]})
            continue
        results.append({
            "venue_id": bundle.get("venue_id"),
            "instrument_id": bundle.get("instrument_id"),
            "instrument_type": bundle.get("instrument_type"),
            "assessment": assess_evidence_bundle(bundle, as_of_utc),
        })
    counts: dict[str, int] = {}
    for item in results:
        status = item.get("assessment", item).get("status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION, "generated_at_utc": as_of_utc,
        "results": results, "status_counts": counts,
        "authority": AUTHORITY, "research_only": True,
        "profile_approval_performed": False, "trade_authority": False,
        "live_readiness": False,
    }
