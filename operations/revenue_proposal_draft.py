"""Deterministic internal-only service proposal drafts; never customer-ready by default."""
from __future__ import annotations
from dataclasses import dataclass
from revenue_intake_sandbox import Opportunity, qualify
from revenue_delivery_plan import plan_delivery

SERVICE_NAMES = {
    "coding": "Software bug fixing and code review",
    "authorized_bug_bounty": "Authorized security research",
    "app_build": "Application prototype and implementation",
    "ai_setup": "AI workflow and agent setup",
    "research": "Research and evidence reporting",
}

@dataclass(frozen=True)
class ProposalDraft:
    reference: str
    status: str
    markdown: str
    blockers: tuple[str, ...]
    client_contact_authorized: bool = False
    submission_authorized: bool = False
    agent_execution_authorized: bool = False
    spending_authorized: bool = False

def draft_proposal(item: Opportunity) -> ProposalDraft:
    decision = qualify(item)
    if decision.status != "REVIEW_READY":
        return ProposalDraft(decision.reference, "HOLD", "", decision.reasons)
    plan = plan_delivery(item)
    if plan.classification != "INTERNAL_PLAN_ONLY" or not plan.tasks:
        return ProposalDraft(decision.reference, "HOLD", "", ("delivery_plan_unavailable",))
    service = SERVICE_NAMES[item.kind]
    steps = "\n".join(f"- {task.replace('_', ' ')}" for task in plan.tasks)
    document = (
        f"# Internal proposal draft — {decision.reference}\n\n"
        f"**Service:** {service}\n\n"
        f"**Preliminary estimated opportunity value:** CAD {item.expected_revenue_cad:,}\n\n"
        "**Scope:** Subject to customer requirements, verified permissions, feasibility, "
        "security review, agreed deliverables and commercial terms.\n\n"
        f"**Proposed internal delivery workflow:**\n{steps}\n\n"
        "**Conditions:** No guarantee of acceptance, payout, security findings or results. "
        "No customer contact, external submission, agent execution or spending is approved. "
        "Independent human review and separate authorization are required before any external action.\n"
    )
    return ProposalDraft(decision.reference, "INTERNAL_DRAFT", document, ())
