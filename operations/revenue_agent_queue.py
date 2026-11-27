"""Aevora offline work-queue projection. No dispatch, network, or agent invocation."""
from __future__ import annotations

from dataclasses import dataclass

from revenue_delivery_plan import DeliveryPlan

ROLES = {
    "reproduce_issue_in_sandbox": "engineering",
    "draft_patch": "engineering",
    "run_tests": "quality",
    "prepare_review": "quality",
    "verify_program_scope": "compliance",
    "review_rules": "compliance",
    "research_passively": "research",
    "prepare_private_review": "quality",
    "confirm_requirements": "product",
    "design_prototype": "product",
    "build_offline_demo": "engineering",
    "run_acceptance_tests": "quality",
    "map_workflow": "product",
    "design_agent_permissions": "security",
    "simulate_agent_tasks": "engineering",
    "review_data_handling": "security",
    "define_question": "research",
    "collect_permitted_sources": "research",
    "cross_check_claims": "quality",
    "draft_cited_report": "research",
}


@dataclass(frozen=True)
class QueueItem:
    task_id: str
    opportunity_reference: str
    sequence: int
    task: str
    role: str
    state: str = "AWAITING_INTERNAL_REVIEW"
    execution_authorized: bool = False
    external_delivery_authorized: bool = False
    spending_authorized: bool = False


def prepare_queue(plan: DeliveryPlan) -> tuple[QueueItem, ...]:
    if not isinstance(plan, DeliveryPlan):
        raise TypeError("DeliveryPlan required")
    if plan.classification != "INTERNAL_PLAN_ONLY" or not plan.human_review_required:
        return ()
    if (plan.agent_execution_authorized or plan.customer_contact_authorized
            or plan.external_submission_authorized or plan.spending_authorized):
        raise ValueError("elevated permissions forbidden in offline queue")
    if (not isinstance(plan.reference, str) or not plan.reference
            or len(plan.reference) > 80 or not plan.reference.isascii()
            or not all(c.isalnum() or c in "-_" for c in plan.reference)):
        raise ValueError("invalid reference")
    if not isinstance(plan.tasks, tuple) or len(plan.tasks) != 4:
        raise ValueError("invalid task plan")
    if any(not isinstance(task, str) or task not in ROLES for task in plan.tasks):
        raise ValueError("unrecognized task")
    return tuple(QueueItem(f"{plan.reference}:{i:02d}", plan.reference, i, task, ROLES[task])
                 for i, task in enumerate(plan.tasks, start=1))
