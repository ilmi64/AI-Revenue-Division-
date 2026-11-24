"""Offline coverage for independent company OCC visibility."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from occ_company_visibility import _read_optional, build_company_visibility
from occ_readonly import EXPECTED, read_fixture


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


class CompanyVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.ai = read_fixture(FIXTURES / EXPECTED["ai_revenue"])
        self.trading = read_fixture(FIXTURES / EXPECTED["trading_technology"])
        self.operations = {
            "organization": "Daivora Group",
            "source_company": "Aevora AI",
            "recipient": "Main Hub/OCC",
            "mode": "read_only_aggregate",
            "execution_authorized": False,
            "external_actions_performed": False,
            "counts": {
                "blocked": 0,
                "checklist_complete_unverified": 1,
                "hold": 0,
                "rejected": 0,
                "review_ready": 0,
            },
            "total": 1,
        }

    def build(self, **overrides):
        inputs = dict(
            ai_revenue_snapshot=self.ai,
            trading_snapshot=self.trading,
            aevora_operations=self.operations,
            now=NOW,
        )
        return build_company_visibility(**{**inputs, **overrides})

    def test_different_company_statuses_do_not_roll_up_into_a_readiness_claim(self):
        self.ai["subsystems"].update(commercial_operations="HEALTHY", ai_workforce="DEGRADED")
        self.trading["subsystems"].update(paper_trading="BLOCKED", recovery="DEGRADED")
        self.ai["gates"][0]["status"] = "PASS"
        self.trading["gates"][0]["status"] = "FAIL"
        report = self.build()
        ai, trading = (report["companies"][company] for company in EXPECTED)
        self.assertFalse(report["operational_claim"])
        self.assertEqual(ai["operations"]["reported_total"], 1)
        self.assertEqual(ai["operations"]["input_status"], "UNVERIFIED_UNTIMED")
        self.assertNotIn("operations", trading)
        self.assertEqual(ai["snapshot"]["reported_critical_gates_not_passed"], 0)
        self.assertEqual(trading["snapshot"]["reported_critical_gates_not_passed"], 1)
        self.assertEqual(ai["snapshot"]["reported_subsystem_statuses"]["ai_workforce"], "DEGRADED")
        self.assertEqual(ai["snapshot"]["reported_subsystem_statuses"]["research_intelligence"], "UNKNOWN")
        self.assertEqual(trading["snapshot"]["reported_subsystem_statuses"]["recovery"], "DEGRADED")
        for view in (ai, trading):
            self.assertEqual(view["snapshot"]["display_status"], "UNKNOWN")

    def test_swapped_snapshots_and_cross_company_evidence_are_rejected(self):
        report = self.build(ai_revenue_snapshot=self.trading, trading_snapshot=self.ai)
        for view in report["companies"].values():
            self.assertEqual(view["snapshot"]["input_status"], "REJECTED")
        self.trading["gates"][0]["evidence_refs"] = [self.ai["evidence"][0]["evidence_id"]]
        report = self.build()
        self.assertEqual(report["companies"]["trading_technology"]["snapshot"]["input_status"], "REJECTED")
        self.assertEqual(report["companies"]["ai_revenue"]["snapshot"]["input_status"], "UNVERIFIED")

    def test_free_text_never_reaches_report_and_unknown_fields_reject(self):
        snapshot = self.ai
        before = deepcopy(snapshot)
        snapshot["snapshot_id"] = "PRIVATE-IDENTIFIER"
        snapshot["gates"][0]["notes"] = "PRIVATE-NOTE"
        snapshot["blockers"][0]["summary"] = "PRIVATE-BLOCKER"
        snapshot["evidence"][0]["reference"] = "synthetic://PRIVATE-EVIDENCE"
        preview = self.build()
        self.assertEqual(preview, self.build(ai_revenue_snapshot=before))
        self.assertNotIn("PRIVATE-", json.dumps(preview))
        snapshot["PRIVATE-FIELD"] = "PRIVATE-ITEM"
        self.assertEqual(self.build()["companies"]["ai_revenue"]["snapshot"]["input_status"], "REJECTED")
        del snapshot["PRIVATE-FIELD"]
        snapshot["subsystems"]["paper_trading"] = "HEALTHY"
        self.assertEqual(self.build()["companies"]["ai_revenue"]["snapshot"]["input_status"], "REJECTED")

    def test_missing_stale_invalid_and_quarantined_inputs_are_distinct(self):
        self.assertEqual(build_company_visibility(now=NOW)["companies"]["ai_revenue"]["snapshot"]["input_status"], "MISSING")
        old = NOW - timedelta(hours=25)
        self.trading["published_at"] = old.isoformat()
        trading = self.build()["companies"]["trading_technology"]["snapshot"]
        self.assertEqual(trading["input_status"], "STALE")
        self.assertNotIn("reported_gate_counts", trading)
        self.trading["incident_summary"]["quarantined"] = True
        trading = self.build()["companies"]["trading_technology"]["snapshot"]
        self.assertEqual(trading["input_status"], "QUARANTINED")
        self.assertNotIn("reported_gate_counts", trading)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trading.snapshot.json"
            path.write_text('{"PRIVATE-DUPLICATE": 1, "PRIVATE-DUPLICATE": 2}', encoding="utf-8")
            report = self.build(trading_snapshot=_read_optional(path))
            self.assertEqual(report["companies"]["trading_technology"]["snapshot"]["input_status"], "REJECTED")
            self.assertEqual(report["companies"]["ai_revenue"]["snapshot"]["input_status"], "UNVERIFIED")
            self.assertNotIn("PRIVATE-", json.dumps(report))

    def test_aevora_aggregate_rejects_spoofed_authority_scope_and_counts(self):
        for changes in (
            {"source_company": "Trading & Technology"},
            {"recipient": "Trading & Technology"},
            {"execution_authorized": True},
            {"external_actions_performed": True},
            {"total": 0},
            {"total": True},
            {"total": 0, "counts": {**self.operations["counts"], "checklist_complete_unverified": False}},
            {"counts": {**self.operations["counts"], "PRIVATE-CASE": 1}},
            {"PRIVATE-FIELD": "PRIVATE-CASE"},
        ):
            with self.subTest(changes=changes):
                report = self.build(aevora_operations={**self.operations, **changes})
                self.assertEqual(report["companies"]["ai_revenue"]["operations"], {"input_status": "REJECTED"})
                self.assertEqual(report["companies"]["trading_technology"]["snapshot"]["input_status"], "UNVERIFIED")
