import unittest
from decimal import Decimal
from unit_economics import calculate

BASE={
 "sku":"SKU-1","currency":"CAD","selling_price":"40.00","buyer_shipping_collected":"5.00",
 "product_cost":"18.00","fulfilment_shipping_cost":"8.00","marketplace_fee_pct":"13",
 "payment_fee_pct":"2.9","fixed_order_fees":"0.30","packaging_cost":"1.00","other_variable_costs":"0"
}

class UnitEconomicsTests(unittest.TestCase):
 def test_contribution_calculates_all_order_costs(self):
  r=calculate(BASE)
  self.assertTrue(r["valid"])
  self.assertEqual(r["gross_order_revenue"],"45.00")
  self.assertEqual(r["marketplace_fee"],"5.85")
  self.assertEqual(r["payment_fee"],"1.31")
  self.assertEqual(r["total_variable_cost"],"34.46")
  self.assertEqual(r["contribution_before_ads_tax_and_overhead"],"10.54")
 def test_negative_cost_is_rejected(self):
  row=dict(BASE,product_cost="-1")
  r=calculate(row)
  self.assertFalse(r["valid"])
  self.assertTrue(any("finite non-negative" in e for e in r["errors"]))
 def test_fee_rate_over_100_is_rejected(self):
  r=calculate(dict(BASE,marketplace_fee_pct="101"))
  self.assertFalse(r["valid"])
  self.assertTrue(any("cannot exceed 100" in e for e in r["errors"]))
 def test_invalid_currency_is_rejected(self):
  self.assertFalse(calculate(dict(BASE,currency="CAD$"))["valid"])
 def test_zero_contribution_has_zero_ad_budget(self):
  row=dict(BASE,product_cost="40",fulfilment_shipping_cost="10",marketplace_fee_pct="0",payment_fee_pct="0",fixed_order_fees="0",packaging_cost="0")
  r=calculate(row)
  self.assertEqual(r["break_even_ad_spend_per_order"],"0.00")
 def test_missing_columns_are_reported(self):
  r=calculate({"sku":"SKU-2"})
  self.assertFalse(r["valid"])
  self.assertTrue(any("missing required column" in e for e in r["errors"]))

if __name__=="__main__": unittest.main()
