"""Finite Aevora fixture workers. The registry is closed over repository-owned code."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import MappingProxyType

from evidence_verifier import VerificationBlocked
from revenue_agent_queue import QueueItem
from revenue_delivery_plan import TASKS
from synthetic_delivery_rehearsal import _sha


@dataclass(frozen=True)
class ServiceProfile:
    reference: str
    country: str
    task: str
    fixture_id: str


PROFILES = MappingProxyType({
    "app_build": ServiceProfile("synthetic_catalogue_preflight", "CA", "build_offline_demo", "synthetic-listings.csv"),
    "coding": ServiceProfile("synthetic_invoice_rounding", "US", "draft_patch", "invoice-rounding-fixture-v1"),
    "ai_setup": ServiceProfile("synthetic_ai_review_routing", "GB", "simulate_agent_tasks", "review-routing-fixture-v1"),
})
_SOURCE = b"""sku,title,price,quantity,shipping
FIX-001,Fictional notebook,12.00,3,2.00
FIX-001,Fictional duplicate,15.00,2.5,2.00
"""
_LISTING_PREFLIGHT = (
    Path(__file__).resolve().parents[1] / "portfolio" / "listing-preflight" / "listing_preflight.py"
)
_ENGINEERING_ROLE = "ar_engineering_worker"
_ROUNDING_CHANGE = (
    "--- synthetic invoice fixture: before\n"
    "+++ synthetic invoice fixture: proposed\n"
    "-tax_cents = subtotal_cents * rate_bps // 10000\n"
    "+tax_cents = (subtotal_cents * rate_bps + 5000) // 10000\n"
)


@dataclass(frozen=True)
class FixtureTicket:
    service: str
    task_id: str
    source_fixture: str
    company_id: str = "ai_revenue"
    recipient_scope: str = "ai_revenue"
    role_id: str = _ENGINEERING_ROLE
    data_classification: str = "SYNTHETIC_FIXTURE_ONLY"
    tool_allowlist: tuple[str, ...] = ("fixed_local_fixture_worker",)
    maximum_cost_cad: int = 0


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def fixture_ticket(service: str, task: QueueItem) -> FixtureTicket:
    return FixtureTicket(service, task.task_id, PROFILES[service].fixture_id)


def _listing_fixture_report() -> tuple[dict, dict, str]:
    """Run only the repository's known read-only CLI against fixed invented rows."""
    validator_sha256 = _sha(_LISTING_PREFLIGHT.read_bytes())
    with TemporaryDirectory() as directory:
        fixture = Path(directory) / "synthetic-listings.csv"
        fixture.write_bytes(_SOURCE)
        run = subprocess.run(
            [sys.executable, str(_LISTING_PREFLIGHT), str(fixture), "--json"],
            capture_output=True, timeout=10, check=False,
        )
    result = json.loads(run.stdout)
    if run.returncode != 1 or run.stderr:
        raise VerificationBlocked("offline_preflight_known_answer_failed")
    return result, {
        "command": "python listing_preflight.py synthetic-listings.csv --json",
        "observed_exit_code": run.returncode,
        "validator_sha256": validator_sha256,
        "stdout_sha256": _sha(run.stdout),
    }, _sha(_SOURCE)


def _invoice_fixture_report() -> tuple[dict, dict, str]:
    # The fixture corrects integer-cent tax rounding from truncation to half-up.
    rows = ((1999, 2), (501, 1))
    rate_bps = 500
    subtotal = sum(price * quantity for price, quantity in rows)
    tax = (subtotal * rate_bps + 5000) // 10000
    return {
        "fixture": "invoice-rounding-fixture-v1",
        "currency": "CAD",
        "subtotal_cents": subtotal,
        "legacy_truncated_tax_cents": subtotal * rate_bps // 10000,
        "half_up_tax_cents": tax,
        "total_cents": subtotal + tax,
        "proposed_diff": _ROUNDING_CHANGE,
    }, {"algorithm": "integer_cents_half_up"}, _sha(canonical({"rows": rows, "rate_bps": rate_bps}))


def _review_routing_fixture_report() -> tuple[dict, dict, str]:
    rows = (
        {"fixture": "complete", "evidence_present": True, "external_requested": False},
        {"fixture": "missing", "evidence_present": False, "external_requested": False},
        {"fixture": "outbound", "evidence_present": True, "external_requested": True},
    )
    decisions = []
    for row in rows:
        if row["external_requested"]:
            disposition = "HOLD_EXTERNAL_ACTION"
        elif not row["evidence_present"]:
            disposition = "HOLD_MISSING_EVIDENCE"
        else:
            disposition = "QUEUE_FOR_INDEPENDENT_QA"
        decisions.append({"fixture": row["fixture"], "disposition": disposition})
    return {
        "fixture": "review-routing-fixture-v1",
        "ruleset": "deterministic_evidence_routing",
        "model_invoked": False,
        "decisions": decisions,
    }, {"algorithm": "fixed_rule_routing"}, _sha(canonical({"rows": rows}))


