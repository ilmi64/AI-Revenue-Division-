import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_executive_snapshot import build_snapshot


class ExecutiveSnapshotTests(unittest.TestCase):
    def test_empty_sources_report_no_recorded_revenue(self):
        result = build_snapshot([], [])
        self.assertEqual(result["finance_cad"]["net_cash_received_verified_by_ledger_status"], "0.00")
        self.assertEqual(result["source"]["revenue_ledger_rows"], 0)

    def test_estimate_and_accepted_are_not_counted_as_cash(self):
        ledger = [{
            "opportunity_id": "A1", "gross_estimate": "100", "gross_accepted": "75",
            "fees": "0", "direct_costs": "0", "net_received_cad": "",
            "payment_status": "approved_unpaid"
        }]
        result = build_snapshot([], ledger)
        finance = result["finance_cad"]
        self.assertEqual(finance["gross_estimate_unconfirmed"], "100.00")
        self.assertEqual(finance["gross_accepted_not_necessarily_paid"], "75.00")
        self.assertEqual(finance["net_cash_received_verified_by_ledger_status"], "0.00")
        self.assertEqual(finance["accepted_but_unpaid_rows"], 1)

    def test_only_paid_status_counts_cash_received(self):
        ledger = [
            {"opportunity_id": "paid", "gross_estimate": "0", "gross_accepted": "50",
             "fees": "2", "direct_costs": "3", "net_received_cad": "45", "payment_status": "paid"},
            {"opportunity_id": "pending", "gross_estimate": "0", "gross_accepted": "90",
             "fees": "0", "direct_costs": "0", "net_received_cad": "90", "payment_status": "pending"}
        ]
        result = build_snapshot([], ledger)
        self.assertEqual(result["finance_cad"]["net_cash_received_verified_by_ledger_status"], "45.00")
        self.assertEqual(result["finance_cad"]["paid_ledger_rows"], 1)

    def test_opportunity_evidence_and_canada_checks_are_counted(self):
        opportunities = [{
            "id": "O1", "status": "verified", "official_url": "https://example.org",
            "evidence_checked_on": "2026-11-12", "canada_eligibility_checked": "yes"
        }]
        result = build_snapshot(opportunities, [])
        self.assertEqual(result["pipeline"]["opportunities_with_official_url_and_evidence_date"], 1)
        self.assertEqual(result["pipeline"]["canada_eligibility_checked"], 1)


if __name__ == "__main__":
    unittest.main()
