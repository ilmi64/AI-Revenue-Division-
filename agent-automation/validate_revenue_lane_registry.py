#!/usr/bin/env python3
"""Validate the review-only revenue source registry and write an executive coverage report."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

ALLOWED_LANES = {
    "ai_development", "freelance_services", "ai_evaluation", "digital_products",
    "grants_sponsorships", "security_testing", "research_tasks", "github_bounties",
    "remote_employment",
}
COVERAGE_STATES = {
    "candidate_sources_listed", "gap_research_required",
    "existing_connector", "existing_connectors",
}

def validate_registry(data: dict) -> tuple[dict, list[str]]:
    errors = []
    policy = data.get("policy", {})
    if policy.get("external_accounts_connected") is not False:
        errors.append("Registry must explicitly state external_accounts_connected=false")
    if policy.get("default_budget_cad") != 0:
        errors.append("Registry must preserve a CAD $0 default budget")
    if policy.get("approval_required_for_external_actions") is not True:
        errors.append("External actions must require owner approval")

    sources = data.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")
    source_map = {}
    for source in sources:
        if not isinstance(source, dict):
            errors.append("Ignored non-object source")
            continue
        source_id = str(source.get("id", "")).strip()
        if not source_id or source_id in source_map:
            errors.append(f"Missing or duplicate source id: {source_id or '<blank>'}")
            continue
        source_map[source_id] = source
        for key in ("name", "source_type", "official_url", "evidence_url"):
            if not str(source.get(key, "")).strip():
                errors.append(f"{source_id}: missing {key}")
        for key in ("official_url", "evidence_url"):
            if not str(source.get(key, "")).startswith("https://"):
                errors.append(f"{source_id}: {key} must use HTTPS")
        if source.get("integration_status") not in (
            "not_connected", "manual_research_only", "existing_read_only_connector",
            "read_only_connector_with_candidate_boards_pending_runtime_validation",
        ):
            errors.append(f"{source_id}: unsupported or unsafe integration_status")
        if source.get("human_review_required") is not True:
            errors.append(f"{source_id}: human_review_required must be true")
        if not isinstance(source.get("lanes"), list) or not source["lanes"]:
            errors.append(f"{source_id}: lanes must be a non-empty list")
        else:
            for lane in source["lanes"]:
                if lane not in ALLOWED_LANES:
                    errors.append(f"{source_id}: unsupported lane {lane}")

    lanes = data.get("lanes", [])
    if not isinstance(lanes, list):
        raise ValueError("lanes must be a list")
    lane_ids = set()
    coverage = []
    for lane in lanes:
        if not isinstance(lane, dict):
            errors.append("Ignored non-object lane")
            continue
        lane_id = lane.get("id")
        if lane_id not in ALLOWED_LANES or lane_id in lane_ids:
            errors.append(f"Missing, duplicate or unsupported lane id: {lane_id}")
            continue
        lane_ids.add(lane_id)
        source_ids = lane.get("source_ids", [])
        if not isinstance(source_ids, list):
            errors.append(f"{lane_id}: source_ids must be a list")
            source_ids = []
        unknown = [sid for sid in source_ids if sid not in source_map]
        if unknown:
            errors.append(f"{lane_id}: unknown source ids: {', '.join(unknown)}")
        mapped = [sid for sid in source_ids if sid in source_map]
        for sid in mapped:
            if lane_id not in source_map[sid].get("lanes", []):
                errors.append(f"{lane_id}: source {sid} does not map back to this lane")
        state = lane.get("coverage_status")
        if state not in COVERAGE_STATES:
            errors.append(f"{lane_id}: unsupported coverage_status {state}")
        if not mapped and state != "gap_research_required":
            errors.append(f"{lane_id}: empty source list must be explicitly marked gap_research_required")
        if mapped and state == "gap_research_required":
            errors.append(f"{lane_id}: research gap cannot also have active source candidates")
        coverage.append({
            "lane": lane_id,
            "label": str(lane.get("label") or lane_id),
            "coverage_status": state,
            "source_count": len(mapped),
            "source_ids": mapped,
            "next_step": str(lane.get("next_step") or ""),
        })

    missing_lanes = sorted(ALLOWED_LANES - lane_ids)
    for lane_id in missing_lanes:
        errors.append(f"Registry is missing supported lane {lane_id}")
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "registry_valid": not errors,
        "source_count": len(source_map),
        "lane_count": len(coverage),
        "covered_lane_count": sum(1 for x in coverage if x["source_count"]),
        "research_gap_count": sum(1 for x in coverage if x["coverage_status"] == "gap_research_required"),
        "coverage": coverage,
        "source_status": {sid: source.get("integration_status") for sid, source in source_map.items()},
        "external_accounts_connected": False,
        "default_budget_cad": 0,
        "errors": errors,
        "note": "Source directory and lane coverage only. It does not verify current vacancies, task supply, Canada eligibility, payment, commercial demand, or income."
    }
    return report, errors

def render_markdown(report: dict) -> str:
    lines = [
        "# Revenue Lane Coverage Report", "",
        f"Generated: {report['generated_at']}", "",
        f"**Registry valid:** {report['registry_valid']}",
        f"**Sources listed:** {report['source_count']}",
        f"**Lanes with candidate/existing sources:** {report['covered_lane_count']}/{report['lane_count']}",
        f"**Research gaps:** {report['research_gap_count']}", "",
        "| Revenue lane | Coverage | Sources |",
        "|---|---|---:|",
    ]
    for item in report["coverage"]:
        lines.append(f"| {item['label']} | {item['coverage_status']} | {item['source_count']} |")
    lines.extend(["", "## Operating controls", "",
        "- All external sources remain review-only; account integrations are not created by this registry.",
        "- No application, client contact, claim, security test, submission, publishing, purchase, invoice or payment is authorized.",
        "- Confirm Canadian/Ontario eligibility, fees, KYC, payout methods, minimums, timing, tax treatment and platform terms before acting.",
        "- Grants are conditional project support, not personal income; ordinary GitHub issues are not presumed paid.",
        "- Do not treat source counts, advertised rates, task availability or funding ceilings as earnings.",
        "", "## Research gaps", ""])
    for item in report["coverage"]:
        if item["coverage_status"] == "gap_research_required":
            lines.append(f"- **{item['label']}:** {item['next_step']}")
    lines.extend(["", "No external action is authorized by this report.", ""])
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="agent-automation/revenue-lane-registry.json")
    parser.add_argument("--output-dir", default="executive-output")
    args = parser.parse_args()
    data = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    report, errors = validate_registry(data)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "revenue-lane-coverage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "revenue-lane-coverage.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"Revenue lane registry: {report['covered_lane_count']}/{report['lane_count']} lanes have sources; {len(errors)} validation errors.")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
