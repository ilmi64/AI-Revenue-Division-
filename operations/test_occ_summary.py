import unittest
from occ_summary import summarize

class OCCSummaryTests(unittest.TestCase):
    def test_counts_are_aggregated(self):
        report = summarize([{"status": "hold"}, {"status": "hold"},
                            {"status": "checklist_complete_unverified"}])
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["counts"]["hold"], 2)
        self.assertEqual(report["counts"]["ready_for_manual_delivery"], 1)

    def test_legacy_delivery_ready_status_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize([{"status": "ready_for_manual_delivery"}])

    def test_delivery_gate_to_occ_summary_remains_unverified(self):
        from delivery_gate import decide
        item = {"opportunity": {"id": "synthetic-1", "kind": "coding",
                 "title": "Synthetic task", "source_url": "https://example.org/task",
                 "scope_authorized": True, "cost_cad": 0,
                 "requires_credentials": False, "external_action": False,
                 "deadline_utc": None},
                "evidence": {"task_owner": "producer", "source_commit": "a" * 40,
                             "tests_passed": True, "test_command": "python -m unittest",
                             "test_log_ref": "local:claimed.log"},
                "approvals": {"delivery_authorized": True, "scope_reviewed": True}}
        decision = decide(item)
        report = summarize([decision])
        self.assertEqual(report["counts"]["checklist_complete_unverified"], 1)
        self.assertFalse(decision["release_authorized"])
        self.assertFalse(report["execution_authorized"])

    def test_private_fields_not_exported(self):
        secret = "CONFIDENTIAL_CUSTOMER_INFORMATION"
        report = summarize([{"status": "blocked", "customer_name": secret,
                             "credentials": secret, "opportunity_id": secret}])
        self.assertNotIn(secret, str(report))
        self.assertFalse(report["execution_authorized"])

    def test_empty_report(self):
        self.assertEqual(summarize([])["total"], 0)

    def test_invalid_status_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize([{"status": "authorized_to_trade"}])

    def test_malformed_item_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize([None])

    def test_non_list_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize({"status": "hold"})

if __name__ == "__main__":
    unittest.main()