_WORKERS = MappingProxyType({
    "app_build": _listing_fixture_report,
    "coding": _invoice_fixture_report,
    "ai_setup": _review_routing_fixture_report,
})


def _known_answer(service: str, output: object) -> tuple[str, ...]:
    """Check fixture outcomes against constants held separately from worker logic."""
    if not isinstance(output, dict):
        raise VerificationBlocked("malformed_offline_worker_output")
    if service == "app_build":
        findings = output.get("findings")
        if not isinstance(findings, list) or any(not isinstance(finding, dict) for finding in findings):
            raise VerificationBlocked("malformed_offline_worker_output")
        if (
            set(output) == {"file", "valid", "finding_count", "findings"}
            and all(set(f) == {"row", "field", "severity", "message"} for f in findings)
            and output.get("valid") is False and output.get("file") == "synthetic-listings.csv"
            and output.get("finding_count") == 2
            and [(f.get("row"), f.get("field"), f.get("severity")) for f in findings]
            == [(3, "sku", "error"), (3, "quantity", "error")]
        ):
            return ("duplicate_sku_on_row_3", "fractional_quantity_on_row_3", "two_findings")
    elif service == "coding" and output == {
        "fixture": "invoice-rounding-fixture-v1", "currency": "CAD", "subtotal_cents": 4499,
        "legacy_truncated_tax_cents": 224, "half_up_tax_cents": 225, "total_cents": 4724,
        "proposed_diff": _ROUNDING_CHANGE,
    }:
        return ("subtotal_4499", "legacy_truncation_224", "corrected_tax_225", "total_4724")
    elif service == "ai_setup" and output == {
        "fixture": "review-routing-fixture-v1", "ruleset": "deterministic_evidence_routing", "model_invoked": False,
        "decisions": [
            {"fixture": "complete", "disposition": "QUEUE_FOR_INDEPENDENT_QA"},
            {"fixture": "missing", "disposition": "HOLD_MISSING_EVIDENCE"},
            {"fixture": "outbound", "disposition": "HOLD_EXTERNAL_ACTION"},
        ],
    }:
        return ("queue_review_only", "hold_missing_evidence", "hold_external_action")
    raise VerificationBlocked("offline_worker_known_answer_failed")


def validate_fixture_scope(ticket: FixtureTicket, task: QueueItem) -> None:
    """Reject all non-fixture scopes and assignments before a worker can run."""
    if not isinstance(ticket, FixtureTicket) or not isinstance(task, QueueItem):
        raise VerificationBlocked("missing_or_malformed_fixture_ticket")
    if not isinstance(ticket.service, str) or ticket.service not in PROFILES:
        raise VerificationBlocked("fixture_service_not_allowlisted")
    profile = PROFILES[ticket.service]
    if type(ticket.maximum_cost_cad) is not int or ticket != fixture_ticket(ticket.service, task):
        raise VerificationBlocked("fixture_ticket_scope_mismatch")
    position = TASKS[ticket.service].index(profile.task) + 1
    if (
        task.task != profile.task or task.opportunity_reference != profile.reference
        or task.role != "engineering" or task.state != "AWAITING_INTERNAL_REVIEW"
        or type(task.sequence) is not int or task.sequence != position
        or task.task_id != f"{profile.reference}:{position:02d}"
        or task.execution_authorized is not False or task.external_delivery_authorized is not False
        or task.spending_authorized is not False
    ):
        raise VerificationBlocked("fixture_assignment_mismatch")


def dispatch_fixture(ticket: FixtureTicket, task: QueueItem) -> tuple[dict, dict, str]:
    """Execute one known local fixture after deterministic scope validation."""
    validate_fixture_scope(ticket, task)
    try:
        output, runtime_observation, source_digest = _WORKERS[ticket.service]()
        if (
            not isinstance(runtime_observation, dict) or not isinstance(source_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", source_digest) is None
        ):
            raise VerificationBlocked("malformed_offline_worker_output")
        checks = _known_answer(ticket.service, output)
        return output, {
            **runtime_observation,
            "classification": "SYNTHETIC",
            "dispatch": asdict(ticket),
            "passed_checks": checks,
        }, source_digest
    except (OSError, subprocess.TimeoutExpired, RuntimeError, TypeError, KeyError, ValueError) as exc:
        if isinstance(exc, VerificationBlocked):
            raise
        raise VerificationBlocked("offline_worker_evidence_unavailable") from exc
