"""Offline delivery workflow. No execution, network, billing or submission.

Input: local JSON object with `opportunity`, `evidence`, `approvals`.
Outputs an unverified checklist decision only; does not change any external system.
"""
import argparse
import json
from pathlib import Path
from opportunity_intake import assess

STAGES = ("intake", "assignment", "qa", "delivery")
def decide(record):
    if not isinstance(record, dict):
        return {"status": "blocked", "reasons": ["invalid_record"]}
    opportunity = record.get("opportunity")
    intake = assess(opportunity)
    reasons = list(intake.get("reasons", []))
    if intake["status"] != "review_ready":
        reasons.append("intake_not_review_ready")
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    approvals = record.get("approvals")
    if not isinstance(approvals, dict):
        approvals = {}
    if not isinstance(evidence.get("task_owner"), str) or not evidence["task_owner"].strip():
        reasons.append("missing_task_owner")
    if not isinstance(evidence.get("source_commit"), str) or len(evidence["source_commit"]) != 40 or any(c not in "0123456789abcdefABCDEF" for c in evidence["source_commit"]):
        reasons.append("invalid_source_commit")
    if evidence.get("tests_passed") is not True:
        reasons.append("qa_not_passed")
    if not isinstance(evidence.get("test_command"), str) or not evidence["test_command"].strip():
        reasons.append("missing_test_command")
    if not isinstance(evidence.get("test_log_ref"), str) or not evidence["test_log_ref"].strip():
        reasons.append("missing_test_evidence")
    if approvals.get("delivery_authorized") is not True:
        reasons.append("delivery_not_authorized")
    if approvals.get("scope_reviewed") is not True:
        reasons.append("scope_not_reviewed")
    return {
        "opportunity_id": opportunity.get("id") if isinstance(opportunity, dict) else None,
        "status": "checklist_complete_unverified" if not reasons else "blocked",
        "reasons": sorted(set(reasons)),
        "next_action": "independent_evidence_and_owner_review_required" if not reasons else "resolve_blockers",
        "evidence_verified": False,
        "release_authorized": False,
        "external_actions_performed": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    decision = decide(json.loads(args.input.read_text(encoding="utf-8")))
    report = json.dumps(decision, indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)

if __name__ == "__main__":
    main()
