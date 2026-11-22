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
