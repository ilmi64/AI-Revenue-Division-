import unittest

from specialist_research.replay import replay
from specialist_research.test_capital_flow_handoff import (
    event as flow_event, review as flow_review, REGISTRY as FLOW_REGISTRY,
)

NOW = "2026-11-17T12:00:00Z"


def obs(kind, instrument_id):
    row = {
        "instrument_id": instrument_id, "instrument_type": kind,
        "source_id": "synthetic-local", "venue_or_broker": "fixture-venue",
        "source_timestamp_utc": NOW, "received_timestamp_utc": NOW,
        "data_class": "synthetic", "licence_status": "not_applicable",
        "session_state": "open", "portfolio_version": 7,
        "evidence_refs": ["fixture:" + instrument_id],
        "currency": "USD", "unit_or_contract_multiplier": 1,
        "bid": 99.9, "ask": 100.1,
    }
    if kind in {"crypto_spot", "crypto_perpetual"}:
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
                   quote_unit="USD_per_troy_ounce", quote_age_seconds=0,
                   stale_threshold_seconds=30, is_stale=False,
                   financing_status="unknown", settlement_type="unknown",
                   real_yield_evidence=["fixture:real-yield"],
                   usd_evidence=["fixture:usd"],
                   central_bank_demand_evidence=["fixture:demand"])
    return row


def source_registry(rows):
    return {
        "instruments": [
            {"id": row["instrument_id"], "candidate_sources": [{
                "name": row["source_id"], "status": "approved_manual",
                "terms_review": "approved", "canada_review": "approved",
            }]}
            for row in rows
        ]
    }


class ReplayTests(unittest.TestCase):
    def run_replay(self, rows, registry=None, **kwargs):
        return replay(rows, NOW, registry if registry is not None else source_registry(rows), **kwargs)

    def test_four_desk_replay_reruns_gate_and_keeps_gold_separate(self):
        rows = [obs("crypto_spot", "SOL-USDC"), obs("fx_spot", "EUR-USD"),
                obs("index_cash", "FIXTURE500"), obs("xauusd_spot", "XAUUSD-FIXTURE")]
        result = self.run_replay(rows)
        self.assertEqual(result["status"], "unverified")
        self.assertEqual({p["desk_id"] for p in result["desk_packets"]},
                         {"crypto", "forex", "indices", "gold"})
        self.assertEqual(result["evidence_gate"]["method"],
                         "rerun_from_raw_observation_and_source_registry")
        self.assertFalse(result["live_readiness"])
        self.assertEqual(result["capital_flow_handoff"]["status"], "not_consumed")

    def test_verified_capital_flow_event_attaches_only_to_exact_crypto_identity(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = self.run_replay(
            rows, capital_flow_events=[flow_event(contract_address="fixture-mint")],
            capital_flow_reviews=[flow_review()],
            capital_flow_source_registry=FLOW_REGISTRY,
        )
        packet = result["desk_packets"][0]
        self.assertEqual(len(packet["capital_flow_handoff"]["event_records"]), 1)
        self.assertEqual(result["capital_flow_handoff"]["status"], "consumed_research_context")
        self.assertFalse(result["capital_flow_handoff"]["trade_authority"])
        self.assertFalse(result["trade_authority"])

    def test_capital_flow_wrong_contract_never_attaches(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = self.run_replay(
            rows, capital_flow_events=[flow_event(contract_address="different-mint")],
            capital_flow_reviews=[flow_review()],
            capital_flow_source_registry=FLOW_REGISTRY,
        )
        self.assertEqual(result["capital_flow_handoff"]["accepted_event_count"], 0)
        self.assertEqual(result["capital_flow_handoff"]["status"], "provided_no_eligible_match")

    def test_capital_flow_broken_ledger_is_blocked_without_granting_authority(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        bad_review = flow_review()
        bad_review["reason"] = "tampered"
        result = self.run_replay(
            rows, capital_flow_events=[flow_event(contract_address="fixture-mint")],
            capital_flow_reviews=[bad_review],
            capital_flow_source_registry=FLOW_REGISTRY,
        )
        packet = result["desk_packets"][0]
        self.assertEqual(packet["capital_flow_handoff"]["status"], "blocked")
        self.assertIn("CAPITAL_FLOW_HANDOFF_REJECTED", packet["risk_flags"])
        self.assertFalse(result["trade_authority"])

    def test_unapproved_market_source_blocks_desk(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        registry = source_registry(rows)
        registry["instruments"][0]["candidate_sources"][0]["terms_review"] = "unknown"
        result = self.run_replay(rows, registry)
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["desk_packets"][0]["status"], "halt")
        self.assertIn("EVIDENCE_GATE_BLOCK", result["desk_packets"][0]["risk_flags"])

    def test_missing_market_source_registry_entry_blocks_observation(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = self.run_replay(rows, {"instruments": []})
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["desk_packets"][0]["status"], "halt")

    def test_stale_market_observation_blocks_desk(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        rows[0]["source_timestamp_utc"] = "2026-11-17T11:00:00Z"
        rows[0]["received_timestamp_utc"] = "2026-11-17T11:00:00Z"
        result = self.run_replay(rows)
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["desk_packets"][0]["status"], "halt")

    def test_duplicate_instrument_id_halts_coordinator(self):
        rows = [obs("crypto_spot", "DUPLICATE"), obs("crypto_spot", "DUPLICATE")]
        result = self.run_replay(rows)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any("duplicate instrument_id" in e for e in result["occ"]["errors"]))

    def test_invalid_raw_quote_blocks_desk(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        rows[0]["bid"] = 0
        result = self.run_replay(rows)
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["desk_packets"][0]["status"], "halt")

    def test_replay_emits_reproducibility_digests_for_raw_inputs_and_gate_code(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = self.run_replay(rows)
        gate = result["evidence_gate"]
        for key in ("observations_sha256", "market_source_registry_sha256",
                    "gate_implementation_sha256"):
            self.assertRegex(gate[key], r"^[a-f0-9]{64}$")
        implementation = gate["implementation_sha256"]
        self.assertEqual(set(implementation), {
            "replay", "evidence_gate", "specialist_engines", "gold_specialist",
            "capital_flow_handoff", "capital_flow_provenance",
            "capital_flow_priority", "capital_flow_taxonomy", "stop_clearance_review", "portfolio_risk",
        })
        for digest in implementation.values():
            self.assertRegex(digest, r"^[a-f0-9]{64}$")
        self.assertIsNone(gate["capital_flow_inputs_sha256"])
        self.assertEqual(gate["evaluation_time_utc"], NOW)

    def test_capital_flow_input_digests_are_recorded_when_supplied(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        result = self.run_replay(
            rows, capital_flow_events=[flow_event(contract_address="fixture-mint")],
            capital_flow_reviews=[flow_review()],
            capital_flow_source_registry=FLOW_REGISTRY,
        )
        digests = result["evidence_gate"]["capital_flow_inputs_sha256"]
        self.assertEqual(set(digests), {"events", "reviews", "source_registry"})
        for value in digests.values():
            self.assertRegex(value, r"^[a-f0-9]{64}$")

    def test_replay_does_not_accept_a_supplied_gate_report(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        with self.assertRaises(TypeError):
            replay(rows, NOW, source_registry(rows), gate_report={
                "status": "PASS_RESEARCH_GATES",
                "authority": "research_only_no_execution_authority",
            })

    def test_unknown_instrument_type_not_silently_routed(self):
        rows = [obs("unknown_product", "MYSTERY")]
        result = self.run_replay(rows)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(result["occ"]["errors"])


if __name__ == "__main__":
    unittest.main()
