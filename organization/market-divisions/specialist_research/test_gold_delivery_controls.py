"""Synthetic tests for GC/MGC delivery and FCM deadline gates."""
import unittest

from specialist_research.gold_delivery_controls import assess_gold_delivery_controls


def contract():
    return {
        "product_code": "GC", "rulebook_chapter": "113", "settlement_type": "physical",
        "contract_id": "GCZ26", "contract_month": "2026-12",
        "exchange_calendar_revision_id": "cme-calendar-r1",
        "fcm_policy_revision_id": "broker-policy-r1",
        "exchange_calendar_source_ref": "official-calendar-ref",
        "fcm_policy_source_ref": "broker-policy-ref", "fcm_timezone": "America/New_York",
        "first_position_date": "2026-11-27", "first_notice_date": "2026-11-30",
        "last_trade_date": "2026-12-29", "delivery_start_date": "2026-12-01",
        "delivery_end_date": "2026-12-31",
        "fcm_long_position_cutoff_date": "2026-11-25",
        "fcm_short_position_cutoff_date": "2026-12-28", "last_intent_date": "2026-12-30",
        "new_position_freeze_date": "2026-11-24",
        "fcm_long_cutoff_utc": "2026-11-25T17:00:00Z",
        "fcm_short_cutoff_utc": "2026-12-28T17:00:00Z",
        "new_position_freeze_utc": "2026-11-24T17:00:00Z",
    }


class GoldDeliveryControlTests(unittest.TestCase):
    def test_valid_pre_delivery_flat_state(self):
        result = assess_gold_delivery_controls(contract(), {"side": "flat", "is_open": False}, "2026-11-20T12:00:00Z")
        self.assertEqual(result["status"], "DELIVERY_CONTROLS_CLEAR")
        self.assertFalse(result["trade_authority"])

    def test_long_position_after_fcm_receive_cutoff_blocks(self):
        result = assess_gold_delivery_controls(contract(), {"side": "long", "is_open": True, "contracts": 1}, "2026-11-26T12:00:00Z")
        self.assertEqual(result["status"], "HALT_DELIVERY_CONTROLS")
        self.assertIn("LONG_POSITION_AT_OR_AFTER_FCM_RECEIVE_CUTOFF", result["blocks"])

    def test_short_position_after_fcm_delivery_cutoff_blocks(self):
        result = assess_gold_delivery_controls(contract(), {"side": "short", "is_open": True, "contracts": 1}, "2026-12-29T12:00:00Z")
        self.assertIn("SHORT_POSITION_AT_OR_AFTER_FCM_DELIVERY_CUTOFF", result["blocks"])

    def test_new_position_after_freeze_blocks(self):
        result = assess_gold_delivery_controls(contract(), {"side": "flat", "is_open": False}, "2026-11-25T12:00:00Z")
        self.assertIn("NEW_POSITION_PROHIBITED_BY_FCM_FREEZE", result["blocks"])

    def test_first_notice_and_delivery_period_are_warned(self):
        result = assess_gold_delivery_controls(contract(), {"side": "long", "is_open": True}, "2026-12-02T12:00:00Z")
        self.assertIn("FIRST_NOTICE_DATE_REACHED", result["warnings"])
        self.assertIn("PHYSICAL_DELIVERY_POSITION_PERIOD_REACHED", result["warnings"])

    def test_mismatched_rulebook_chapter_fails_closed(self):
        item = contract()
        item["rulebook_chapter"] = "120"
        result = assess_gold_delivery_controls(item, {"side": "flat", "is_open": False}, "2026-11-20T12:00:00Z")
        self.assertEqual(result["status"], "HALT_DELIVERY_CONTROLS")

    def test_missing_fcm_cutoff_fails_closed(self):
        item = contract()
        del item["fcm_long_cutoff_utc"]
        result = assess_gold_delivery_controls(item, {"side": "flat", "is_open": False}, "2026-11-20T12:00:00Z")
        self.assertEqual(result["status"], "HALT_DELIVERY_CONTROLS")

    def test_inconsistent_exchange_and_fcm_dates_fail_closed(self):
        item = contract()
        item["fcm_long_position_cutoff_date"] = "2026-12-02"
        result = assess_gold_delivery_controls(item, {"side": "flat", "is_open": False}, "2026-11-20T12:00:00Z")
        self.assertEqual(result["status"], "HALT_DELIVERY_CONTROLS")

    def test_mgc_requires_chapter_120(self):
        item = contract()
        item["product_code"] = "MGC"
        item["rulebook_chapter"] = "120"
        result = assess_gold_delivery_controls(item, {"side": "flat", "is_open": False}, "2026-11-20T12:00:00Z")
        self.assertEqual(result["status"], "DELIVERY_CONTROLS_CLEAR")

    def test_mgc_delivery_lot_multiple_of_ten_is_enforced(self):
        item = contract()
        item["product_code"] = "MGC"
        item["rulebook_chapter"] = "120"
        result = assess_gold_delivery_controls(item, {"side": "long", "is_open": True, "contracts": 1}, "2026-11-20T12:00:00Z")
        self.assertIn("MGC_DELIVERY_QUANTITY_MUST_BE_MULTIPLE_OF_TEN_EXCEPT_LAST_INTENT_DAY", result["blocks"])

    def test_mgc_ten_contract_delivery_quantity_passes_lot_rule(self):
        item = contract()
        item["product_code"] = "MGC"
        item["rulebook_chapter"] = "120"
        result = assess_gold_delivery_controls(item, {"side": "long", "is_open": True, "contracts": 10}, "2026-11-20T12:00:00Z")
        self.assertNotIn("MGC_DELIVERY_QUANTITY_MUST_BE_MULTIPLE_OF_TEN_EXCEPT_LAST_INTENT_DAY", result["blocks"])

    def test_no_delivery_action_or_authority(self):
        result = assess_gold_delivery_controls(contract(), {"side": "flat", "is_open": False}, "2026-11-20T12:00:00Z")
        self.assertFalse(result["delivery_instructions_submitted"])
        self.assertFalse(result["position_changed"])
        self.assertFalse(result["live_readiness"])


if __name__ == "__main__":
    unittest.main()
