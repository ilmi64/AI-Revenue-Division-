import unittest

from crypto.polybot.data_quality import DataQualityError, evaluate_candle_quality


START = "2026-11-14T10:00:00Z"
END = "2026-11-14T12:00:00Z"
NOW = "2026-11-14T13:00:00Z"


def candle(hour, *, source="binance_spot", quote="USDT", close="100", complete=True, collected=NOW):
    return {
        "source": source,
        "venue_symbol": "BTCUSDT" if quote == "USDT" else "BTC-USD",
        "base_asset": "BTC",
        "quote_asset": quote,
        "data_type": "candle",
        "event_time": f"2026-11-14T{hour:02d}:00:00+00:00",
        "collected_at": collected,
        "interval": "1h",
        "payload": {"close": close},
        "is_snapshot": False,
        "is_complete": complete,
        "quality_flags": [],
    }


class HistoricalDataQualityTests(unittest.TestCase):
    def evaluate(self, rows, **kwargs):
        return evaluate_candle_quality(
            rows,
            expected_start=START,
            expected_end=END,
            now=NOW,
            **kwargs,
        )

    def test_complete_hourly_history_has_full_coverage(self):
        report = self.evaluate([candle(10), candle(11), candle(12)])
        self.assertEqual(report["expected_candles"], 3)
        self.assertEqual(report["valid_candles"], 3)
        self.assertEqual(report["coverage_percent"], 100.0)
        self.assertTrue(report["usable_for_research"])
        self.assertEqual(report["quote_asset"], "USDT")

    def test_missing_hour_is_reported_as_a_gap(self):
        report = self.evaluate([candle(10), candle(12)])
        self.assertEqual(report["missing_candles"], 1)
        self.assertEqual(report["missing_ranges"], [{
            "start": "2026-11-14T11:00:00+00:00",
            "end": "2026-11-14T11:00:00+00:00",
            "missing_candles": 1,
        }])
        self.assertFalse(report["usable_for_research"])

    def test_duplicate_timestamp_is_counted_and_fails_closed(self):
        report = self.evaluate([candle(10), candle(10), candle(11), candle(12)])
        self.assertEqual(report["duplicate_records"], 1)
        self.assertIn("duplicate_timestamps", report["quality_flags"])
        self.assertFalse(report["usable_for_research"])

    def test_malformed_and_incomplete_records_are_distinguished(self):
        bad = candle(11)
        bad["payload"]["close"] = "NaN"
        report = self.evaluate([candle(10), bad, candle(12, complete=False)])
        self.assertEqual(report["malformed_records"], 1)
        self.assertEqual(report["incomplete_candles"], 1)
        self.assertEqual(report["valid_candles"], 1)
        self.assertFalse(report["usable_for_research"])

    def test_stale_and_future_collection_times_fail_closed(self):
        stale = self.evaluate([candle(10, collected="2026-11-14T10:00:00Z"), candle(11, collected="2026-11-14T10:00:00Z"), candle(12, collected="2026-11-14T10:00:00Z")])
        self.assertTrue(stale["freshness"]["stale"])
        self.assertFalse(stale["usable_for_research"])
        future = self.evaluate([candle(10, collected="2026-11-14T14:00:00Z")])
        self.assertTrue(future["freshness"]["future_collection_time"])
        self.assertFalse(future["usable_for_research"])

    def test_out_of_window_and_mixed_provenance_are_flagged(self):
        outside = candle(9)
        mixed = candle(11, source="coinbase_exchange", quote="USD")
        report = self.evaluate([candle(10), outside, mixed])
        self.assertEqual(report["out_of_window_records"], 1)
        self.assertEqual(report["malformed_records"], 1)
        self.assertFalse(report["usable_for_research"])

    def test_unusual_cross_venue_divergence_is_a_review_flag_not_a_signal(self):
        comparisons = [
            {"event_time": "t1", "return_difference_percentage_points": "0.2"},
            {"event_time": "t2", "return_difference_percentage_points": "-1.8"},
            {"event_time": "t3", "return_difference_percentage_points": "0.1"},
        ]
        report = self.evaluate(
            [candle(10), candle(11), candle(12)],
            comparison_rows=comparisons,
            divergence_threshold_percentage_points=1.0,
            minimum_comparison_samples=3,
        )
        self.assertEqual(len(report["comparison"]["divergence_flags"]), 1)
        self.assertTrue(report["comparison"]["divergence_flags"][0]["review_required"])
        self.assertIn("not a trade signal", report["comparison"]["divergence_flags"][0]["interpretation"])

    def test_insufficient_comparison_samples_are_flagged(self):
        report = self.evaluate(
            [candle(10), candle(11), candle(12)],
            comparison_rows=[{"return_difference_percentage_points": "0.1"}],
            minimum_comparison_samples=3,
        )
        self.assertTrue(report["comparison"]["insufficient_samples"])
        self.assertFalse(report["usable_for_research"])

    def test_invalid_window_boundaries_are_rejected(self):
        with self.assertRaises(DataQualityError):
            evaluate_candle_quality(
                [], expected_start="2026-11-14T10:15:00Z",
                expected_end=END, now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
