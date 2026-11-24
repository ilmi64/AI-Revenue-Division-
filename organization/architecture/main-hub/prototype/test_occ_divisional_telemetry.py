"""Scoped signed division counts through the existing durable OCC path."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
from shutil import copyfile
import unittest

import test_occ_durable_receipt_anchor as durable_fixture
from occ_receipt_anchor import custody_digest
from occ_signed_visibility import ReceiptJournal, sign_fixture


AI, TRADING, NOW = durable_fixture.AI, durable_fixture.TRADING, durable_fixture.NOW


def counts(incidents, approvals, blockers):
    return {
        "open_incident_count": incidents, "pending_approval_count": approvals, "blocker_count": blockers,
    }


class DivisionalTelemetryTests(unittest.TestCase):
    def setUp(self):
        durable_fixture.DurableReceiptAnchorTests.setUp(self)
        self.original_trust = dict(self.trust)
        for company in (AI, TRADING):
            before = self.trust[company]
            after = replace(before, divisional_telemetry=True)
            approval = self.authorize(after, signer=company, current=self.anchor.read(company))
            self.journals[company].transition_custody(before, after, approval, now=NOW)
            self.trust[company] = after

    authorize = durable_fixture.DurableReceiptAnchorTests.authorize
    view = durable_fixture.DurableReceiptAnchorTests.view
    reopen = durable_fixture.DurableReceiptAnchorTests.reopen

    def payload(self, company):
        if company == AI:
            return {
                "report": deepcopy(self.ai),
                "divisional_telemetry": {
                    "company_totals": counts(2, 4, 6),
                    "divisions": {"commercial_operations": counts(0, 3, 4), "recovery": counts(1, 0, 1)},
                },
            }
        return {
            "report": deepcopy(self.trading),
            "divisional_telemetry": {
                "company_totals": counts(0, 7, 1),
                "divisions": {"paper_trading": counts(0, 2, 0), "recovery": counts(0, 4, 1)},
            },
        }

    def wire(self, company, *, payload=None, trust=None, sequence=1):
        return sign_fixture(
            self.payload(company) if payload is None else payload,
            trust=self.trust[company] if trust is None else trust,
            sequence=sequence, issued_at=NOW, expires_at=NOW + timedelta(seconds=30),
            private_key=self.keys[company],
        )

    def test_independent_counts_reach_projection_with_zero_distinct_from_missing(self):
        report = self.view(ai_revenue_wire=self.wire(AI), trading_wire=self.wire(TRADING))
        for company in (AI, TRADING):
            with self.subTest(company=company):
                expected = self.payload(company)["divisional_telemetry"]
                self.assertEqual(report[company]["reported_divisional_telemetry"], expected)
                self.assertEqual(report[company]["authentication"], "AUTHENTICATED_OFFLINE")
                self.assertNotIn("ai_workforce", expected["divisions"])
        self.assertEqual(report[AI]["reported_divisional_telemetry"]["divisions"]
                         ["commercial_operations"]["open_incident_count"], 0)
        self.assertNotIn("snapshot_id", json.dumps(report))

    def test_bad_counters_scope_and_unapproved_details_reject_without_suppressing_peer(self):
        for kind in ("peer", "boolean", "negative", "overflow", "extra", "overcount", "unknown"):
            with self.subTest(kind=kind):
                payload = self.payload(AI)
                telemetry = payload["divisional_telemetry"]
                if kind == "peer":
                    telemetry["divisions"]["paper_trading"] = counts(0, 0, 0)
                elif kind == "boolean":
                    telemetry["company_totals"]["blocker_count"] = False
                elif kind == "negative":
                    telemetry["company_totals"]["blocker_count"] = -1
                elif kind == "overflow":
                    telemetry["company_totals"]["pending_approval_count"] = 1 << 53
                elif kind == "extra":
                    telemetry["divisions"]["recovery"]["raw_id"] = "PRIVATE-ID"
                elif kind == "overcount":
                    telemetry["divisions"]["recovery"]["pending_approval_count"] = 4
                else:
                    del telemetry["company_totals"]["pending_approval_count"]
                outcome = self.view(ai_revenue_wire=self.wire(AI, payload=payload))
                self.assertEqual(outcome[AI], {"input_status": "REJECTED", "authentication": "UNVERIFIED"})
                self.assertEqual(self.anchor.read(AI).count, 0)
        report = self.view(ai_revenue_wire=self.wire(AI, payload={**self.payload(AI), "raw": "PRIVATE"}),
                           trading_wire=self.wire(TRADING))
        self.assertEqual(report[AI]["input_status"], "REJECTED")
        self.assertEqual(report[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_m2_incident_blocker_conflict_fails_closed_and_quarantine_hides_all_counts(self):
        for field in ("open_incident_count", "blocker_count"):
            payload = self.payload(TRADING)
            payload["divisional_telemetry"]["company_totals"][field] += 1
            self.assertEqual(self.view(trading_wire=self.wire(TRADING, payload=payload))[TRADING]
                             ["input_status"], "REJECTED")
        payload = self.payload(TRADING)
        payload["report"]["incident_summary"] = {
            "open_count": 1, "highest_severity": "high", "quarantined": True,
        }
        payload["divisional_telemetry"]["company_totals"]["open_incident_count"] = 1
        view = self.view(trading_wire=self.wire(TRADING, payload=payload))[TRADING]
        self.assertEqual(view, {
            "input_status": "QUARANTINED", "display_status": "UNKNOWN",
            "authentication": "AUTHENTICATED_OFFLINE",
        })

    def test_extension_cannot_downgrade_or_use_unanchored_journal(self):
        original = self.original_trust[AI]
        self.assertNotEqual(custody_digest(original), custody_digest(self.trust[AI]))
        legacy = self.wire(AI, trust=original, payload=self.ai)
        rejected = self.view(ai_revenue_wire=legacy, trust_by_company={**self.trust, AI: original})
        self.assertEqual(rejected[AI]["input_status"], "REJECTED")
        journal = ReceiptJournal.initialize(self.path / "unanchored-ai.sqlite", company_id=AI)
        self.assertEqual(self.view(ai_revenue_wire=self.wire(AI),
                                   journal_by_company={**self.journals, AI: journal})
                         [AI]["input_status"], "REJECTED")

    def test_concurrent_cloned_and_reopened_journals_cannot_repeat_telemetry(self):
        clone = self.path / "clone.sqlite"
        copyfile(self.journals[AI].path, clone)
        wire = self.wire(AI)
        with ThreadPoolExecutor(max_workers=2) as pool:
            views = list(pool.map(lambda path: self.view(
                ai_revenue_wire=wire,
                journal_by_company={**self.journals, AI: ReceiptJournal(path, AI, self.reopen())},
            )[AI], (clone, self.journals[AI].path)))
        self.assertEqual(sum("reported_divisional_telemetry" in view for view in views), 1)
        self.assertEqual(self.reopen().read(AI).count, 1)

    def test_expired_or_replayed_extended_report_never_exposes_counts(self):
        wire = self.wire(AI)
        self.assertEqual(self.view(ai_revenue_wire=wire, now=NOW + timedelta(seconds=31))[AI],
                         {"input_status": "REJECTED", "authentication": "UNVERIFIED"})
        self.assertEqual(self.view(ai_revenue_wire=wire)[AI]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(self.view(ai_revenue_wire=wire)[AI],
                         {"input_status": "REJECTED", "authentication": "UNVERIFIED"})
