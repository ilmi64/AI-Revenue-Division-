"""Offline, synthetic-only Mini-Review effort and QA evidence calculations.

No I/O, network, customer data, pricing, or authorization side effects.
This module does not conduct or approve a rehearsal.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class EffortEntry:
    exercise_id: str
    contributor: str
    stage: str
    active_minutes: Decimal
    rework: bool = False


@dataclass(frozen=True)
class EffortSummary:
    exercise_id: str
    active_minutes: Decimal
    rework_minutes: Decimal
    rework_share: Decimal | None
    target_180_variance_minutes: Decimal
    rehearsal_210_variance_minutes: Decimal


def summarize_effort(exercise_id: str, entries: Iterable[EffortEntry]) -> EffortSummary:
    """Aggregate *recorded* active effort; do not infer elapsed time or costs.

    The 180-minute offer target and 210-minute rehearsal allocation are
    deliberately separate comparisons. Neither is a validated promise.
    """
    if not isinstance(exercise_id, str) or not exercise_id.strip():
        raise ValueError("exercise_id is required")
    rows = tuple(entries)
    if not rows:
        raise ValueError("at least one contemporaneously recorded entry is required")
    for row in rows:
        if not isinstance(row, EffortEntry):
            raise ValueError("each entry must be an EffortEntry")
        if row.exercise_id != exercise_id:
            raise ValueError("mixed exercise IDs")
        if (
            not isinstance(row.contributor, str) or not row.contributor.strip()
            or not isinstance(row.stage, str) or not row.stage.strip()
        ):
            raise ValueError("contributor and stage are required")
        if not isinstance(row.rework, bool):
            raise ValueError("rework must be boolean")
        if (
            not isinstance(row.active_minutes, Decimal)
            or not row.active_minutes.is_finite()
            or row.active_minutes < 0
        ):
            raise ValueError("active minutes must be finite and nonnegative")
    active = sum((r.active_minutes for r in rows), Decimal(0))
    rework = sum((r.active_minutes for r in rows if r.rework), Decimal(0))
    return EffortSummary(
        exercise_id=exercise_id,
        active_minutes=active,
        rework_minutes=rework,
        rework_share=rework / active if active else None,
        target_180_variance_minutes=active - Decimal(180),
        rehearsal_210_variance_minutes=active - Decimal(210),
    )


# Match the criteria in the Delivery QA, Acceptance & Time-Capture Standard.
QA_CRITERIA = (
    "scope_conformity",
    "source_traceability",
    "calculation_integrity",
    "baseline_integrity",
    "recommendation_quality",
    "privacy_data_minimization",
    "security_and_rights",
    "halal_or_regulated_issue_flags",
    "limitations_and_uncertainty",
    "readability_and_actionability",
    "recipient_and_version_control",
    "commercial_honesty",
)
_NON_WAIVABLE_CRITERIA = (
    "scope_conformity",
    "source_traceability",
    "calculation_integrity",
    "privacy_data_minimization",
    "security_and_rights",
    "recipient_and_version_control",
    "commercial_honesty",
)


@dataclass(frozen=True)
class QACriterionEvidence:
    criterion: str
    disposition: str
    evidence_ref: str = ""
    rationale: str = ""


@dataclass(frozen=True)
class QAEvidenceSummary:
    exercise_id: str
    draft_ref: str
    reviewer_id: str
    blockers: tuple[str, ...]


def summarize_qa_evidence(
    exercise_id: str,
    *,
    draft_ref: str,
    producer_id: str,
    reviewer_id: str,
    evidence_class: str,
    criteria: Iterable[QACriterionEvidence],
    unresolved_critical_defects: int,
    unresolved_major_defects: int,
) -> QAEvidenceSummary:
    """Summarize blockers from a recorded synthetic review of one draft.

    Evidence references are recorded identifiers. An empty blocker list
    makes no claim about evidence authenticity, review authorization,
    customer readiness, or release.
    """
    if evidence_class != "SYNTHETIC":
        raise ValueError("only synthetic QA evidence is supported")
    for name, value in (
        ("exercise_id", exercise_id),
        ("draft_ref", draft_ref),
        ("producer_id", producer_id),
        ("reviewer_id", reviewer_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")

    blockers = []
    if producer_id.strip().casefold() == reviewer_id.strip().casefold():
        blockers.append("reviewer_matches_producer")
    for severity, count in (
        ("critical", unresolved_critical_defects),
        ("major", unresolved_major_defects),
    ):
        if type(count) is not int or count < 0:
            raise ValueError(f"unresolved {severity} defects must be a nonnegative integer")
        if count:
            blockers.append(f"unresolved_{severity}_defects")

    by_criterion = {}
    for result in criteria:
        if not isinstance(result, QACriterionEvidence) or result.criterion not in QA_CRITERIA:
            raise ValueError("unknown QA criterion or invalid record")
        if result.criterion in by_criterion:
            raise ValueError(f"duplicate QA criterion: {result.criterion}")
        if result.disposition not in ("PASS", "FAIL", "NOT_APPLICABLE", "BLOCKED"):
            raise ValueError(f"invalid QA disposition: {result.criterion}")
        if not isinstance(result.evidence_ref, str) or not isinstance(result.rationale, str):
            raise ValueError(f"invalid QA evidence reference or rationale: {result.criterion}")
        by_criterion[result.criterion] = result

    for criterion in QA_CRITERIA:
        result = by_criterion.get(criterion)
        if result is None:
            blockers.append(f"missing:{criterion}")
        elif result.disposition in ("FAIL", "BLOCKED"):
            blockers.append(f"{result.disposition.lower()}:{criterion}")
        elif result.disposition == "PASS" and not result.evidence_ref.strip():
            blockers.append(f"missing_evidence:{criterion}")
        elif result.disposition == "NOT_APPLICABLE":
            if criterion in _NON_WAIVABLE_CRITERIA:
                blockers.append(f"required:{criterion}")
            elif not result.rationale.strip():
                blockers.append(f"missing_rationale:{criterion}")

    return QAEvidenceSummary(exercise_id, draft_ref, reviewer_id, tuple(blockers))
