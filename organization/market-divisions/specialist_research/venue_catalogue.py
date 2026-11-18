"""Validation and readiness reporting for the offline venue research catalogue."""
from __future__ import annotations

from typing import Any

AUTHORITY = "research_only_no_execution_authority"
DIVISIONS = {"crypto", "forex", "indices", "gold"}
INSTRUMENT_TYPES = {
    "crypto_perpetual", "forex_cfd", "index_future", "index_cfd",
    "gold_future", "gold_cfd",
}


def validate_catalogue(catalogue: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(catalogue, dict):
        return ["catalogue must be an object"]
    if catalogue.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if catalogue.get("catalogue_status") != "candidate_research_only":
        errors.append("catalogue_status must remain candidate_research_only")
    if catalogue.get("jurisdiction", {}).get("country") != "Canada":
        errors.append("catalogue jurisdiction must identify Canada")
    if catalogue.get("jurisdiction", {}).get("province") != "Ontario":
        errors.append("catalogue jurisdiction must identify Ontario")
    if catalogue.get("jurisdiction", {}).get("eligibility_status") != "UNVERIFIED_FOR_EACH_PROVIDER_AND_PRODUCT":
        errors.append("provider/product eligibility must remain explicitly unverified")
    candidates = catalogue.get("candidates")
    if not isinstance(candidates, list):
        return errors + ["candidates must be an array"]
    seen_candidates: set[str] = set()
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            errors.append(f"{prefix}.candidate_id is required")
        elif candidate_id in seen_candidates:
            errors.append(f"{prefix}.candidate_id is duplicated")
        else:
            seen_candidates.add(candidate_id)
        if candidate.get("division") not in DIVISIONS:
            errors.append(f"{prefix}.division is unsupported")
        types = candidate.get("instrument_types")
        if not isinstance(types, list) or not types or any(item not in INSTRUMENT_TYPES for item in types):
            errors.append(f"{prefix}.instrument_types is invalid")
        if candidate.get("jurisdiction_status") is None:
            errors.append(f"{prefix}.jurisdiction_status is required")
        if candidate.get("candidate_status") not in {
            "official_product_documentation_located",
            "official_canada_documentation_located",
            "official_contract_documentation_located",
        }:
            errors.append(f"{prefix}.candidate_status is unsupported")
        sources = candidate.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{prefix}.sources must be a non-empty array")
            continue
        source_ids: set[str] = set()
        for source_index, source in enumerate(sources):
            sp = f"{prefix}.sources[{source_index}]"
            if not isinstance(source, dict):
                errors.append(f"{sp} must be an object")
                continue
            for key in ("source_id", "source_uri", "source_class", "reviewed_at_utc"):
                if not isinstance(source.get(key), str) or not source[key].strip():
                    errors.append(f"{sp}.{key} is required")
            if source.get("source_id") in source_ids:
                errors.append(f"{sp}.source_id is duplicated within candidate")
            source_ids.add(source.get("source_id"))
            if not source.get("source_uri", "").startswith("https://"):
                errors.append(f"{sp}.source_uri must use HTTPS")
            if source.get("full_document_capture") is not False:
                errors.append(f"{sp}.full_document_capture must remain false until actual capture is recorded")
            if source.get("source_content_hash") is not None:
                errors.append(f"{sp}.source_content_hash must remain null until bytes are captured and hashed")
    controls = catalogue.get("global_controls", {})
    if controls.get("profile_creation") != "not_performed":
        errors.append("profile_creation must remain not_performed")
    if controls.get("profile_approval") != "not_performed":
        errors.append("profile_approval must remain not_performed")
    if controls.get("source_authentication") != "not_performed":
        errors.append("source_authentication must remain not_performed")
    if controls.get("trade_authority") is not False or controls.get("live_readiness") is not False:
        errors.append("trade_authority and live_readiness must remain false")
    if controls.get("research_only") is not True:
        errors.append("research_only must remain true")
    return errors


def build_catalogue_report(catalogue: Any) -> dict[str, Any]:
    errors = validate_catalogue(catalogue)
    candidates = catalogue.get("candidates", []) if isinstance(catalogue, dict) else []
    results = []
    for candidate in candidates if isinstance(candidates, list) else []:
        if not isinstance(candidate, dict):
            continue
        sources = candidate.get("sources", [])
        captured = [
            source for source in sources if isinstance(source, dict)
            and source.get("full_document_capture") is True
            and isinstance(source.get("source_content_hash"), str)
        ]
        results.append({
            "candidate_id": candidate.get("candidate_id"),
            "provider": candidate.get("provider"),
            "division": candidate.get("division"),
            "instrument_types": candidate.get("instrument_types"),
            "source_count": len(sources) if isinstance(sources, list) else 0,
            "captured_source_count": len(captured),
            "status": "DOCUMENTATION_CAPTURED_NOT_AUTHENTICATED" if captured else "DOCUMENTATION_LOCATED_NOT_CAPTURED",
            "jurisdiction_status": candidate.get("jurisdiction_status"),
            "profile_eligible": False,
            "operational_readiness": False,
        })
    return {
        "status": "INVALID_CATALOGUE" if errors else "CANDIDATE_CATALOGUE_VALID",
        "errors": errors, "candidate_count": len(results),
        "division_coverage": sorted({item["division"] for item in results}),
        "candidates": results,
        "source_authentication": "NOT_PERFORMED",
        "profile_creation": "NOT_PERFORMED",
        "profile_approval": "NOT_PERFORMED",
        "authority": AUTHORITY, "research_only": True,
        "trade_authority": False, "live_readiness": False,
    }
