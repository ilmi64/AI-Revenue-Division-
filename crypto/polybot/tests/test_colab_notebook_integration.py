import json
import unittest
from pathlib import Path


class ColabNotebookIntegrationTests(unittest.TestCase):
    def test_cross_venue_cell_is_valid_python_and_keeps_phase3_separate(self):
        repo_root = Path(__file__).resolve().parents[3]
        notebook_path = repo_root / "Polybot_Development.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        sources = [
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        ]

        original_phase3 = next(
            (source for source in sources if "PHASE 3: MARKET INTELLIGENCE" in source),
            None,
        )
        integration = next(
            (source for source in sources if "PHASE 3B: CROSS-VENUE COMPARISON" in source),
            None,
        )

        self.assertIsNotNone(original_phase3, "Original Coinbase collector must remain present")
        self.assertIsNotNone(integration, "Separate cross-venue cell must be present")
        compile(integration, str(notebook_path), "exec")
        self.assertIn("get_klines", integration)
        self.assertIn("normalize_coinbase_candles", integration)
        self.assertIn("normalize_binance_klines", integration)
        self.assertIn("from crypto.polybot.data_quality import evaluate_candle_quality", integration)
        self.assertIn("coinbase_quality = evaluate_candle_quality", integration)
        self.assertIn("binance_quality = evaluate_candle_quality", integration)
        self.assertIn("data_quality_hourly.csv", integration)
        self.assertIn("Pairs with quality reports", integration)
        self.assertIn("No orders or transactions", integration)


if __name__ == "__main__":
    unittest.main()
