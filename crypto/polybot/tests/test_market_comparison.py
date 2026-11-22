import unittest

from crypto.polybot.market_normalization import (
    MarketDataValidationError,
    compare_candle_series,
    normalize_binance_klines,
    normalize_coinbase_candles,
)

COLLECTED = "2026-11-14T15:00:00Z"
T1 = "1794661200000"
T2 = "1794664800000"


def binance_row(open_ms, close_ms, close):
    return [open_ms, "100", "120", "90", close, "10", close_ms, "0", 1, "0", "0", "0"]


class CrossVenueComparisonTests(unittest.TestCase):
    def test_coinbase_normalizer_preserves_usd_source_and_timestamp(self):
        rows = normalize_coinbase_candles(
            [{"timestamp": "2026-11-14T13:00:00Z", "open": "100", "high": "110",
              "low": "90", "close": "105", "volume": "2"}],
            pair="BTC-USD", interval="1h", collected_at=COLLECTED,
        )
        self.assertEqual(rows[0]["source"], "coinbase_exchange")
        self.assertEqual(rows[0]["quote_asset"], "USD")
        self.assertEqual(rows[0]["event_time"], "2026-11-14T13:00:00+00:00")

    def test_aligned_series_compares_returns_without_merging_quote_currencies(self):
        coinbase = normalize_coinbase_candles(
            [
                {"timestamp": "2026-11-14T13:00:00Z", "open": "100", "high": "110", "low": "90", "close": "100", "volume": "2"},
                {"timestamp": "2026-11-14T14:00:00Z", "open": "100", "high": "120", "low": "95", "close": "110", "volume": "3"},
            ],
            pair="BTC-USD", interval="1h", collected_at=COLLECTED,
        )
        binance = normalize_binance_klines(
            [
                binance_row(int(T1), int(T1) + 3599999, "100"),
                binance_row(int(T2), int(T2) + 3599999, "108"),
            ],
            symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT",
            interval="1h", collected_at=COLLECTED,
        )
        report = compare_candle_series(coinbase, binance)
        self.assertEqual(len(report), 2)
        self.assertIsNone(report[0]["return_difference_percentage_points"])
        self.assertEqual(report[1]["left_return_percent"], "10.0")
        self.assertEqual(report[1]["right_return_percent"], "8.00")
        self.assertEqual(report[1]["return_difference_percentage_points"], "-2.00")
        self.assertFalse(report[1]["price_levels_comparable"])
        self.assertEqual(report[1]["left_quote_asset"], "USD")
        self.assertEqual(report[1]["right_quote_asset"], "USDT")

    def test_comparison_rejects_different_assets_or_intervals(self):
        left = normalize_coinbase_candles(
            [{"timestamp": "2026-11-14T13:00:00Z", "open": "100", "high": "110", "low": "90", "close": "105", "volume": "2"}],
            pair="BTC-USD", interval="1h", collected_at=COLLECTED,
        )
        right = normalize_coinbase_candles(
            [{"timestamp": "2026-11-14T13:00:00Z", "open": "100", "high": "110", "low": "90", "close": "105", "volume": "2"}],
            pair="ETH-USD", interval="1h", collected_at=COLLECTED,
        )
        with self.assertRaises(MarketDataValidationError):
            compare_candle_series(left, right)
        right[0]["base_asset"] = "BTC"
        right[0]["interval"] = "15m"
        with self.assertRaises(MarketDataValidationError):
            compare_candle_series(left, right)

    def test_comparison_rejects_unfinished_candles(self):
        left = normalize_coinbase_candles(
            [{"timestamp": "2026-11-14T13:00:00Z", "open": "100", "high": "110", "low": "90", "close": "105", "volume": "2"}],
            pair="BTC-USD", interval="1h", collected_at=COLLECTED,
        )
        right = normalize_binance_klines(
            [binance_row(int(T1), int(T1) + 3599999, "105")],
            symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT",
            interval="1h", collected_at=COLLECTED,
        )
        right[0]["is_complete"] = False
        with self.assertRaises(MarketDataValidationError):
            compare_candle_series(left, right)


if __name__ == "__main__":
    unittest.main()
