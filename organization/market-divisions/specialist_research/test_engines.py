import unittest

from specialist_research.engines import (
    assess_crypto, assess_forex, assess_indices, assess_gold, coordinate,
)

NOW = "2026-11-17T12:00:00Z"


def common(kind):
    return {
        "instrument_id": "TEST-INSTRUMENT",
        "instrument_type": kind,
        "venue_or_broker": "SYNTHETIC-ONLY",
        "source_id": "fixture-source",
        "source_timestamp_utc": NOW,
        "received_timestamp_utc": NOW,
        "data_class": "synthetic",
        "licence_status": "not_applicable",
        "currency": "USD",
        "unit_or_contract_multiplier": 1,
        "session_state": "open",
        "portfolio_version": 1,
        "evidence_refs": ["fixture:one"],
    }


class SpecialistEngineTests(unittest.TestCase):
    def test_crypto_rejects_wrong_pair_orientation(self):
        o = common("crypto_spot")
        o.update(base_asset="SOL", quote_asset="USDC", market_pair="USDC/SOL",
                 token_identity_status="verified", currency="USDC")
        p = assess_crypto(o, NOW)
        self.assertEqual(p["status"], "halt")
        self.assertTrue(any("BASE/QUOTE" in x for x in p["data_quality"]["errors"]))

    def test_crypto_accepts_identity_but_warns_missing_liquidity(self):
        o = common("crypto_spot")
        o.update(base_asset="SOL", quote_asset="USDC", market_pair="SOL/USDC",
                 token_identity_status="verified", currency="USDC",
                 chain_id="solana", contract_address="synthetic-mint",
                 liquidity_evidence={"depth": "fixture"})
        p = assess_crypto(o, NOW)
        self.assertEqual(p["status"], "research")
        self.assertFalse(p["trade_authority"])

    def test_crypto_blocks_unverified_token(self):
        o = common("crypto_spot")
        o.update(base_asset="SOL", quote_asset="USDC", market_pair="SOL/USDC",
                 token_identity_status="unverified", currency="USDC")
        self.assertEqual(assess_crypto(o, NOW)["status"], "halt")

    def test_forex_requires_quote_per_base_orientation(self):
        o = common("fx_spot")
        o.update(base_currency="EUR", quote_currency="USD",
                 quote_convention="base_per_quote", currency="USD")
        p = assess_forex(o, NOW)
        self.assertEqual(p["status"], "halt")
        self.assertTrue(any("quote convention" in x for x in p["data_quality"]["errors"]))

    def test_forex_flags_unreviewed_financing(self):
        o = common("fx_spot")
        o.update(base_currency="EUR", quote_currency="USD",
                 quote_convention="quote_per_base", currency="USD",
                 central_bank_evidence=["fixture:ecb"], macro_calendar_evidence=["fixture:calendar"],
                 financing_status="unknown")
        p = assess_forex(o, NOW)
        self.assertEqual(p["status"], "unverified")
        self.assertIn("FINANCING_UNASSESSED", p["risk_flags"])

    def test_indices_cash_identity_must_match_currency(self):
        o = common("index_cash")
        o.update(index_code="SYNTH500", index_calculation_currency="EUR", currency="USD")
        self.assertEqual(assess_indices(o, NOW)["status"], "halt")

    def test_indices_future_requires_contract_and_expiry(self):
        o = common("index_future")
        self.assertEqual(assess_indices(o, NOW)["status"], "halt")

    def test_gold_rejects_basis_type_confusion(self):
        o = common("xauusd_spot")
        o.update(gold_price_basis="comex_futures", gold_session="fixture-session",
                 quote_age_seconds=1, stale_threshold_seconds=30, is_stale=False,
                 financing_status="reviewed", settlement_type="physical")
        self.assertEqual(assess_gold(o, NOW)["status"], "halt")

    def test_gold_rejects_stale_quote(self):
        o = common("xauusd_spot")
        o.update(gold_price_basis="broker_executable_xauusd", gold_session="fixture-session",
                 quote_age_seconds=31, stale_threshold_seconds=30, is_stale=True,
                 financing_status="reviewed", settlement_type="cash")
        self.assertEqual(assess_gold(o, NOW)["status"], "halt")

    def test_gold_flags_unassessed_financing_settlement_and_shariah(self):
        o = common("xauusd_spot")
        o.update(gold_price_basis="broker_executable_xauusd", gold_session="fixture-session",
                 quote_age_seconds=1, stale_threshold_seconds=30, is_stale=False)
        p = assess_gold(o, NOW)
        self.assertEqual(p["status"], "unverified")
        self.assertIn("FINANCING_UNASSESSED", p["risk_flags"])
        self.assertIn("SETTLEMENT_UNASSESSED", p["risk_flags"])
        self.assertIn("SHARIAH_PRODUCT_REVIEW_UNASSESSED", p["risk_flags"])

    def test_gold_basis_requires_two_distinct_aligned_legs(self):
        o = common("xauusd_spot")
        o.update(gold_price_basis="broker_executable_xauusd", gold_session="fixture-session",
                 quote_age_seconds=1, stale_threshold_seconds=30, is_stale=False,
                 financing_status="reviewed", settlement_type="cash",
                 evidence_refs=["fixture:spot", "fixture:future"],
                 spot_futures_basis=2.5,
                 spot_futures_leg_source_ids=["spot-feed", "future-feed"],
                 spot_futures_leg_timestamps_utc=[NOW, "2026-11-17T12:01:00Z"])
        p = assess_gold(o, NOW)
        self.assertEqual(p["status"], "halt")
        self.assertTrue(any("time-aligned" in x for x in p["data_quality"]["errors"]))

    def test_occ_halts_on_desk_stop(self):
        p = assess_crypto(common("crypto_spot"), NOW)
        p["status"] = "halt"
        result = coordinate([p], NOW)
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["halted_desks"], ["crypto"])
        self.assertFalse(result["trade_authority"])

    def test_occ_halts_on_portfolio_version_mismatch(self):
        a = assess_crypto(common("crypto_spot"), NOW)
        b = assess_forex(common("fx_spot"), NOW)
        b["portfolio_version"] = 2
        self.assertEqual(coordinate([a, b], NOW)["status"], "halt")

    def test_occ_rejects_execution_authority_packet(self):
        p = assess_gold(common("xauusd_spot"), NOW)
        p["trade_authority"] = True
        result = coordinate([p], NOW)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
