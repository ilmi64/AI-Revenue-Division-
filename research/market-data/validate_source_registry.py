"""Fail-closed validation for research-only market-data source candidates."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ALLOWED_STATUSES = {
    "candidate_read_only_adapter_exists", "candidate_not_configured",
    "review_required", "candidate_reference_only",
    "candidate_plan_restrictions_unverified", "candidate_unverified",
    "not_connected_owner_approval_required"
}
REQUIRED_SOURCE_FIELDS = {"name", "endpoint_class", "status", "evidence", "terms_review", "canada_review"}

def validate_registry(registry):
    errors, warnings = [], []
    if not isinstance(registry, dict):
        return {"status": "invalid", "errors": ["Registry must be a JSON object."], "warnings": [], "instrument_count": 0, "source_count": 0, "live_approved_count": 0}
    if registry.get("status") != "candidate_registry_research_only":
        errors.append("Registry status must remain candidate_registry_research_only.")
    if registry.get("production_approval") not in (None, "none"):
        errors.append("Production approval is prohibited in this research-only registry.")
    instruments = registry.get("instruments")
    if not isinstance(instruments, list):
        instruments = []
        errors.append("instruments must be an array.")
    seen = set()
    source_count = 0
    live_approved = 0
    for i, instrument in enumerate(instruments):
        if not isinstance(instrument, dict):
            errors.append(f"Instrument at index {i} must be an object.")
            continue
        instrument_id = instrument.get("id")
        if not isinstance(instrument_id, str) or not instrument_id.strip() or instrument_id in seen:
            errors.append(f"Instrument at index {i} requires a unique non-empty id.")
        seen.add(instrument_id)
        if not instrument.get("asset_class") or not instrument.get("market") or not instrument.get("purpose"):
            errors.append(f"{instrument_id}: asset_class, market and purpose are required.")
        candidates = instrument.get("candidate_sources")
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"{instrument_id}: at least one candidate source record is required.")
            continue
        names = set()
        for j, source in enumerate(candidates):
            source_count += 1
            if not isinstance(source, dict):
                errors.append(f"{instrument_id}: source {j} must be an object.")
                continue
            missing = REQUIRED_SOURCE_FIELDS - set(source)
            if missing:
                errors.append(f"{instrument_id}: source {j} missing fields {sorted(missing)}.")
            name = source.get("name")
            if not isinstance(name, str) or not name.strip() or name in names:
                errors.append(f"{instrument_id}: source names must be unique non-empty strings.")
            names.add(name)
            if source.get("status") not in ALLOWED_STATUSES:
                errors.append(f"{instrument_id}/{name}: status is not an allowed research-only state.")
            if source.get("terms_review") != "pending" or source.get("canada_review") != "pending":
                errors.append(f"{instrument_id}/{name}: terms and Canadian review must remain pending until evidenced.")
            if source.get("status") in {"approved", "production", "live_enabled"}:
                live_approved += 1
    policy = registry.get("policy", {})
    if not isinstance(policy, dict) or policy.get("default_spend_cad") != 0:
        errors.append("Policy must retain the CAD 0 default spend.")
    if live_approved:
        errors.append("Live-approved sources are prohibited in the research-only registry.")
    if not registry.get("global_gaps"):
        warnings.append("Global evidence gaps should be recorded.")
    return {
        "status": "validated" if not errors else "invalid",
        "instrument_count": len(seen),
        "source_count": source_count,
        "live_approved_count": live_approved,
        "errors": errors,
        "warnings": warnings,
        "authority": "research_intake_only_no_live_data_or_execution_authority"
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("research/market-data/source-registry.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with args.registry.open(encoding="utf-8") as handle:
        report = validate_registry(json.load(handle))
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "validated" else 1

if __name__ == "__main__":
    raise SystemExit(main())
