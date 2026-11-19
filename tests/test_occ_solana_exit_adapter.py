import unittest

from occ.solana_exit_adapter import (
    SolanaExitAdapterError, collect_solana_exit_incidents,
)


class FakeSource:
    def __init__(self):
        self.market = [{
            "incident_id": "md-1", "symbol": "SOL/CAD",
            "reason_code": "EXIT_MARK_STALE",
            "first_seen_epoch": 100.0, "last_seen_epoch": 110.0,
            "occurrences": 2, "status": "UNRESOLVED",
        }]
        self.exits = [{
            "operation_id": "op-9", "symbol": "BTC/CAD",
            "created_at_epoch": 105.0, "status": "REVIEW_REQUIRED",
        }]
        self.calls = []

    def unresolved_exit_market_data_incidents(self):
        self.calls.append("market")
        return [dict(row) for row in self.market]

    def unresolved_position_exits(self):
        self.calls.append("exits")
        return [dict(row) for row in self.exits]


class SolanaExitAdapterTests(unittest.TestCase):
    def test_maps_both_sources_with_stable_namespaced_identity(self):
        source = FakeSource()
        report = collect_solana_exit_incidents(source, now_epoch=120.0)
        self.assertEqual(source.calls, ["market", "exits"])
        self.assertEqual(report["source_record_count"], 2)
        self.assertEqual(report["active_count"], 2)
        rows = {item["source_incident_id"]: item for item in report["incidents"]}
        market = rows["market-data:md-1"]
        position = rows["position-exit:op-9"]
        self.assertEqual(market["source_system"], "solana-paper-exit-market-data")
        self.assertEqual(market["instrument"], "SOL/CAD")
        self.assertEqual(market["reason_code"], "EXIT_MARK_STALE")
        self.assertEqual(position["source_system"], "solana-paper-exit-position")
        self.assertEqual(position["instrument"], "BTC/CAD")
        self.assertEqual(position["source_status"], "REVIEW_REQUIRED")
        self.assertEqual(market["severity"], "CRITICAL")
        self.assertEqual(position["status"], "OPEN")

    def test_source_records_are_not_mutated(self):
        source = FakeSource()
        before_market = [dict(row) for row in source.market]
        before_exits = [dict(row) for row in source.exits]
        collect_solana_exit_incidents(source, now_epoch=120.0)
        self.assertEqual(source.market, before_market)
        self.assertEqual(source.exits, before_exits)

    def test_rejects_non_unresolved_market_row(self):
        source = FakeSource()
        source.market[0]["status"] = "RESOLVED"
        with self.assertRaisesRegex(SolanaExitAdapterError, "non-unresolved"):
            collect_solana_exit_incidents(source, now_epoch=120.0)

    def test_rejects_unsupported_position_status(self):
        source = FakeSource()
        source.exits[0]["status"] = "COMPLETED"
        with self.assertRaisesRegex(SolanaExitAdapterError, "unsupported status"):
            collect_solana_exit_incidents(source, now_epoch=120.0)

    def test_rejects_missing_stable_identity(self):
        source = FakeSource()
        source.market[0]["incident_id"] = ""
        with self.assertRaises(SolanaExitAdapterError):
            collect_solana_exit_incidents(source, now_epoch=120.0)

    def test_requires_read_only_source_methods(self):
        with self.assertRaises(SolanaExitAdapterError):
            collect_solana_exit_incidents(object(), now_epoch=120.0)


if __name__ == "__main__":
    unittest.main()
