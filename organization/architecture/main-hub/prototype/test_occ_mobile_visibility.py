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

    def test_authenticated_divisional_counts_show_zero_and_unknown_in_separate_cards(self):
        counts = {"open_incident_count": 0, "pending_approval_count": 2, "blocker_count": 3}
        ai = {
            "input_status": "UNVERIFIED_UNTIMED", "authentication": "AUTHENTICATED_OFFLINE",
            "reported_divisional_telemetry": {
                "company_totals": counts, "divisions": {"commercial_operations": counts},
            },
        }
        trading = {
            "input_status": "UNVERIFIED", "authentication": "AUTHENTICATED_OFFLINE",
            "reported_commissioning_status": "BLOCKED",
            "reported_divisional_telemetry": {
                "company_totals": {"open_incident_count": 1, "pending_approval_count": 0, "blocker_count": 1},
                "divisions": {"portfolio-private-evidence": counts},
            },
        }
        html = render_mobile_visibility(projection(ai, trading))
        ai_card, trading_card = html.split('<article aria-labelledby="trading_technology">')
        self.assertIn("Pending approvals</dt><dd>2", ai_card)
        self.assertIn("Open incidents</dt><dd>0", ai_card)
        self.assertIn("Pending approvals</dt><dd>Unknown", ai_card)
        self.assertIn("Reported commissioning</dt><dd>Blocked", trading_card)
        self.assertIn("Pending approvals</dt><dd>0", trading_card)
        self.assertNotIn("portfolio-private-evidence", html)

    def test_divisional_counts_are_hidden_when_auth_or_input_is_unavailable(self):
        for authentication, status in (("UNVERIFIED", "UNVERIFIED"), ("AUTHENTICATED_OFFLINE", "QUARANTINED")):
            with self.subTest(authentication=authentication, status=status):
                page = render_mobile_visibility(projection(
                    {"input_status": "MISSING"},
                    {"input_status": status, "authentication": authentication,
                     "reported_commissioning_status": "BLOCKED",
                     "reported_divisional_telemetry": {
                         "company_totals": {"pending_approval_count": 999},
                     }},
                ))
                self.assertNotIn("Pending approvals", page)
                self.assertNotIn("999", page)

    def test_commissioning_label_uses_the_validated_m2_readiness_gate(self):
        from pathlib import Path

        from occ_readonly import read_fixture

        snapshot = read_fixture(Path(__file__).resolve().parents[1] / "fixtures" / "trading-technology.snapshot.example.json")
        now = datetime.fromisoformat(snapshot["published_at"])
        report = build_company_visibility(trading_snapshot=snapshot, now=now)
        page = render_mobile_visibility(report)
        self.assertIn("Reported commissioning</dt><dd>Not run", page)

    def test_checkpoint_display_uses_verifier_assessment_time_in_utc(self):
        timestamp = datetime.fromisoformat("2026-11-26T08:30:45-05:00")
        page = render_mobile_visibility(projection({}, {}), assessed_at=timestamp)
        self.assertIn('<time datetime="2026-11-26T13:30:45Z">2026-11-26 13:30:45 UTC</time>', page)
        self.assertNotIn("Evidence time verified", page)

    def test_legacy_report_has_unknown_assessment_time_and_rejects_naive_values(self):
        page = render_mobile_visibility(projection({}, {}))
        self.assertIn("Assessment time unknown", page)
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            render_mobile_visibility(projection({}, {}), assessed_at=datetime(2026, 11, 26))
