import tempfile
import unittest
from pathlib import Path

from listing_preflight import Finding, validate_csv, validate_rows


class ListingPreflightTests(unittest.TestCase):
    def test_valid_rows_pass(self):
        rows = [{
            "sku": "MO-001", "title": "Black graphic tee",
            "price": "24.99", "quantity": "5", "shipping": "6.50",
        }]
        self.assertEqual(validate_rows(rows), [])

    def test_duplicate_sku_and_invalid_values_are_reported(self):
        rows = [
            {"sku": "A1", "title": "First", "price": "10", "quantity": "2", "shipping": "0"},
            {"sku": "A1", "title": "Second", "price": "0", "quantity": "-1", "shipping": "-2"},
        ]
        findings = validate_rows(rows)
        messages = [item.message for item in findings]
        self.assertTrue(any("Duplicate SKU" in message for message in messages))
        self.assertTrue(any("greater than zero" in message for message in messages))
        self.assertTrue(any("zero or greater" in message for message in messages))

    def test_fractional_quantity_is_rejected(self):
        rows = [{
            "sku": "A1", "title": "Item", "price": "1.00",
            "quantity": "1.5", "shipping": "0",
        }]
        self.assertTrue(any(
            "whole number" in item.message for item in validate_rows(rows)
        ))

    def test_missing_column_is_reported(self):
        rows = [{"sku": "A1", "title": "Item", "price": "5", "quantity": "1"}]
        findings = validate_rows(rows)
        self.assertTrue(any(
            item.row == 1 and item.field == "shipping" for item in findings
        ))

    def test_custom_column_names_work(self):
        rows = [{
            "SKU Code": "A1", "Product Name": "Item",
            "Sale Price": "8.50", "Stock": "3", "Postage": "2",
        }]
        findings = validate_rows(
            rows, sku_field="SKU Code", title_field="Product Name",
            price_field="Sale Price", quantity_field="Stock",
            shipping_field="Postage",
        )
        self.assertEqual(findings, [])

    def test_csv_file_with_utf8_bom_is_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.csv"
            path.write_text(
                "\ufeffsku,title,price,quantity,shipping\nA1,Item,10,2,0\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_csv(path), [])


if __name__ == "__main__":
    unittest.main()
