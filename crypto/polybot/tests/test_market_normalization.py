import unittest

from crypto.polybot.market_normalization import (
    MarketDataValidationError,
    compare_price_observations,
    freshness_status,
    normalize_binance_klines,
    normalize_last_price,
    normalize_order_book_snapshot,
)


COLLECTED = "2026-11-14T15:00:00Z"


def candle(open_ms=1794661200000, close_ms=1794664799999, **changes):
    row = [open_ms, "100", "110", "90", "105", "12", close_ms, "0", 1, "0", "0", "0"]
    for index, value in changes.items():
        row[int(index)] = value
    return row


class MarketNormalizationTests(unittest.TestCase):
    def test_candle_keeps_source_and_quote_provenance_and_utc(self):
        rows = normalize_binance_klines(
            [candle()], symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT",
            interval="1h", collected_at=COLLECTED,
        )
        self.assertEqual(len(rows), 1)
        item = rows[0]
        self.assertEqual(item["source"], "binance_spot")
        self.assertEqual(item["quote_asset"], "USDT")
        self.assertTrue(item["event_time"].endswith("+00:00"))
        self.assertEqual(item["payload"]["close"], "105")

    def test_unfinished_candle_is_excluded_by_default(self):
        self.assertEqual(normalize_binance_klines(
            [candle(close_ms=1794668400000)], symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", interval="1h", collected_at=COLLECTED,
        ), [])

    def test_unfinished_candle_can_be_retained_but_marked(self):
        rows = normalize_binance_klines(
            [candle(close_ms=1794668400000)], symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", interval="1h", collected_at=COLLECTED,
            include_unfinished=True,
        )
        self.assertFalse(rows[0]["is_complete"])

    def test_duplicate_candle_rejected(self):
        with self.assertRaises(MarketDataValidationError):
            normalize_binance_klines(
                [candle(), candle()], symbol="BTCUSDT", base_asset="BTC",
                quote_asset="USDT", interval="1h", collected_at=COLLECTED,
            )

    def test_malformed_ohlcv_rejected(self):
        with self.assertRaises(MarketDataValidationError):
            normalize_binance_klines(
                [candle(**{"2": "80"})], symbol="BTCUSDT", base_asset="BTC",
                quote_asset="USDT", interval="1h", collected_at=COLLECTED,
            )
        with self.assertRaises(MarketDataValidationError):
            normalize_binance_klines(
                [candle(**{"5": "-1"})], symbol="BTCUSDT", base_asset="BTC",
                quote_asset="USDT", interval="1h", collected_at=COLLECTED,
            )

    def test_malformed_row_and_timestamp_rejected(self):
        with self.assertRaises(MarketDataValidationError):
            normalize_binance_klines(
                [[1, "2"]], symbol="BTCUSDT", base_asset="BTC",
                quote_asset="USDT", interval="1h", collected_at=COLLECTED,
            )
        with self.assertRaises(MarketDataValidationError):
            normalize_binance_klines(
                [candle(open_ms="bad")], symbol="BTCUSDT", base_asset="BTC",
                quote_asset="USDT", interval="1h", collected_at=COLLECTED,
            )

    def test_naive_collection_time_rejected(self):
        with self.assertRaises(MarketDataValidationError):
            normalize_last_price(
                source="binance_spot", venue_symbol="BTCUSDT", base_asset="BTC",
                quote_asset="USDT", price="100", collected_at="2026-11-14T15:00:00",
            )

    def test_ticker_does_not_fabricate_event_time(self):
        item = normalize_last_price(
            source="binance_spot", venue_symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", price="100", collected_at=COLLECTED,
        )
        self.assertIsNone(item["event_time"])
        self.assertIn("missing_event_time", item["quality_flags"])

    def test_stale_and_future_collection_times_fail_closed(self):
        item = normalize_last_price(
            source="binance_spot", venue_symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", price="100", collected_at=COLLECTED,
        )
        stale = freshness_status(item, now="2026-11-14T15:02:00Z", max_age_seconds=30)
        self.assertFalse(stale["available"])
        future = freshness_status(item, now="2026-11-14T14:59:00Z", max_age_seconds=30)
        self.assertFalse(future["available"])

    def test_order_book_is_snapshot_not_order_flow(self):
        item = normalize_order_book_snapshot(
            source="binance_spot", venue_symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", book={"lastUpdateId": 7, "bids": [["99", "1"]], "asks": [["101", "2"]]},
            collected_at=COLLECTED,
        )
        self.assertTrue(item["is_snapshot"])
        self.assertIn("not_synchronized_order_flow", item["quality_flags"])
        self.assertEqual(item["payload"]["lastUpdateId"], 7)

    def test_price_comparison_discloses_quote_mismatch_and_is_not_spread(self):
        left = normalize_last_price(
            source="coinbase_exchange", venue_symbol="BTC-USD", base_asset="BTC",
            quote_asset="USD", price="65000", collected_at=COLLECTED,
        )
        right = normalize_last_price(
            source="binance_spot", venue_symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", price="65100", collected_at="2026-11-14T15:00:10Z",
        )
        result = compare_price_observations(left, right)
        self.assertFalse(result["quote_assets_match"])
        self.assertFalse(result["executable_spread"])
        self.assertTrue(result["comparable_in_time"])
        self.assertEqual(result["relative_quote_price_difference_percent"], str((__import__("decimal").Decimal("65100") - __import__("decimal").Decimal("65000")) / __import__("decimal").Decimal("65000") * 100))

    def test_comparison_rejects_stale_time_alignment_and_other_data_types(self):
        left = normalize_last_price(
            source="coinbase_exchange", venue_symbol="BTC-USD", base_asset="BTC",
            quote_asset="USD", price="65000", collected_at=COLLECTED,
        )
        right = normalize_last_price(
            source="binance_spot", venue_symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", price="65100", collected_at="2026-11-14T15:02:00Z",
        )
        self.assertFalse(compare_price_observations(left, right)["comparable_in_time"])
        right["data_type"] = "candle"
        with self.assertRaises(MarketDataValidationError):
            compare_price_observations(left, right)


if __name__ == "__main__":
    unittest.main()
