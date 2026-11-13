#!/usr/bin/env python3
"""Aggregate division artifacts into a factual executive readiness report."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

def load_json(path: str) -> dict | None:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except FileNotFoundError:
        return None

def build_report(opportunities: dict | None, triage: dict | None,
                 risk: dict | None, finance: dict | None,
                 lane_registry: dict | None = None) -> dict:
    missing = [name for name, value in (
        ("unified_division_intake", opportunities), ("development_triage", triage),
        ("risk_review", risk), ("finance_review", finance)) if value is None]
    discovery_count = len(opportunities.get("results", [])) if opportunities else 0
    triage_count = triage.get("lead_count", 0) if triage else 0
    risk_count = risk.get("reviewed_count", 0) if risk else 0
    finance_count = finance.get("opportunities_reviewed", 0) if finance else 0
    lane_coverage = None
    if lane_registry is not None:
        lane_coverage = {
            "registry_valid": lane_registry.get("registry_valid", False),
            "source_count": lane_registry.get("source_count", 0),
            "lane_count": lane_registry.get("lane_count", 0),
            "covered_lane_count": lane_registry.get("covered_lane_count", 0),
            "research_gap_count": lane_registry.get("research_gap_count", 0),
            "coverage": lane_registry.get("coverage", []),
            "external_accounts_connected": lane_registry.get("external_accounts_connected", False),
        }
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "division": "Revenue Intelligence",
        "pipeline": ["revenue_lane_registry", "opportunity_discovery", "development_triage", "risk_review", "finance_review"],
        "artifacts_missing": missing,
        "counts": {"discovered": discovery_count, "triaged": triage_count,
                   "risk_reviewed": risk_count, "finance_reviewed": finance_count},
        "revenue_lane_coverage": lane_coverage,
        "verified_paid_opportunities": 0,
        "cash_received": 0,
        "readiness": "incomplete" if missing else "human_review_required",
        "blockers": [
            "Workflow execution and all tests must be verified from a real Actions run.",
            "Every opportunity requires source-level human verification.",
            "Funding, Canadian eligibility, escrow, acceptance and payout must be independently confirmed.",
            "No application, claim, sponsor contact, submission or financial action is authorized by this report.",
        ],
        "missing_artifacts": missing,
        "disclaimer": "Counts describe available report records only; they do not represent earnings, accepted work or cash received.",
    }

def render_markdown(report: dict) -> str:
    c = report["counts"]
    lines = [
        "# Executive Revenue Intelligence Report", "",
        f"Generated: {report['generated_at']}", "",
        f"**Readiness:** {report['readiness']}", "",
        "| Pipeline stage | Records |", "|---|---:|",
        f"| Discovered | {c['discovered']} |",
        f"| Development triage | {c['triaged']} |",
        f"| Risk reviewed | {c['risk_reviewed']} |",
        f"| Finance reviewed | {c['finance_reviewed']} |",
    ]
    lane = report.get("revenue_lane_coverage")
    if lane is not None:
        lines.extend([
            "", "## Revenue lane coverage", "",
            f"- Candidate/existing source coverage: {lane['covered_lane_count']}/{lane['lane_count']} lanes",
            f"- Source directory entries: {lane['source_count']}",
            f"- Research gaps: {lane['research_gap_count']}",
            "- External accounts connected by registry: no",
            "",
            "| Lane | Coverage | Sources |", "|---|---|---:|",
        ])
        for item in lane.get("coverage", []):
            lines.append(f"| {item.get('label', item.get('lane'))} | {item.get('coverage_status')} | {item.get('source_count', 0)} |")
    lines.extend([
        "", "## Financial status", "",
        "- Verified paid opportunities: 0 recorded",
        "- Cash received: 0 recorded",
        "- These are conservative system counters, not a statement about the user's external accounts.",
        "", "## Blockers", "",
    ])
    lines.extend([f"- {x}" for x in report["blockers"]])
    if report["artifacts_missing"]:
        lines.extend(["", "## Missing artifacts", ""])
        lines.extend([f"- {x}" for x in report["artifacts_missing"]])
    lines.extend(["", "No external action is authorized by this report.", ""])
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="executive-output")
    args = parser.parse_args()
    report = build_report(
        load_json("opportunity-output/all-opportunities.json"),
        load_json("development-output/engineering-triage.json"),
        load_json("risk-output/risk-review.json"),
        load_json("finance-output/finance-payout-review.json"),
        load_json("executive-output/revenue-lane-coverage.json"),
    )
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "executive-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "executive-report.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"Executive readiness: {report['readiness']}; missing artifacts: {len(report['artifacts_missing'])}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
