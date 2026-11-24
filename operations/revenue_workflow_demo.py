"""Run one allowlisted Aevora AI fictional workforce workflow offline."""
import argparse
from dataclasses import asdict, replace
import json

from anchored_delivery_rehearsal import _verify_anchored_fixture
from evidence_verifier import VerificationBlocked
from occ_summary import summarize
from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import plan_delivery
from revenue_fixture_dispatch import PROFILES, canonical as _canonical, dispatch_fixture, fixture_ticket
from revenue_intake_sandbox import Opportunity, qualify
from revenue_proposal_draft import draft_proposal
from revenue_task_evidence import TaskEvidence, review_evidence
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
    }
    if intake.status != "REVIEW_READY":
        report["occ"] = summarize([{"status": {"HOLD": "hold", "REJECT": "rejected"}[intake.status]}])
        return report

    public_status = "blocked"
    try:
        plan = plan_delivery(item)
        queue = prepare_queue(plan)
        proposal = draft_proposal(item)
        build_tasks = [task for task in queue if task.task == profile.task]
        if len(queue) != 4 or len(build_tasks) != 1 or proposal.status != "INTERNAL_DRAFT":
            raise VerificationBlocked("offline_plan_or_proposal_blocked")
        build_task = build_tasks[0]
        outcome, log, source_digest = dispatch_fixture(fixture_ticket(service, build_task), build_task)
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
        review = review_evidence(build_task, TaskEvidence(
            task_id=build_task.task_id,
            artifact_sha256=artifact_digest,
            artifact_bytes=artifact,
            author_role=build_task.role,
            reviewer_role="quality",
            reviewer_attested=True,
        ))
        report["private_task_review"] = asdict(review)
        if review.task_id != build_task.task_id or review.status != "EVIDENCE_REVIEWED":
            raise VerificationBlocked("offline_task_evidence_review_blocked")
        report["private_test_log"] = {**log, "task_evidence_review": asdict(review)}
        log = _canonical(report["private_test_log"])
        events.append({"stage": "known_answer_checked", "artifact_sha256": artifact_digest,
                       "test_log_sha256": _sha(log)})
        anchored_scenario = "missing_anchor" if scenario == "missing_anchor" else "baseline"
        receipt = _verify_anchored_fixture(
            anchored_scenario, artifact, log, events,
            opportunity_id=item.reference, producer_id="fixture-engineering-builder",
        )
        if receipt["release_authorized"] is not False:
            raise VerificationBlocked("offline_receipt_grants_release")
        report["receipt"] = receipt
        public_status = "checklist_complete_unverified"
    except VerificationBlocked as exc:
        report["private_audit"].append({"stage": "evidence_review_blocked", "reason": str(exc)})
    except (TypeError, ValueError):
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
