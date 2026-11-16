"""Offline structural tests for the draft organisation risk policy."""
import json
import unittest
from pathlib import Path

from validate_risk_controls import POLICY_PATH, validate


class RiskPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_current_policy_passes_structural_checks(self):
        self.assertEqual(validate(self.policy), [])

    def test_live_trading_cannot_be_enabled(self):
        changed = json.loads(json.dumps(self.policy))
        changed["trading_controls"]["live_execution_enabled"] = True
        self.assertTrue(any("live_execution_enabled" in e for e in validate(changed)))

    def test_risk_cannot_gain_trade_authority(self):
        changed = json.loads(json.dumps(self.policy))
        changed["authority"]["risk_division"] = "approve_trades"
        self.assertTrue(any("risk authority" in e for e in validate(changed)))

    def test_stale_data_stop_cannot_be_disabled(self):
        changed = json.loads(json.dumps(self.policy))
        changed["market_data_controls"]["fail_closed_on_stale_data"] = False
        self.assertTrue(any("fail_closed_on_stale_data" in e for e in validate(changed)))

    def test_missing_owner_approval_gate_fails(self):
        changed = json.loads(json.dumps(self.policy))
        changed["mandatory_owner_approval"].remove("wallet_actions")
        self.assertTrue(any("approval" in e for e in validate(changed)))

    def test_production_source_cannot_be_approved_by_draft_policy(self):
        changed = json.loads(json.dumps(self.policy))
        changed["market_data_controls"]["production_sources_approved"] = ["example-feed"]
        self.assertTrue(any("no production market-data source" in e for e in validate(changed)))

    def test_secret_denylist_is_mandatory(self):
        changed = json.loads(json.dumps(self.policy))
        changed["never_request_or_store"].remove("seed_phrases")
        self.assertTrue(any("secret-handling" in e for e in validate(changed)))


if __name__ == "__main__":
    unittest.main()
