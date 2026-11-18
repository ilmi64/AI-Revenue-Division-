"""Synthetic tests for explicit contract lifecycle replay."""
import unittest

from specialist_research.contract_lifecycle import (
    AUTHORITY, replay_contract_lifecycle, validate_contract_profile,
)


def profile(kind="gold_future"):
    return {
        "schema_version": "1.0.0", "profile_id": "synthetic-gold",
        "venue_id": "synthetic-venue", "instrument_id": "XAU-DEC",
        "instrument_type": kind, "quote_currency": "USD",
        "settlement_currency": "USD", "settlement_method": "cash",
        "roll_method": "manual_close_open", "financing_convention": "none",
        "contract_code": "GCZ6", "expiry_utc": "2026-12-28T18:30:00Z",
    }


def successor_profile(contract_code, expiry_utc, profile_id=None):
    value = profile()
    value["profile_id"] = profile_id or f"synthetic-gold-{contract_code}"
    value["contract_code"] = contract_code
    value["expiry_utc"] = expiry_utc
    return value


def position(**overrides):
    value = {
        "position_id": "pos-1", "instrument_id": "XAU-DEC",
        "side": "long", "quantity": 2.0, "contract_id": "GCZ6",
    }
    value.update(overrides)
    return value


class ContractLifecycleTests(unittest.TestCase):
    def test_valid_future_profile(self):
        self.assertEqual(validate_contract_profile(profile()), [])

    def test_missing_expiry_blocks_future(self):
        value = profile()
        del value["expiry_utc"]
        self.assertTrue(validate_contract_profile(value))

    def test_roll_updates_contract_and_cashflow(self):
        result = replay_contract_lifecycle(profile(), position(), [{
            "event_id": "roll-1", "event_type": "roll",
            "timestamp_utc": "2026-11-20T15:00:00Z",
            "old_contract_id": "GCZ6", "new_contract_id": "GCG7",
            "old_reference_price": 4200.0, "new_reference_price": 4220.0,
            "cash_adjustment": -5.0, "currency": "USD",
            "new_contract_profile": successor_profile("GCG7", "2027-02-28T18:30:00Z"),
        }])
        self.assertEqual(result["status"], "LIFECYCLE_REPLAYED")
        self.assertEqual(result["ending_contract_id"], "GCG7")
        self.assertEqual(result["cashflow_total"], -5.0)

    def test_roll_requires_a_valid_successor_contract_profile(self):
        result = replay_contract_lifecycle(profile(), position(), [{
            "event_type": "roll", "timestamp_utc": "2026-11-20T15:00:00Z",
            "old_contract_id": "GCZ6", "new_contract_id": "GCG7",
            "old_reference_price": 4200.0, "new_reference_price": 4220.0,
            "cash_adjustment": 0.0, "currency": "USD",
        }])
        self.assertEqual(result["status"], "BLOCKED_INVALID_EVENT_SEQUENCE")
        self.assertTrue(any("new_contract_profile" in item for item in result["errors"]))

    def test_roll_rejects_successor_profile_with_wrong_contract_code(self):
        next_profile = successor_profile("WRONG", "2027-02-28T18:30:00Z")
        result = replay_contract_lifecycle(profile(), position(), [{
            "event_type": "roll", "timestamp_utc": "2026-11-20T15:00:00Z",
            "old_contract_id": "GCZ6", "new_contract_id": "GCG7",
            "old_reference_price": 4200.0, "new_reference_price": 4220.0,
            "cash_adjustment": 0.0, "currency": "USD",
            "new_contract_profile": next_profile,
        }])
        self.assertEqual(result["status"], "BLOCKED_INVALID_EVENT_SEQUENCE")
        self.assertTrue(any("contract_code" in item for item in result["errors"]))

    def test_successor_profile_controls_later_roll_expiry_window(self):
        result = replay_contract_lifecycle(profile(), position(), [
            {
                "event_type": "roll", "timestamp_utc": "2026-11-20T15:00:00Z",
                "old_contract_id": "GCZ6", "new_contract_id": "GCG7",
                "old_reference_price": 4200.0, "new_reference_price": 4220.0,
                "cash_adjustment": 0.0, "currency": "USD",
                "new_contract_profile": successor_profile("GCG7", "2027-02-28T18:30:00Z"),
            },
            {
                "event_type": "roll", "timestamp_utc": "2027-01-10T15:00:00Z",
                "old_contract_id": "GCG7", "new_contract_id": "GCH7",
                "old_reference_price": 4220.0, "new_reference_price": 4230.0,
                "cash_adjustment": 0.0, "currency": "USD",
                "new_contract_profile": successor_profile("GCH7", "2027-03-31T18:30:00Z"),
            },
        ])
        self.assertEqual(result["status"], "LIFECYCLE_REPLAYED")
        self.assertEqual(result["ending_contract_id"], "GCH7")

    def test_roll_wrong_old_contract_blocks(self):
        result = replay_contract_lifecycle(profile(), position(), [{
            "event_type": "roll", "timestamp_utc": "2026-11-20T15:00:00Z",
            "old_contract_id": "WRONG", "new_contract_id": "GCG7",
            "old_reference_price": 4200.0, "new_reference_price": 4220.0,
            "cash_adjustment": 0.0, "currency": "USD",
        }])
        self.assertEqual(result["status"], "BLOCKED_INVALID_EVENT_SEQUENCE")

    def test_settlement_requires_expiry_and_matching_contract(self):
        result = replay_contract_lifecycle(profile(), position(), [{
            "event_id": "settle-1", "event_type": "expiry_settlement",
            "timestamp_utc": "2026-12-28T18:31:00Z",
            "contract_id": "GCZ6", "settlement_price": 4250.0,
            "settlement_method": "cash", "realized_cashflow": 100.0,
            "currency": "USD",
        }])
        self.assertEqual(result["status"], "SETTLED")
        self.assertEqual(result["ending_quantity"], 0.0)
        self.assertEqual(result["cashflow_total"], 100.0)

    def test_settlement_before_expiry_blocks(self):
        result = replay_contract_lifecycle(profile(), position(), [{
            "event_type": "expiry_settlement",
            "timestamp_utc": "2026-12-20T18:31:00Z",
            "contract_id": "GCZ6", "settlement_price": 4250.0,
            "settlement_method": "cash", "realized_cashflow": 100.0,
            "currency": "USD",
        }])
        self.assertEqual(result["status"], "BLOCKED_INVALID_EVENT_SEQUENCE")

    def test_cannot_append_after_settlement(self):
        events = [{
            "event_type": "expiry_settlement",
            "timestamp_utc": "2026-12-28T18:31:00Z",
            "contract_id": "GCZ6", "settlement_price": 4250.0,
            "settlement_method": "cash", "realized_cashflow": 100.0,
            "currency": "USD",
        }, {
            "event_type": "roll", "timestamp_utc": "2026-12-28T18:32:00Z",
            "old_contract_id": "GCZ6", "new_contract_id": "GCG7",
            "old_reference_price": 4250.0, "new_reference_price": 4260.0,
            "cash_adjustment": 0.0, "currency": "USD",
        }]
        result = replay_contract_lifecycle(profile(), position(), events)
        self.assertEqual(result["status"], "BLOCKED_INVALID_EVENT_SEQUENCE")

    def test_perpetual_requires_funding_convention(self):
        value = {
            "schema_version": "1.0.0", "profile_id": "p", "venue_id": "v",
            "instrument_id": "BTC-PERP", "instrument_type": "crypto_perpetual",
            "quote_currency": "USD", "settlement_currency": "USD",
            "settlement_method": "not_applicable", "roll_method": "not_applicable",
            "financing_convention": "none",
        }
        self.assertTrue(validate_contract_profile(value))

    def test_funding_rate_event_requires_perpetual_profile(self):
        value = {
            "schema_version": "1.0.0", "profile_id": "p", "venue_id": "v",
            "instrument_id": "BTC-PERP", "instrument_type": "crypto_perpetual",
            "quote_currency": "USD", "settlement_currency": "USD",
            "settlement_method": "not_applicable", "roll_method": "not_applicable",
            "financing_convention": "funding_rate",
        }
        pos = position(instrument_id="BTC-PERP", contract_id="BTC-PERP")
        result = replay_contract_lifecycle(value, pos, [{
            "event_type": "funding", "timestamp_utc": "2026-11-20T15:00:00Z",
            "cashflow": -2.5, "currency": "USD",
        }])
        self.assertEqual(result["status"], "LIFECYCLE_REPLAYED")
        self.assertEqual(result["cashflow_total"], -2.5)

    def test_signed_rate_cashflow_is_not_inverted_for_short_positions(self):
        for side in ("long", "short"):
            result = replay_contract_lifecycle(
                {
                    "schema_version": "1.0.0", "profile_id": "p", "venue_id": "v",
                    "instrument_id": "EUR_USD", "instrument_type": "forex_cfd",
                    "quote_currency": "USD", "settlement_currency": "USD",
                    "settlement_method": "broker_cash_adjustment",
                    "roll_method": "venue_defined", "financing_convention": "daily_rate",
                },
                position(instrument_id="EUR_USD", contract_id="EUR_USD", side=side),
                [{
                    "event_type": "financing", "timestamp_utc": "2026-11-20T15:00:00Z",
                    "rate": -0.01, "notional": 100.0, "basis_units": 1.0,
                    "currency": "USD",
                }],
            )
            self.assertEqual(result["status"], "LIFECYCLE_REPLAYED")
            self.assertEqual(result["cashflow_total"], -1.0)

    def test_event_time_must_increase(self):
        events = [{
            "event_type": "roll", "timestamp_utc": "2026-11-20T15:00:00Z",
            "old_contract_id": "GCZ6", "new_contract_id": "GCG7",
            "old_reference_price": 4200.0, "new_reference_price": 4220.0,
            "cash_adjustment": 0.0, "currency": "USD",
            "new_contract_profile": successor_profile("GCG7", "2027-02-28T18:30:00Z"),
        }, {
            "event_type": "roll", "timestamp_utc": "2026-11-20T14:00:00Z",
            "old_contract_id": "GCG7", "new_contract_id": "GCH7",
            "old_reference_price": 4220.0, "new_reference_price": 4230.0,
            "cash_adjustment": 0.0, "currency": "USD",
            "new_contract_profile": successor_profile("GCH7", "2027-03-31T18:30:00Z"),
        }]
        result = replay_contract_lifecycle(profile(), position(), events)
        self.assertEqual(result["status"], "BLOCKED_INVALID_EVENT_SEQUENCE")

    def test_authority_remains_research_only(self):
        result = replay_contract_lifecycle(profile(), position(), [])
        self.assertEqual(result["authority"], AUTHORITY)
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertTrue(result["simulation_only"])


if __name__ == "__main__":
    unittest.main()
