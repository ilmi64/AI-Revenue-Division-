#!/usr/bin/env python3
"""Convert discovery leads into cautious, human-reviewable engineering triage briefs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

def triage(item: dict) -> dict:
    title = str(item.get("title", "")).strip()
    url = str(item.get("url", "")).strip()
    signals = set(item.get("signals", []))
    score = 0
    reasons = []
    if "bounty_keyword" in signals:
        score += 2
        reasons.append("Bounty-related wording detected")
    if "payment_keyword" in signals:
        score += 2
        reasons.append("Payment-related wording detected")
    if "accessibility_keyword" in signals:
        score += 1
        reasons.append("Potential accessibility signal detected")
    if not title or not url.startswith("https://github.com/"):
        score = 0
        reasons.append("Missing title or non-GitHub source URL; manual correction required")
    return {
        "title": title or "Untitled lead",
        "url": url,
        "triage_score": score,
        "triage_reasons": reasons,
        "priority": "review_first" if score >= 4 else "review_later" if score > 0 else "hold",
        "verified_scope": False,
        "verified_effort": False,
        "verified_acceptance_criteria": False,
        "recommended_next_step": "Open the source issue and manually inspect its full description, comments, acceptance criteria, sponsor and current status.",
        "do_not": ["Do not claim or assign the issue", "Do not contact the sponsor", "Do not submit code or a pull request", "Do not treat keywords or score as proof of payment"],
    }

def build_report(payload: dict) -> dict:
    items = payload.get("results", [])
    if not isinstance(items, list):
        raise ValueError("Input 'results' must be a list")
    briefs = [triage(x) for x in items if isinstance(x, dict)]
    briefs.sort(key=lambda x: (x["triage_score"], x["title"].lower()), reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_generated_at": payload.get("generated_at"),
        "lead_count": len(briefs),
        "briefs": briefs,
        "disclaimer": "Heuristic triage only. No source issue was opened or independently verified by this agent.",
    }

def render_markdown(report: dict) -> str:
    lines = ["# Engineering Opportunity Triage", "",
             "> Heuristic prioritisation only. This is not a verified job, funded bounty, or commitment.", "",
             f"Leads reviewed: {report['lead_count']}", "",
             "| Priority | Score | Lead |", "|---|---:|---|"]
    for b in report["briefs"]:
        title = b["title"].replace("|", "\\|")
        lines.append(f"| {b['priority']} | {b['triage_score']} | [{title}]({b['url']}) |")
    lines.extend(["", "## Required human review", "",
        "1. Read the complete issue, comments and linked specifications.",
        "2. Confirm sponsor, funding amount, payout mechanism, escrow and Canadian eligibility.",
        "3. Check whether the issue is already assigned, claimed, solved or under review.",
        "4. Define acceptance criteria and estimate effort before choosing to work.",
        "5. Obtain approval before any claim, application, sponsor contact, code publication or submission.",
        "", "Scores reflect search-keyword signals only; they do not estimate technical difficulty or probability of payment.", ""])
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="opportunity-output/github-opportunities.json")
    parser.add_argument("--output-dir", default="development-output")
    args = parser.parse_args()
    source = Path(args.input)
    payload = json.loads(source.read_text(encoding="utf-8"))
    report = build_report(payload)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "engineering-triage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "engineering-triage.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"Prepared {report['lead_count']} engineering triage briefs.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
