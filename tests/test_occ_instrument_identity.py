"""Tests for canonical OCC instrument identity validation."""
import unittest

from occ.instrument_identity import (
    InstrumentIdentityError,
    validate_instrument_identity,
)


def identity(**overrides):
    value = {
        "market_class": "METALS",
        "product_type": "SPOT",
        "venue": "ExampleVenue",
        "symbol": "XAUUSD",
        "base_currency": "XAU",
        "quote_currency": "USD",
        "contract_unit": "troy_ounce",
        "settlement_method": "UNKNOWN",
    }
    value.update(overrides)
    return value


class InstrumentIdentityTests(unittest.TestCase):
    def test_xauusd_spot_keeps_unknown_custody_and_financing(self):
        result = validate_instrument_identity(identity())
        self.assertEqual(result["symbol"], "XAUUSD")
        self.assertEqual(result["custody_model"], "UNKNOWN")
        self.assertEqual(result["financing_model"], "UNKNOWN")
        self.assertFalse(result["ownership_verified"])
        self.assertFalse(result["execution_eligible"])

    def test_future_requires_expiry(self):
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(identity(product_type="FUTURE"))

    def test_future_accepts_explicit_expiry(self):
        result = validate_instrument_identity(
            identity(product_type="FUTURE", expiry="2027-02")
        )
        self.assertEqual(result["expiry"], "2027-02")

    def test_spot_rejects_futures_expiry(self):
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(identity(expiry="2027-02"))

    def test_quote_currency_is_mandatory(self):
        value = identity()
        del value["quote_currency"]
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(value)

    def test_contract_unit_is_mandatory(self):
        value = identity()
        del value["contract_unit"]
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(value)

    def test_invalid_symbol_is_rejected(self):
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(identity(symbol="XAU USD"))

    def test_non_finite_contract_multiplier_is_rejected(self):
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(identity(contract_multiplier=float("inf")))

    def test_boolean_contract_multiplier_is_rejected(self):
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(identity(contract_multiplier=True))

    def test_unknown_custody_is_not_inferred_as_allocated(self):
        result = validate_instrument_identity(identity())
        self.assertNotEqual(result["custody_model"], "ALLOCATED")

    def test_unknown_settlement_does_not_claim_delivery(self):
        result = validate_instrument_identity(identity())
        self.assertEqual(result["settlement_method"], "UNKNOWN")

    def test_source_mapping_is_not_mutated(self):
        source = identity()
        before = dict(source)
        validate_instrument_identity(source)
        self.assertEqual(source, before)

    def test_fx_spot_requires_base_currency(self):
        value = identity(market_class="FOREX", product_type="FX_SPOT", symbol="EURUSD")
        del value["base_currency"]
        with self.assertRaises(InstrumentIdentityError):
            validate_instrument_identity(value)

    def test_fx_spot_with_base_currency_is_valid(self):
        result = validate_instrument_identity(
            identity(market_class="FOREX", product_type="FX_SPOT",
                     symbol="EURUSD", base_currency="EUR",
                     quote_currency="USD", contract_unit="one_euro")
        )
        self.assertEqual(result["base_currency"], "EUR")


if __name__ == "__main__":
    unittest.main()
