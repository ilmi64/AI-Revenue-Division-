"""Run Aevora AI's fixed, fictional listing-preflight workflow offline."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from anchored_delivery_rehearsal import _verify_anchored_fixture
from evidence_verifier import VerificationBlocked
from occ_summary import summarize
from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import plan_delivery
from revenue_intake_sandbox import Opportunity, qualify
from revenue_proposal_draft import draft_proposal
from revenue_task_evidence import TaskEvidence, review_evidence
from synthetic_delivery_rehearsal import _sha


SCENARIOS = ("baseline", "missing_scope", "paid_dependency", "missing_anchor")
_SOURCE = b"""sku,title,price,quantity,shipping
FIX-001,Fictional notebook,12.00,3,2.00
FIX-001,Fictional duplicate,15.00,2.5,2.00
"""
_FIXTURE = Opportunity(
    reference="synthetic_catalogue_preflight",
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
    "product": ("fixture-product-planner", "Technology & Infrastructure"),
    "engineering": ("fixture-engineering-builder", "Technology & Infrastructure"),
    "quality": ("fixture-risk-reviewer", "Risk & Recovery"),
}
_LISTING_PREFLIGHT = (
    Path(__file__).resolve().parents[1] / "portfolio" / "listing-preflight" / "listing_preflight.py"
)


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _listing_fixture_report() -> tuple[dict, bytes]:
    """Exercise the existing read-only CLI on two invented catalogue rows."""
    try:
        validator_sha256 = _sha(_LISTING_PREFLIGHT.read_bytes())
        with TemporaryDirectory() as directory:
            fixture = Path(directory) / "synthetic-listings.csv"
            fixture.write_bytes(_SOURCE)
            run = subprocess.run(
                [sys.executable, str(_LISTING_PREFLIGHT), str(fixture), "--json"],
                capture_output=True, timeout=10, check=False,
            )
        result = json.loads(run.stdout)
        if not isinstance(result, dict) or not isinstance(result["findings"], list):
            raise VerificationBlocked("offline_preflight_report_invalid")
        findings = [(finding["row"], finding["field"], finding["severity"])
                    for finding in result["findings"]]
        if (
            run.returncode != 1 or run.stderr or result["valid"] is not False
            or result["file"] != "synthetic-listings.csv" or result["finding_count"] != 2
            or findings != [(3, "sku", "error"), (3, "quantity", "error")]
        ):
            raise VerificationBlocked("offline_preflight_known_answer_failed")
    except (OSError, subprocess.TimeoutExpired, TypeError, KeyError, ValueError) as exc:
        if isinstance(exc, VerificationBlocked):
            raise
        raise VerificationBlocked("offline_preflight_evidence_unavailable") from exc
    return result, _canonical({
        "classification": "SYNTHETIC",
        "command": "python listing_preflight.py synthetic-listings.csv --json",
        "observed_exit_code": run.returncode,
        "validator_sha256": validator_sha256,
        "stdout_sha256": _sha(run.stdout),
        "passed_checks": ["duplicate_sku_on_row_3", "fractional_quantity_on_row_3", "two_findings"],
    })


def _assignment(task) -> dict:
    agent, division = _CHARTER_BY_ROLE[task.role]
    return {
        **asdict(task),
        "proposed_owner": agent,
        "charter_division": division,
        "source_fixture": "synthetic-listings.csv",
        "tools_scope": "local_read_only_preflight",
        "verification": "check_against_fixed_fixture",
        "human_review_required": True,
    }


def run_demo(*, mode: str, scenario: str = "baseline") -> dict:
    """Prepare private review evidence from a fixed fixture with no dispatch."""
    if mode != "anchored":
        raise ValueError("explicit anchored mode required")
    if scenario not in SCENARIOS:
        raise ValueError("unknown demo scenario")
    changes = {
        "missing_scope": {"authorization_evidence": False},
        "paid_dependency": {"upfront_cost_cad": 1},
    }
    item = replace(_FIXTURE, **changes.get(scenario, {}))
    intake = qualify(item)
    report = {
        "company": "Aevora AI",
        "classification": "SYNTHETIC_INTERNAL_ONLY",
        "scenario": scenario,
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

    plan = plan_delivery(item)
    queue = prepare_queue(plan)
    proposal = draft_proposal(item)
    public_status = "blocked"
    try:
        build_tasks = [task for task in queue if task.task == "build_offline_demo"]
        if len(queue) != 4 or len(build_tasks) != 1 or proposal.status != "INTERNAL_DRAFT":
            raise VerificationBlocked("offline_plan_or_proposal_blocked")
        preflight, log = _listing_fixture_report()
        artifact = _canonical({
            "classification": report["classification"],
            "reference": item.reference,
            "synthetic_source_sha256": _sha(_SOURCE),
            "intake": asdict(intake),
            "delivery_plan": asdict(plan),
            "assignments": [_assignment(task) for task in queue],
            "proposal": {**asdict(proposal), "markdown": "SYNTHETIC INTERNAL DRAFT\n\n" + proposal.markdown},
            "deliverable": preflight,
        })
        events = report["private_audit"]
        artifact_digest = _sha(artifact)
        report["private_artifact"] = {"contents": json.loads(artifact), "sha256": artifact_digest}
        build_task = build_tasks[0]
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
        report["private_test_log"] = {**json.loads(log), "task_evidence_review": asdict(review)}
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
    report["occ"] = summarize([{"status": public_status}])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("anchored",))
    parser.add_argument("--scenario", choices=SCENARIOS, default="baseline")
    parser.add_argument("--view", choices=("private", "occ"), default="private")
    args = parser.parse_args()
    report = run_demo(mode=args.mode, scenario=args.scenario)
    print(json.dumps(report if args.view == "private" else report["occ"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
