"""Regression coverage for the local two-company executive export."""

from datetime import datetime
import unittest

from occ_company_visibility import build_company_visibility
from occ_mobile_visibility import render_mobile_visibility


def projection(ai, trading):
    return {
        "mode": "offline_read_only", "operational_claim": False,
        "companies": {"ai_revenue": ai, "trading_technology": trading},
    }


class MobileVisibilityTests(unittest.TestCase):
    def test_missing_inputs_keep_company_cards_and_no_counts(self):
        report = build_company_visibility(now=datetime.fromisoformat("2026-11-24T12:00:00+00:00"))
        page = render_mobile_visibility(report)
        self.assertIn('aria-labelledby="ai_revenue"', page)
        self.assertIn('aria-labelledby="trading_technology"', page)
        self.assertIn("Operational readiness unverified", page)
        self.assertIn("Missing", page)
        self.assertNotIn("Reported work items", page)
        self.assertNotIn("Reported incidents", page)

    def test_only_allowlisted_redacted_fields_reach_html(self):
        report = projection(
            {"input_status": "UNVERIFIED_UNTIMED", "authentication": "AUTHENTICATED_OFFLINE",
             "reported_total": 2, "reported_counts": {"blocked": 1},
             "private_audit": "<img src=https://secret.invalid>"},
            {"input_status": "UNVERIFIED", "authentication": "AUTHENTICATED_OFFLINE",
             "reported_gate_counts": {"BLOCKED": 1},
             "reported_subsystem_statuses": {"research_intelligence": "DEGRADED", "recovery": "<script>alert(1)</script>"}},
        )
        page = render_mobile_visibility(report)
        self.assertIn("Offline signature verified", page)
        self.assertIn("Reported work items", page)
        self.assertIn("Research &amp; Intelligence", page)
        self.assertIn("Degraded", page)
        self.assertIn("Unknown", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<img", page)
        self.assertIn("default-src 'none'", page)

    def test_rejected_and_stale_inputs_hide_counts_without_suppressing_peer(self):
        for failure in ("REJECTED", "STALE", "QUARANTINED"):
            with self.subTest(failure=failure):
                page = render_mobile_visibility(projection(
                    {"input_status": "UNVERIFIED_UNTIMED", "reported_total": 1},
                    {"input_status": failure, "authentication": "AUTHENTICATED_OFFLINE",
                     "reported_gate_counts": {"BLOCKED": 999}},
                ))
                self.assertIn(failure.capitalize(), page)
                self.assertIn("Reported work items", page)
                self.assertNotIn("Reported gate counts", page)
                self.assertNotIn("Offline signature verified", page)
                self.assertNotIn("999", page)

    def test_refuses_an_operational_claim_or_missing_company_partition(self):
        report = projection({}, {})
        with self.assertRaisesRegex(ValueError, "offline read-only"):
            render_mobile_visibility({**report, "operational_claim": True})
        with self.assertRaisesRegex(ValueError, "two separate"):
            render_mobile_visibility({**report, "companies": {"ai_revenue": {}}})
