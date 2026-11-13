#!/usr/bin/env python3
"""Prepare a financial due-diligence checklist from risk-reviewed opportunity leads.

This module does not estimate or promise earnings, convert currencies, contact sponsors,
submit claims, create invoices, or initiate payments.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

def assess(item: dict) -> dict:
    findings = []
    if not str(item.get("url", "")).startswith("https://"):
        findings.append("Source URL is missing or invalid.")
    # Search-derived metadata is not proof of a commercial offer.
    findings.append("Named sponsor and legal contracting entity have not been verified.")
    findings.append("Reward amount, currency and payment conditions have not been verified.")
    findings.append("Escrow or other payout protection has not been verified.")
    findings.append("Canadian/Ontario eligibility, tax treatment and payout access have not been verified.")
    findings.append("Payment fees, minimum withdrawal, payment timing and dispute process have not been verified.")
    findings.append("Acceptance, approval and payment are not guaranteed.")
    return {
        "title": item.get("title", "Untitled opportunity"),
        "url": item.get("url", ""),\n        "lane": item.get("lane", "github_bounties"),\n        "source_name": item.get("source_name", "GitHub"),
        "eligibility_hint": item.get("eligibility_hint", "unknown"),
        "source_attribution": item.get("source_attribution", ""),
        "commercial_status": "unverified_lead",
        "reward_amount": None,
        "reward_currency": None,
        "estimated_net_amount": None,
        "payment_method": None,
        "payout_timing": None,
        "canada_eligibility": "unverified",
        "escrow_status": "unverified",
        "tax_status": "requires_independent_review",
        "findings": findings,
        "required_evidence": [
            "Official sponsor identity and terms",
            "Explicit reward amount and currency",
            "Written acceptance criteria and payment trigger",
            "Canadian participant eligibility",
            "Payout method, minimum, fees and timing",
            "Escrow terms or clear explanation of payment risk",
            "Applicable tax and record-keeping requirements",
        ],
        "approval_gate": "Do not claim, apply, contact, invoice, or perform paid work until a human verifies terms and explicitly approves the next action.",
    }

def build_report(payload: dict) -> dict:
    records = payload.get("results", [])
    if not isinstance(records, list):
        raise ValueError("Input 'results' must be a list")
    assessments = [assess(x) for x in records if isinstance(x, dict)]
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "opportunities_reviewed": len(assessments),
        "verified_paid_opportunities": 0,
        "assessments": assessments,
        "accounting_note": "No earnings, receivables or cash receipts are recognized from discovery leads.",
        "disclaimer": "Due-diligence checklist only; not legal, tax, accounting or financial advice.",
    }

def render_markdown(report: dict) -> str:
    lines = [
        "# Finance & Payout Due-Diligence Report", "",
        "> Discovery leads are not earnings. No payment or eligibility has been verified.", "",
        f"Leads assessed: {report['opportunities_reviewed']}",
        f"Verified paid opportunities: {report['verified_paid_opportunities']}", "",
        "| Opportunity | Status | Reward | Canada | Escrow |",
        "|---|---|---|---|---|",
    ]
    for item in report["assessments"]:
        title = str(item["title"]).replace("|", "\\|")
        lines.append(f"| [{title}]({item['url']}) | {item['commercial_status']} | Not verified | Unverified | Unverified |")
    lines.extend(["", "## Required checks before treating an opportunity as commercial work", "",
        "- Verify the sponsor, reward, currency and payment trigger from official terms.",
        "- Verify Canadian eligibility, payout route, minimums, fees and timing.",
        "- Verify escrow, dispute rights and acceptance conditions.",
        "- Keep projected rewards, accepted rewards, invoices and received funds in separate records.",
        "- Do not recognize a lead as income or receivable before the relevant work is accepted under verified terms.",
        "- Obtain human approval before claims, applications, contact, invoices or any financial action.",
        "", "Tax treatment and reporting obligations require independent review for the user's circumstances.", ""])
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="opportunity-output/all-opportunities.json")
    parser.add_argument("--output-dir", default="finance-output")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = build_report(payload)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "finance-payout-review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "finance-payout-review.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"Prepared financial due-diligence checks for {report['opportunities_reviewed']} leads.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
