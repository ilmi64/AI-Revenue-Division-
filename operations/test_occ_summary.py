import unittest
from occ_summary import summarize

class OCCSummaryTests(unittest.TestCase):
    def test_counts_are_aggregated(self):
        report = summarize([{"status": "hold"}, {"status": "hold"},
                            {"status": "ready_for_manual_delivery"}])
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["counts"]["hold"], 2)
        self.assertEqual(report["counts"]["ready_for_manual_delivery"], 1)

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
