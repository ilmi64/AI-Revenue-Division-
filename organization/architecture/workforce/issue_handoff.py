"""Pure offline validator for issue-based engineering handoffs.

A validated handoff is a task description, NEVER execution or launch authorization.
No network, GitHub API, Codex API, polling or side effects.
"""
from dataclasses import dataclass
from enum import Enum
import re
from urllib.parse import urlparse


class Company(str, Enum):
    AI_REVENUE = "AI_REVENUE"
    TRADING_TECHNOLOGY = "TRADING_TECHNOLOGY"


class TestStatus(str, Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    BLOCKED = "BLOCKED"
    PASS = "PASS"


REPOS = {
    Company.AI_REVENUE: "ilmi64/AI-Revenue-Division-",
    Company.TRADING_TECHNOLOGY: "ilmi64/Solana-memecoins",
}
SAFE_OPERATIONS = frozenset({"READ_SOURCE", "EDIT_TASK_BRANCH", "OFFLINE_SYNTHETIC_TEST", "COMMIT_TASK_BRANCH", "REPORT_EVIDENCE"})
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
BRANCH_PATTERN = re.compile(r"(?:implementation|codex|docs)/[A-Za-z0-9._/-]+\Z")


@dataclass(frozen=True)
class Handoff:
    company: Company
    issue_url: str
    issue_number: int
    source_sha: str
    task_branch: str
    allowed_operations: frozenset[str]
    test_status: TestStatus
    evidence_refs: tuple[str, ...]
    human_approval_required: bool = True


def handoff_blockers(item: object) -> tuple[str, ...]:
    """Fail closed on malformed task records and cross-company issue links."""
    if not isinstance(item, Handoff):
        return ("invalid_handoff",)
    blockers = []
    if not isinstance(item.company, Company):
        blockers.append("invalid_company")
    if type(item.issue_number) is not int or item.issue_number < 1:
        blockers.append("invalid_issue_number")
    parsed = urlparse(item.issue_url) if isinstance(item.issue_url, str) else None
    expected = REPOS.get(item.company) if isinstance(item.company, Company) else None
    if (
        parsed is None or parsed.scheme != "https" or parsed.netloc != "github.com"
        or expected is None or parsed.path != f"/{expected}/issues/{item.issue_number}"
        or parsed.params or parsed.query or parsed.fragment
    ):
        blockers.append("issue_scope_mismatch")
    if not isinstance(item.source_sha, str) or SHA_PATTERN.fullmatch(item.source_sha) is None:
        blockers.append("invalid_source_pin")
    if (
        not isinstance(item.task_branch, str)
        or BRANCH_PATTERN.fullmatch(item.task_branch) is None
        or ".." in item.task_branch or "//" in item.task_branch
        or item.task_branch.endswith(("/", "."))
    ):
        blockers.append("invalid_task_branch")
    if (
        not isinstance(item.allowed_operations, frozenset)
        or not item.allowed_operations
        or any(type(op) is not str for op in item.allowed_operations)
        or not item.allowed_operations <= SAFE_OPERATIONS
    ):
        blockers.append("unauthorized_operations")
    if not isinstance(item.test_status, TestStatus):
        blockers.append("invalid_test_status")
    if (
        not isinstance(item.evidence_refs, tuple)
        or any(not isinstance(ref, str) or not ref.strip() for ref in item.evidence_refs)
    ):
        blockers.append("invalid_evidence_refs")
    if item.human_approval_required is not True:
        blockers.append("human_approval_missing")
    return tuple(blockers)
