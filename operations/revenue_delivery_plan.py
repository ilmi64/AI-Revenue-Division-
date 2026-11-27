"""Offline Aevora service delivery planning. No agent execution or outreach."""
from __future__ import annotations

from dataclasses import dataclass

from revenue_intake_sandbox import Opportunity, qualify

TASKS = {
    "coding": ("reproduce_issue_in_sandbox", "draft_patch", "run_tests", "prepare_review"),
    "authorized_bug_bounty": ("verify_program_scope", "review_rules", "research_passively", "prepare_private_review"),
    "app_build": ("confirm_requirements", "design_prototype", "build_offline_demo", "run_acceptance_tests"),
    "ai_setup": ("map_workflow", "design_agent_permissions", "simulate_agent_tasks", "review_data_handling"),
    "research": ("define_question", "collect_permitted_sources", "cross_check_claims", "draft_cited_report"),
}


@dataclass(frozen=True)
class DeliveryPlan:
    reference: str
    classification: str
    tasks: tuple[str, ...]
    human_review_required: bool = True
    customer_contact_authorized: bool = False
    external_submission_authorized: bool = False
    agent_execution_authorized: bool = False
    spending_authorized: bool = False


def plan_delivery(opportunity: Opportunity) -> DeliveryPlan:
    decision = qualify(opportunity)
    if decision.status != "REVIEW_READY":
        return DeliveryPlan(decision.reference, decision.status, ())
    return DeliveryPlan(decision.reference, "INTERNAL_PLAN_ONLY", TASKS[opportunity.kind])
