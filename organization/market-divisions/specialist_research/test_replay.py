import unittest

from specialist_research.replay import replay
from specialist_research.test_capital_flow_handoff import event as flow_event, review as flow_review, REGISTRY as FLOW_REGISTRY

NOW = "2026-11-17T12:00:00Z"
AUTHORITY = "research_only_no_execution_authority"


def obs(kind, instrument_id):
    row = {
        "instrument_id": instrument_id, "instrument_type": kind,
        "source_id": "synthetic-local", "source_timestamp_utc": NOW,
        "received_timestamp_utc": NOW, "data_class": "synthetic",
        "licence_status": "not_applicable", "session_state": "open",
        "portfolio_version": 7, "evidence_refs": ["fixture:" + instrument_id],
        "currency": "USD", "unit_or_contract_multiplier": 1,
    }
    if kind == "crypto_spot":
        row.update(base_asset="SOL", quote_asset="USDC", market_pair="SOL/USDC",
                   currency="USDC", token_identity_status="verified",
                   chain_id="solana", contract_address="fixture-mint",
                   liquidity_evidence={"fixture_depth": True})
    elif kind == "fx_spot":
        row.update(base_currency="EUR", quote_currency="USD",
                   quote_convention="quote_per_base",
                   central_bank_evidence=["fixture:cb"],
                   macro_calendar_evidence=["fixture:calendar"],
                   financing_status="unknown")
    elif kind == "index_cash":
        row.update(index_code="FIXTURE500", index_calculation_currency="USD",
                   constituent_weight_provenance=["fixture:weights"])
    elif kind == "xauusd_spot":
        row.update(gold_price_basis="synthetic_test", gold_session="fixture-session",
                   quote_age_seconds=1, stale_threshold_seconds=30, is_stale=False,
                   financing_status="unknown", settlement_type="unknown",
                   real_yield_evidence=["fixture:real-yield"], usd_evidence=["fixture:usd"],
                   central_bank_demand_evidence=["fixture:demand"])
    return row


def gate(rows, status="PASS_RESEARCH_GATES"):
    return {
        "status": status, "authority": AUTHORITY,
        "market_observations": [
            {"record_id": row["instrument_id"], "eligible": True, "warnings": [],
             "mode": "research_only", "trade_authority": False}
            for row in rows
        ],
    }


class ReplayTests(unittest.TestCase):
    def test_four_desk_replay_keeps_gold_separate(self):
        rows = [obs("crypto_spot", "SOL-USDC"), obs("fx_spot", "EUR-USD"),
                obs("index_cash", "FIXTURE500"), obs("xauusd_spot", "XAUUSD-FIXTURE")]
        result = replay(rows, gate(rows), NOW)
        self.assertEqual(result["status"], "unverified")
        self.assertEqual({p["desk_id"] for p in result["desk_packets"]},
                         {"crypto", "forex", "indices", "gold"})
        self.assertFalse(result["live_readiness"])
        self.assertEqual(result["capital_flow_handoff"]["status"], "not_consumed")

    def test_verified_capital_flow_event_attaches_only_to_exact_crypto_identity(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        events = [flow_event(contract_address="fixture-mint")]
        reviews = [flow_review()]
        result = replay(rows, gate(rows), NOW, events, reviews, FLOW_REGISTRY)
        packet = result["desk_packets"][0]
        self.assertEqual(len(packet["capital_flow_handoff"]["event_records"]), 1)
        self.assertEqual(result["capital_flow_handoff"]["status"], "consumed_research_context")
        self.assertFalse(result["capital_flow_handoff"]["trade_authority"])
        self.assertFalse(result["trade_authority"])

    def test_capital_flow_wrong_contract_never_attaches(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        events = [flow_event(contract_address="different-mint")]
        result = replay(rows, gate(rows), NOW, events, [flow_review()], FLOW_REGISTRY)
        self.assertEqual(result["capital_flow_handoff"]["accepted_event_count"], 0)
        self.assertEqual(result["capital_flow_handoff"]["status"], "provided_no_eligible_match")

    def test_capital_flow_broken_ledger_is_blocked_without_granting_authority(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        bad_review = flow_review()
        bad_review["reason"] = "tampered"
        result = replay(rows, gate(rows), NOW, [flow_event(contract_address="fixture-mint")], [bad_review], FLOW_REGISTRY)
        packet = result["desk_packets"][0]
        self.assertEqual(packet["capital_flow_handoff"]["status"], "blocked")
        self.assertIn("CAPITAL_FLOW_HANDOFF_REJECTED", packet["risk_flags"])
        self.assertFalse(result["trade_authority"])

    def test_nonpassing_gate_blocks_replay(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = replay(rows, gate(rows, "PARTIAL_OR_BLOCKED"), NOW)
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["desk_packets"][0]["status"], "halt")

    def test_missing_gate_record_blocks_observation(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = replay(rows, gate([]), NOW)
        self.assertEqual(result["status"], "halt")
        self.assertIn("EVIDENCE_GATE_BLOCK", result["desk_packets"][0]["risk_flags"])

    def test_duplicate_instrument_id_halts_coordinator(self):
        rows = [obs("crypto_spot", "DUPLICATE"), obs("crypto_spot", "DUPLICATE")]
        result = replay(rows, gate(rows), NOW)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any("duplicate instrument_id" in e for e in result["occ"]["errors"]))

    def test_authority_mismatch_blocks_replay(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        report = gate(rows)
        report["authority"] = "execution_enabled"
        result = replay(rows, report, NOW)
        self.assertEqual(result["status"], "halt")

    def test_unknown_instrument_type_not_silently_routed(self):
        rows = [obs("unknown_product", "MYSTERY")]
        result = replay(rows, gate(rows), NOW)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(result["occ"]["errors"])


if __name__ == "__main__":
    unittest.main()
