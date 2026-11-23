"""Aevora offline commercial pipeline: deterministic review queue, no outreach."""
from __future__ import annotations

from dataclasses import dataclass
from revenue_intake_sandbox import Opportunity, qualify
from revenue_delivery_plan import plan_delivery

@dataclass(frozen=True)
class PipelineRow:
    reference: str
    service: str
    expected_revenue_cad: int
    status: str
    blockers: tuple[str, ...]
    planned_tasks: tuple[str, ...]
    external_contact_authorized: bool = False
    agent_execution_authorized: bool = False
    spending_authorized: bool = False

@dataclass(frozen=True)
class PipelineBoard:
    rows: tuple[PipelineRow, ...]
    review_ready_count: int
    held_count: int
    rejected_count: int
    estimated_review_ready_cad: int
    booked_revenue_cad: int = 0
    realized_revenue_cad: int = 0

def build_board(opportunities: tuple[Opportunity, ...]) -> PipelineBoard:
    if not isinstance(opportunities, tuple):
        raise TypeError("tuple of opportunities required")
    seen: set[str] = set()
    rows: list[PipelineRow] = []
    for opportunity in opportunities:
        decision = qualify(opportunity)
        if decision.reference in seen:
            raise ValueError("duplicate opportunity reference")
        seen.add(decision.reference)
        plan = plan_delivery(opportunity)
        rows.append(PipelineRow(
            reference=decision.reference,
            service=opportunity.kind,
            expected_revenue_cad=opportunity.expected_revenue_cad
            if type(opportunity.expected_revenue_cad) is int and opportunity.expected_revenue_cad >= 0 else 0,
            status=decision.status,
            blockers=decision.reasons,
            planned_tasks=plan.tasks,
        ))
    rows.sort(key=lambda row: ({"REVIEW_READY": 0, "HOLD": 1, "REJECT": 2}[row.status],
                               -row.expected_revenue_cad, row.reference))
    return PipelineBoard(
        rows=tuple(rows),
        review_ready_count=sum(row.status == "REVIEW_READY" for row in rows),
        held_count=sum(row.status == "HOLD" for row in rows),
        rejected_count=sum(row.status == "REJECT" for row in rows),
        estimated_review_ready_cad=sum(row.expected_revenue_cad for row in rows if row.status == "REVIEW_READY"),
    )
