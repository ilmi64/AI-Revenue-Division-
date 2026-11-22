"""Fail-closed, offline issue gate and dispatcher decision model.

No Codex Cloud API invocation is implemented or authorized here.
"""
from dataclasses import dataclass
from enum import Enum
import re
from typing import Mapping


class DispatchState(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_MANUAL_START = "READY_FOR_MANUAL_START"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class GateResult:
    state: DispatchState
    blockers: tuple[str, ...]
    manual_instruction: str = ""


def validate_issue_payload(payload: object, expected_repo: str) -> tuple[str, ...]:
    """Require explicit task scope, acceptance, stop conditions and source pin."""
    if not isinstance(payload, Mapping):
        return ("invalid_issue_payload",)
    body = payload.get("body")
    number = payload.get("number")
    title = payload.get("title")
    blockers = []
    if not isinstance(body, str) or not body.strip():
        return ("missing_body",)
    if type(number) is not int or number < 1:
        blockers.append("invalid_issue_number")
    if not isinstance(title, str) or not title.strip():
        blockers.append("missing_title")
    if expected_repo not in ("ilmi64/AI-Revenue-Division-", "ilmi64/Solana-memecoins"):
        blockers.append("unknown_repository")
    if not re.search(r"(?im)^## (?:Acceptance(?: criteria)?|Completion)\s*$", body):
        blockers.append("missing_acceptance_section")
    if not re.search(r"(?im)^## (?:Authorized implementation|Bounded task|Bounded implementation)\s*$", body):
        blockers.append("missing_implementation_section")
    if not re.search(r"(?im)^## (?:Source of truth|Starting points|Context)\s*$", body):
        blockers.append("missing_source_section")
    if not re.search(r"`(?:organization/|src/|tests/)[^\n`]+`", body):
        blockers.append("missing_scoped_module_targets")
    if not re.search(r"\b[0-9a-f]{40}\b", body):
        blockers.append("missing_immutable_source_sha")
    if not re.search(r"(?i)\b(?:stop|do not auto-start|no automatic|human review|human approval|explicit approval)\b", body):
        blockers.append("missing_stop_or_escalation")
    if not re.search(r"(?i)\b(?:test commands|test command|tests actually executed|actual test evidence|offline tests)\b", body):
        blockers.append("missing_test_evidence_requirement")
    return tuple(blockers)


def plan_dispatch(issue: object, repo: str, *, explicit_approval: bool,
                  supported_cloud_launcher: bool = False) -> GateResult:
    """Never mark a cloud run started without an approved, supported launcher."""
    blockers = list(validate_issue_payload(issue, repo))
    if explicit_approval is not True:
        blockers.append("explicit_approval_required")
    if blockers:
        return GateResult(DispatchState.BLOCKED, tuple(blockers))
    number = issue["number"]
    instruction = (
        f"Read GitHub Issue #{number} in {repo}; follow AGENTS.md and the "
        "pinned source SHA. Run only authorized offline synthetic checks, "
        "commit to a dedicated branch, report exact results, then stop."
    )
    # A supported launcher must be separately integrated, authenticated and tested.
    # Merely setting supported_cloud_launcher=True does not start a run.
    return GateResult(DispatchState.READY_FOR_MANUAL_START, (), instruction)
