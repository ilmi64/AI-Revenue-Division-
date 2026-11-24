"""Run one allowlisted Aevora AI fictional workforce workflow offline."""
import argparse
from dataclasses import asdict, replace
import json

from evidence_verifier import VerificationBlocked
from occ_summary import summarize
from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import plan_delivery
from revenue_fixture_dispatch import PROFILES, canonical as _canonical, fixture_ticket
from revenue_intake_sandbox import Opportunity, qualify
from revenue_proposal_draft import draft_proposal
from revenue_runtime_mediation import FixtureDelegation, FixtureMediation
from synthetic_delivery_rehearsal import _sha


SCENARIOS = ("baseline", "missing_scope", "paid_dependency", "missing_anchor")
_FIXTURE = Opportunity(
    reference=PROFILES["app_build"].reference,
    kind="app_build",
    country="CA",
    expected_revenue_cad=300,
    upfront_cost_cad=0,
    authorization_evidence=True,
    payout_confirmed=True,
    sanctions_reviewed=True,
    customer_contact_allowed=True,
)
_CHARTER_BY_ROLE = {
    "product": ("fixture-product-planner", "Technology & Infrastructure", "ar_product_delivery"),
    "engineering": ("fixture-engineering-builder", "Technology & Infrastructure", "ar_engineering_worker"),
    "quality": ("fixture-risk-reviewer", "Risk & Recovery", "ar_qa_reviewer"),
    "security": ("fixture-security-reviewer", "Risk & Recovery", "ar_security_analyst"),
}


def _assignment(task, profile) -> dict:
    agent, division, role_id = _CHARTER_BY_ROLE[task.role]
    return {
        **asdict(task),
        "proposed_owner": agent,
        "charter_division": division,
        "role_id": role_id,
        "source_fixture": profile.fixture_id,
        "tools_scope": "local_read_only_fixture",
        "verification": "check_against_fixed_fixture",
        "human_review_required": True,
    }


def run_demo(*, mode: str, scenario: str = "baseline", service: str = "app_build") -> dict:
    """Prepare private evidence by running one fixed synthetic fixture worker."""
    if mode != "anchored":
        raise ValueError("explicit anchored mode required")
    if scenario not in SCENARIOS:
        raise ValueError("unknown demo scenario")
    if not isinstance(service, str) or service not in PROFILES:
        raise ValueError("service must select an allowlisted fixture")
    profile = PROFILES[service]
    changes = {
        "missing_scope": {"authorization_evidence": False},
        "paid_dependency": {"upfront_cost_cad": 1},
    }
    item = replace(_FIXTURE, reference=profile.reference, kind=service, country=profile.country,
                   **changes.get(scenario, {}))
    intake = qualify(item)
    report = {
        "company": "Aevora AI",
        "classification": "SYNTHETIC_INTERNAL_ONLY",
        "scenario": scenario,
        "service": service,
        "fixture_country": profile.country,
        "intake": asdict(intake),
        "private_artifact": None,
        "private_audit": [],
        "receipt": None,
        "release_authorized": False,
        "external_actions_performed": False,
        "agent_execution_authorized": False,
        "customer_contact_authorized": False,
        "spending_authorized": False,
        "private_runtime": {
            "state": "NOT_DELEGATED",
            "commissioning": {
                "status": "HOLD",
                "blockers": [
                    "native_runtime_unverified", "production_custody_unverified",
                    "operational_independent_review_pending", "owner_signoff_pending",
                ],
            },
            "supervisor_escalation": None,
        },
    }
    if intake.status != "REVIEW_READY":
        report["occ"] = summarize([{"status": {"HOLD": "hold", "REJECT": "rejected"}[intake.status]}])
        return report

    public_status = "blocked"
    mediation = None
    try:
        plan = plan_delivery(item)
        queue = prepare_queue(plan)
        proposal = draft_proposal(item)
        build_tasks = [task for task in queue if task.task == profile.task]
        if len(queue) != 4 or len(build_tasks) != 1 or proposal.status != "INTERNAL_DRAFT":
            raise VerificationBlocked("offline_plan_or_proposal_blocked")
        build_task = build_tasks[0]
        mediation = FixtureMediation(FixtureDelegation(fixture_ticket(service, build_task)), build_task)
        report["private_audit"] = mediation.events
        outcome, source_digest = mediation.run_worker()
        artifact = _canonical({
            "classification": report["classification"],
            "reference": item.reference,
            "synthetic_source_sha256": source_digest,
            "intake": asdict(intake),
            "delivery_plan": asdict(plan),
            "assignments": [_assignment(task, profile) for task in queue],
            "proposal": {**asdict(proposal), "markdown": "SYNTHETIC INTERNAL DRAFT\n\n" + proposal.markdown},
            "deliverable": outcome,
        })
        events = report["private_audit"]
        artifact_digest = _sha(artifact)
        report["private_artifact"] = {"contents": json.loads(artifact), "sha256": artifact_digest}
        review = mediation.review_artifact(artifact)
        report["private_task_review"] = asdict(review)
        if review.task_id != build_task.task_id or review.status != "EVIDENCE_REVIEWED":
            raise VerificationBlocked("offline_task_evidence_review_blocked")
        report["private_test_log"] = mediation.test_log
        events.append({"stage": "known_answer_checked", "artifact_sha256": artifact_digest,
                       "test_log_sha256": _sha(_canonical(report["private_test_log"]))})
        receipt = mediation.anchor(anchor_available=scenario != "missing_anchor")
        report["private_runtime"]["state"] = "REVIEW_READY"
        report["receipt"] = receipt
        public_status = "checklist_complete_unverified"
    except VerificationBlocked as exc:
        report["private_runtime"]["state"] = "HOLD"
        if mediation is not None:
            report["private_runtime"]["supervisor_escalation"] = mediation.escalate(str(exc))
        report["private_audit"].append({"stage": "evidence_review_blocked", "reason": str(exc)})
    except (TypeError, ValueError):
        report["private_runtime"]["state"] = "HOLD"
        if mediation is not None:
            report["private_runtime"]["supervisor_escalation"] = mediation.escalate("offline_plan_or_evidence_invalid")
        report["private_audit"].append({"stage": "evidence_review_blocked", "reason": "offline_plan_or_evidence_invalid"})
    report["occ"] = summarize([{"status": public_status}])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("anchored",))
    parser.add_argument("--service", choices=tuple(PROFILES), default="app_build")
    parser.add_argument("--scenario", choices=SCENARIOS, default="baseline")
    parser.add_argument("--view", choices=("private", "occ"), default="private")
    args = parser.parse_args()
    report = run_demo(mode=args.mode, scenario=args.scenario, service=args.service)
    print(json.dumps(report if args.view == "private" else report["occ"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
