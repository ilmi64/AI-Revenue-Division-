"""Strict, read-only, non-authoritative cross-company commissioning projection.

No I/O, external actions, approval decisions, or private evidence ingestion.
"""
from __future__ import annotations

import re

COMPANIES = frozenset({"aevora_ai", "trading_technology"})
STATES = frozenset({"BLOCKED", "UNKNOWN", "RECONCILIATION_REQUIRED"})
TEST_PROVENANCE = frozenset({"UNVERIFIED", "OFFLINE_REPORTED"})
# Independent reproduction cannot be asserted by company-supplied input. A future
# authenticated verifier must issue that classification outside this projection.
BLOCKERS = frozenset({"custody", "trusted_time", "recovery", "signers", "lineage", "risk", "security", "research", "operations", "owner", "ci"})
FIELDS = frozenset({"company_id", "commit_sha", "gate", "test_provenance", "blockers", "evidence_digest"})
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ProjectionRejected(ValueError):
    """Input is invalid or could disclose company-local information."""


def _row(data: object) -> dict:
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ProjectionRejected("unexpected_or_missing_fields")
    company = data["company_id"]
    if not isinstance(company, str) or company not in COMPANIES:
        raise ProjectionRejected("invalid_company")
    sha = data["commit_sha"]
    if sha is not None and (not isinstance(sha, str) or not HEX40.fullmatch(sha)):
        raise ProjectionRejected("invalid_commit")
    gate = data["gate"]
    if not isinstance(gate, str) or gate not in STATES:
        raise ProjectionRejected("non_reporting_or_unsafe_gate")
    provenance = data["test_provenance"]
    if not isinstance(provenance, str) or provenance not in TEST_PROVENANCE:
        raise ProjectionRejected("invalid_test_provenance")
    blockers = data["blockers"]
    if (not isinstance(blockers, list) or any(not isinstance(b, str) or b not in BLOCKERS for b in blockers)
            or len(set(blockers)) != len(blockers)):
        raise ProjectionRejected("invalid_blockers")
    digest = data["evidence_digest"]
    if digest is not None and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
        raise ProjectionRejected("invalid_digest")
    if sha is None and provenance != "UNVERIFIED":
        raise ProjectionRejected("unbound_test_claim")
    if gate == "RECONCILIATION_REQUIRED" and "recovery" not in blockers:
        raise ProjectionRejected("missing_recovery_blocker")
    return {"company_id": company, "commit_sha": sha, "gate": gate,
            "test_provenance": provenance, "blockers": sorted(blockers), "evidence_digest": digest,
            "release_authorized": False, "execution_authorized": False}


def project(rows: object) -> dict:
    """Fail closed; return a bounded, allowlisted snapshot, never authorization."""
    if not isinstance(rows, list) or len(rows) != 2:
        raise ProjectionRejected("two_company_rows_required")
    checked = [_row(row) for row in rows]
    if {row["company_id"] for row in checked} != COMPANIES:
        raise ProjectionRejected("company_scope_duplicate_or_missing")
    return {"schema": "occ-commissioning-review-v1", "recipient": "Main Hub/OCC",
            "mode": "read_only_review", "release_authorized": False,
            "execution_authorized": False, "companies": sorted(checked, key=lambda row: row["company_id"])}
