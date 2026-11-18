"""Validation and reporting for captured official venue-document excerpts.

This is an evidence inventory, not a complete-document archive or source
authentication system. The manifest deliberately distinguishes page excerpts
from full-document byte capture.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from specialist_research.venue_document_revisions import (
    AUTHORITY, validate_revision,
)

EXPECTED_CANDIDATES = {
    "kraken_mtf_crypto_linear_derivatives", "coinbase_intx_crypto_perpetuals",
    "oanda_canada_fx_cfd", "oanda_canada_index_cfd", "oanda_canada_gold_cfd",
    "cme_comex_gold_futures", "cme_equity_index_futures",
}


def validate_capture_manifest(manifest: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    if manifest.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if manifest.get("manifest_status") != "PARTIAL_OFFICIAL_EXCERPT_CAPTURE_NOT_FULL_DOCUMENTS":
        errors.append("manifest_status must explicitly identify partial excerpt capture")
    capture_date = manifest.get("capture_date")
    try:
        date.fromisoformat(capture_date)
    except (TypeError, ValueError):
        errors.append("capture_date must be an ISO date")
    if manifest.get("capture_time_precision") != "date_only_normalized_to_utc_midnight":
        errors.append("capture time precision must disclose date-only normalization")
    controls = manifest.get("global_controls")
    if not isinstance(controls, dict):
        errors.append("global_controls must be an object")
        controls = {}
    for key in ("full_document_capture", "publisher_identity_verified",
                "source_timestamp_trusted", "automatic_profile_update",
                "profile_approval", "trade_authority", "live_readiness"):
        if controls.get(key) is not False:
            errors.append(f"global_controls.{key} must remain false")
    if controls.get("source_authentication") != "NOT_PERFORMED":
        errors.append("source authentication must remain NOT_PERFORMED")
    if controls.get("research_only") is not True:
        errors.append("research_only must remain true")

    captures = manifest.get("captures")
    if not isinstance(captures, list) or not captures:
        return errors + ["captures must be a non-empty array"]
    seen_docs: set[str] = set()
    for index, capture in enumerate(captures):
        prefix = f"captures[{index}]"
        if not isinstance(capture, dict):
            errors.append(f"{prefix} must be an object")
            continue
        errors.extend(f"{prefix}: {error}" for error in validate_revision(capture))
        document_id = capture.get("document_id")
        if isinstance(document_id, str):
            if document_id in seen_docs:
                errors.append(f"{prefix}.document_id is duplicated")
            seen_docs.add(document_id)
        if capture.get("capture_scope") != "official_page_search_excerpt":
            errors.append(f"{prefix}.capture_scope must disclose official-page excerpt")
        if capture.get("full_document_capture") is not False:
            errors.append(f"{prefix}.full_document_capture must be false")
        if capture.get("retrieval_method") not in {"official_web_search_excerpt", "official_web_open_excerpt"}:
            errors.append(f"{prefix}.retrieval_method is unsupported")
        if not isinstance(capture.get("source_ref"), str) or not capture["source_ref"].startswith("turn"):
            errors.append(f"{prefix}.source_ref must preserve the research reference")
        candidate_ids = capture.get("candidate_ids")
        if not isinstance(candidate_ids, list) or not candidate_ids:
            errors.append(f"{prefix}.candidate_ids must be a non-empty array")
        elif any(item not in EXPECTED_CANDIDATES for item in candidate_ids):
            errors.append(f"{prefix}.candidate_ids contains an unknown candidate")

    coverage = manifest.get("candidate_coverage")
    if not isinstance(coverage, list):
        errors.append("candidate_coverage must be an array")
        coverage = []
    seen_candidates: set[str] = set()
    for index, item in enumerate(coverage):
        prefix = f"candidate_coverage[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = item.get("candidate_id")
        if candidate_id not in EXPECTED_CANDIDATES:
            errors.append(f"{prefix}.candidate_id is unknown")
        elif candidate_id in seen_candidates:
            errors.append(f"{prefix}.candidate_id is duplicated")
        else:
            seen_candidates.add(candidate_id)
        doc_ids = item.get("document_ids")
        if not isinstance(doc_ids, list) or not doc_ids:
            errors.append(f"{prefix}.document_ids must be non-empty")
        elif any(doc_id not in seen_docs for doc_id in doc_ids):
            errors.append(f"{prefix}.document_ids references an uncaptured document")
    if seen_candidates != EXPECTED_CANDIDATES:
        errors.append("candidate_coverage must include all seven catalogue candidates")
    return errors


def build_capture_report(manifest: Any) -> dict[str, Any]:
    errors = validate_capture_manifest(manifest)
    captures = manifest.get("captures", []) if isinstance(manifest, dict) else []
    coverage = manifest.get("candidate_coverage", []) if isinstance(manifest, dict) else []
    docs = []
    for capture in captures if isinstance(captures, list) else []:
        if not isinstance(capture, dict):
            continue
        docs.append({
            "document_id": capture.get("document_id"),
            "revision_id": capture.get("revision_id"),
            "source_ref": capture.get("source_ref"),
            "retrieval_method": capture.get("retrieval_method"),
            "title": capture.get("title"),
            "publisher": capture.get("publisher"),
            "source_uri": capture.get("canonical_uri"),
            "candidate_ids": capture.get("candidate_ids", []),
            "capture_scope": capture.get("capture_scope"),
            "full_document_capture": False,
            "fact_count": len(capture.get("extracted_facts", []))
                if isinstance(capture.get("extracted_facts"), list) else 0,
            "known_gaps": capture.get("known_gaps", []),
            "source_authentication": "NOT_PERFORMED",
            "profile_eligible": False,
        })
    return {
        "status": "INVALID_CAPTURE_MANIFEST" if errors else "PARTIAL_EVIDENCE_CAPTURE_VALID",
        "errors": errors,
        "document_count": len(docs),
        "candidate_count": len(coverage) if isinstance(coverage, list) else 0,
        "documents": docs,
        "capture_scope": "official_page_search_excerpts_only",
        "full_document_capture": False,
        "source_authentication": "NOT_PERFORMED",
        "profile_creation": "NOT_PERFORMED",
        "profile_approval": "NOT_PERFORMED",
        "authority": AUTHORITY,
        "research_only": True,
        "trade_authority": False,
        "live_readiness": False,
    }
