"""Redacted, read-only OCC summary of offline Aevora AI decisions.

No network, credentials, customer data, or execution. Never use this report
as an authorization token; only aggregated counters cross the company boundary.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ALLOWED = {"review_ready", "hold", "rejected", "blocked", "checklist_complete_unverified"}
def summarize(decisions):
    if not isinstance(decisions, list):
        raise ValueError("decisions must be a list")
    counts = Counter()
    for item in decisions:
        if not isinstance(item, dict):
            raise ValueError("decision must be an object")
        status = item.get("status")
        if not isinstance(status, str) or status not in ALLOWED:
            raise ValueError("unsupported decision status")
        counts[status] += 1
    return {
        "organization": "Daivora Group",
        "source_company": "Aevora AI",
        "recipient": "Main Hub/OCC",
        "mode": "read_only_aggregate",
        "total": len(decisions),
        "counts": {status: counts[status] for status in sorted(ALLOWED)},
        "execution_authorized": False,
        "external_actions_performed": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = summarize(json.loads(args.input.read_text(encoding="utf-8")))
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)

if __name__ == "__main__":
    main()
