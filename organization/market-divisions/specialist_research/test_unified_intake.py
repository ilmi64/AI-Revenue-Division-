import unittest

from specialist_research.unified_intake import build_unified_intake, validate_handover
from specialist_research.test_replay import NOW, obs, source_registry


class UnifiedIntakeTests(unittest.TestCase):
    def four_desk_rows(self):
        return [
            obs("crypto_spot", "SOL-USDC"),
            obs("fx_spot", "EUR-USD"),
            obs("index_cash", "FIXTURE500"),
            obs("xauusd_spot", "XAUUSD-FIXTURE"),
        ]

    def build(self, rows=None, **kwargs):
        rows = rows or self.four_desk_rows()
        version = kwargs.pop("expected_portfolio_version", 7)
        return build_unified_intake(rows, NOW, source_registry(rows),
                                    expected_portfolio_version=version, **kwargs)

    def test_builds_one_snapshot_across_all_four_specialist_desks(self):
        result = self.build()
        self.assertEqual(result["desk_coverage"],
                         {"crypto": 1, "forex": 1, "indices": 1, "gold": 1})
        self.assertTrue(result["coverage_complete"])
        self.assertEqual(result["status"], "unverified")
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertEqual(result["authority"], "research_only_no_execution_authority")

    def test_multiple_instruments_per_desk_are_supported(self):
        rows = self.four_desk_rows() + [obs("crypto_spot", "BTC-USDC")]
        rows[-1].update(base_asset="BTC", market_pair="BTC/USDC",
                        contract_address="fixture-btc")
        result = self.build(rows)
        self.assertEqual(result["desk_coverage"]["crypto"], 2)
        self.assertEqual(result["occ"]["packet_count"], 5)
        self.assertEqual(result["occ"]["desk_count"], 4)

    def test_missing_desk_is_visible_and_full_coverage_can_be_required(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        partial = self.build(rows)
        self.assertEqual(partial["missing_desks"], ["forex", "indices", "gold"])
        self.assertEqual(partial["status"], "unverified")
        strict = self.build(rows, require_full_coverage=True)
        self.assertEqual(strict["status"], "halt")
        self.assertTrue(strict["packet_validation_errors"])

    def test_any_specialist_halt_propagates_to_global_stop(self):
        rows = self.four_desk_rows()
        rows[0]["token_identity_status"] = "unverified"
        result = self.build(rows)
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any(x["source"] == "crypto" for x in result["active_stops"]))

    def test_prior_stop_cannot_be_cleared_by_clear_observation(self):
        result = self.build(previous_global_stop=True, occ_stop_state="CLEAR")
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any(x["source"] == "prior_occ_state" for x in result["active_stops"]))

    def test_explicit_occ_halt_propagates(self):
        result = self.build(occ_stop_state="HALT")
        self.assertTrue(result["global_stop_active"])
        self.assertTrue(any(x["source"] == "occ_control" for x in result["active_stops"]))

    def test_evidence_index_preserves_desk_and_instrument_provenance(self):
        result = self.build()
        refs = result["evidence_index"]["fixture:SOL-USDC"]
        self.assertEqual(refs[0]["desk_id"], "crypto")
        self.assertEqual(refs[0]["instrument_id"], "SOL-USDC")
        self.assertEqual(refs[0]["evidence_type"], "market_observation")

    def test_handover_requires_both_acknowledgements_and_reconciliation(self):
        record = {
            "outgoing_shift_id": "day", "incoming_shift_id": "night",
            "handover_at_utc": NOW, "snapshot_id": "snapshot-1",
            "portfolio_version": 7, "active_veto_ids": [],
            "unresolved_critical_items": [], "dependency_health": "healthy",
            "outgoing_acknowledged": True, "incoming_acknowledged": True,
            "positions_reconciled": True,
        }
        result = validate_handover(record, NOW, 7)
        self.assertTrue(result["accepted"])
        record["incoming_acknowledged"] = False
        self.assertFalse(validate_handover(record, NOW, 7)["accepted"])

    def test_missing_handover_is_not_assumed_accepted(self):
        result = self.build()
        self.assertEqual(result["handover"]["status"], "not_provided")
        self.assertFalse(result["handover"]["accepted"])

    def test_handover_veto_remains_active(self):
        record = {
            "outgoing_shift_id": "day", "incoming_shift_id": "night",
            "handover_at_utc": NOW, "snapshot_id": "snapshot-1",
            "portfolio_version": 7, "active_veto_ids": ["veto-1"],
            "unresolved_critical_items": [], "dependency_health": "healthy",
            "outgoing_acknowledged": True, "incoming_acknowledged": True,
            "positions_reconciled": True,
        }
        result = self.build(handover=record)
        self.assertTrue(result["global_stop_active"])
        self.assertTrue(any("veto-1" in x["reason"] for x in result["active_stops"]))

    def test_wrong_portfolio_version_fails_before_replay(self):
        rows = self.four_desk_rows()
        with self.assertRaisesRegex(ValueError, "portfolio version mismatch"):
            self.build(rows, expected_portfolio_version=99)

    def test_partial_capital_flow_inputs_are_rejected(self):
        rows = self.four_desk_rows()
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            self.build(rows, capital_flow_events=[])

    def test_duplicate_evidence_refs_are_indexed_without_losing_sources(self):
        rows = self.four_desk_rows()
        rows[1]["evidence_refs"] = ["fixture:SOL-USDC"]
        result = self.build(rows)
        entries = result["evidence_index"]["fixture:SOL-USDC"]
        self.assertEqual({x["desk_id"] for x in entries}, {"crypto", "forex"})


if __name__ == "__main__":
    unittest.main()
