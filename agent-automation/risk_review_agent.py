#!/usr/bin/env python3
"""Deterministic safety gate for engineering opportunity triage reports."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

REQUIRED_FALSE = ("verified_scope", "verified_effort", "verified_acceptance_criteria")

def review_brief(brief: dict) -> dict:
    findings = []
    url = str(brief.get("url", ""))
    if not url.startswith("https://github.com/"):
        findings.append({"level": "high", "code": "UNTRUSTED_OR_MISSING_SOURCE", "detail": "Source is not a GitHub issue URL."})
    for field in REQUIRED_FALSE:
        if brief.get(field) is not False:
            findings.append({"level": "high", "code": "VERIFICATION_STATE_INVALID", "detail": f"{field} must remain false until a human verifies it."})
    if not brief.get("do_not") or not isinstance(brief.get("do_not"), list):
        findings.append({"level": "high", "code": "MISSING_ACTION_BOUNDARY", "detail": "Required prohibited-action list is missing."})
    if brief.get("triage_score", 0) > 5 or brief.get("triage_score", 0) < 0:
        findings.append({"level": "medium", "code": "SCORE_OUT_OF_RANGE", "detail": "Heuristic score is outside the expected 0-5 range."})
    if not findings:
        findings.append({"level": "info", "code": "STRUCTURE_CHECK_PASSED", "detail": "Required safety fields and source format are present; opportunity legitimacy is still unverified."})
    return {"title": brief.get("title", "Untitled"), "url": url, "findings": findings,
            "status": "blocked" if any(x["level"] == "high" for x in findings) else "review_required"}

def review_report(payload: dict) -> dict:
    briefs = payload.get("briefs", [])
    if not isinstance(briefs, list):
        raise ValueError("Input 'briefs' must be a list")
    results = [review_brief(x) for x in briefs if isinstance(x, dict)]
    blocked = sum(x["status"] == "blocked" for x in results)
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "reviewed_count": len(results),
        "blocked_count": blocked,
        "results": results,
        "overall_status": "blocked" if blocked else "human_review_required",
        "disclaimer": "Structural safety checks only. This does not verify the sponsor, funding, eligibility, code safety or payout.",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="development-output/engineering-triage.json")
    parser.add_argument("--output-dir", default="risk-output")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = review_report(payload)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "risk-review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Risk Review", "", f"Overall status: **{report['overall_status']}**", "",
             "Structural checks only; all opportunities still require human verification.", ""]
    for result in report["results"]:
        lines.extend([f"## {result['status']}: {result['title']}", f"Source: {result['url']}"])
        lines.extend([f"- {f['level'].upper()} — {f['code']}: {f['detail']}" for f in result["findings"]])
        lines.append("")
    (output / "risk-review.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Risk review complete: {report['reviewed_count']} items; {report['blocked_count']} blocked.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
