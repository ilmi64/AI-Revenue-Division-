import unittest
from capital_flow_normalizer import EventError, deduplicate, normalize_event, process_jsonl

TX = "0x" + "a" * 64
BASE = {
    "event_type": "large_wallet_transfer",
    "chain": "Ethereum",
    "asset_id": "usdc",
    "transaction_hash": TX,
    "observed_at": "2026-11-17T10:00:00Z",
    "ingested_at": "2026-11-17T10:01:00+00:00",
    "occurred_at": None,
    "source_ids": ["explorer-a"],
    "evidence_refs": ["https://example.invalid/tx/1"],
    "direction": "unknown",
}

class NormalizerTests(unittest.TestCase):
    def test_normalizes_identifiers_and_preserves_unknowns(self):
        event = normalize_event(BASE, now_epoch=1794910000)
        self.assertEqual(event["chain"], "ethereum")
        self.assertEqual(event["asset_id"], "USDC")
        self.assertIsNone(event["occurred_at_epoch"])
        self.assertIsNone(event["value_usd_estimate"])
        self.assertIn("occurred_at_unknown", event["quality_flags"])
        self.assertIn("attribution_unverified", event["quality_flags"])

    def test_rejects_timezone_naive_timestamp(self):
        raw = dict(BASE, observed_at="2026-11-17T10:00:00")
        with self.assertRaises(EventError):
            normalize_event(raw)

    def test_self_transfer_flag_does_not_claim_direction(self):
        raw = dict(BASE, subject_entity_id="wallet-x", counterparty_entity_id="wallet-x")
        event = normalize_event(raw)
        self.assertIn("possible_self_transfer", event["quality_flags"])
        self.assertEqual(event["direction"], "unknown")

    def test_special_transfer_classes_are_flags_only(self):
        for classification in ("exchange_hot_wallet_reshuffle", "bridge_hop",
                               "wrapped_token_mint_burn", "internal_treasury_move"):
            event = normalize_event(dict(BASE, transfer_classification=classification))
            self.assertIn(classification, event["quality_flags"])

    def test_stale_observation_flag(self):
        event = normalize_event(BASE, now_epoch=1795000000, stale_after_seconds=60)
        self.assertIn("stale_observation", event["quality_flags"])

    def test_duplicate_merges_sources_and_evidence(self):
        first = normalize_event(BASE)
        second = normalize_event(dict(BASE, source_ids=["explorer-b"],
                                      evidence_refs=["https://example.invalid/tx/2"]))
        unique, count = deduplicate([first, second])
        self.assertEqual(count, 1)
        self.assertEqual(unique[0]["source_ids"], ["explorer-a", "explorer-b"])
        self.assertEqual(len(unique[0]["evidence_refs"]), 2)

    def test_duplicate_value_conflict_is_retained_as_conflict(self):
        first = normalize_event(dict(BASE, value_native=10))
        second = normalize_event(dict(BASE, value_native=12))
        unique, count = deduplicate([first, second])
        self.assertEqual(count, 1)
        self.assertIn("duplicate_conflict:value_native", unique[0]["conflicts"])
        self.assertIn("duplicate_conflict", unique[0]["quality_flags"])

    def test_bridge_hop_and_wrapped_token_records_are_not_dropped(self):
        bridge = normalize_event(dict(BASE, event_type="bridge_outflow",
                                      transfer_classification="bridge_hop"))
        wrapped = normalize_event(dict(BASE, event_type="token_distribution",
                                       transfer_classification="wrapped_token_mint_burn"))
        self.assertIn("bridge_hop", bridge["quality_flags"])
        self.assertIn("wrapped_token_mint_burn", wrapped["quality_flags"])

    def test_jsonl_reports_bad_line_without_losing_valid_events(self):
        import json
        good = json.dumps(BASE)
        events, errors, duplicates = process_jsonl([good, "{bad json"])
        self.assertEqual(len(events), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(duplicates, 0)

if __name__ == "__main__":
    unittest.main()
