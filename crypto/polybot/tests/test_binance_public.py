import json
import unittest
from unittest.mock import patch

from crypto.polybot import binance_public as client


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class BinancePublicClientTests(unittest.TestCase):
    @patch("crypto.polybot.binance_public.urlopen")
    def test_price_uses_public_host_and_no_auth(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"symbol": "BTCUSDT", "price": "65000.00"})
        result = client.get_price("BTCUSDT")
        self.assertEqual(result["price"], "65000.00")
        request = mock_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.startswith("https://data-api.binance.vision/"))
        self.assertNotIn("X-MBX-APIKEY", request.headers)

    @patch("crypto.polybot.binance_public.urlopen")
    def test_24h_ticker_schema(self, mock_urlopen):
        payload = {
            "symbol": "ETHUSDT",
            "priceChangePercent": "-2.5",
            "lastPrice": "1800",
            "volume": "1000",
            "quoteVolume": "1800000",
        }
        mock_urlopen.return_value = FakeResponse(payload)
        self.assertEqual(client.get_24h_ticker("ETHUSDT")["symbol"], "ETHUSDT")

    @patch("crypto.polybot.binance_public.urlopen")
    def test_klines_shape_and_parameters(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse([[1, "1", "2", "0.5", "1.5", "10"]])
        result = client.get_klines("BTCUSDT", interval="15m", limit=1)
        self.assertEqual(len(result), 1)
        request = mock_urlopen.call_args.args[0]
        self.assertIn("interval=15m", request.full_url)
        self.assertIn("limit=1", request.full_url)

    @patch("crypto.polybot.binance_public.urlopen")
    def test_order_book_shape(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"lastUpdateId": 10, "bids": [["1", "2"]], "asks": [["2", "3"]]})
        result = client.get_order_book("BTCUSDT", limit=5)
        self.assertEqual(result["lastUpdateId"], 10)

    def test_rejects_invalid_symbol_interval_and_limits(self):
        with self.assertRaises(ValueError):
            client.get_price("btc-usdt")
        with self.assertRaises(ValueError):
            client.get_klines("BTCUSDT", interval="2w")
        with self.assertRaises(ValueError):
            client.get_klines("BTCUSDT", limit=1001)
        with self.assertRaises(ValueError):
            client.get_order_book("BTCUSDT", limit=7)

    @patch("crypto.polybot.binance_public.urlopen")
    def test_rejects_unexpected_price_schema(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"symbol": "ETHUSDT", "price": "100"})
        with self.assertRaises(client.BinanceMarketDataError):
            client.get_price("BTCUSDT")


if __name__ == "__main__":
    unittest.main()
