import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_finance_controls import build_report

REGISTRY={"divisions":[{"id":"finance"},{"id":"crypto"}]}
POLICY={"status":"active_zero_spend_control","currency_default":"CAD","approved_spend_ceiling_cad":0,
"incremental_spend_cad":0,"paid_services_enabled":False,"paid_apis_enabled":False,"paid_trials_enabled":False,
"payment_statuses":["not_due","unpaid","partially_paid","paid","disputed","void"],
"approval_statuses":["not_requested","pending","approved","rejected"],
"halal_review_statuses":["not_assessed","requires_review","reviewed_with_advisory_source","not_applicable"],
"halal_safeguards":{"status":"screening_policy_not_a_religious_ruling"}}

class FinanceControlsTests(unittest.TestCase):
 def report(self, commitments=None, ledger=None, policy=None):
  return build_report(policy or POLICY, commitments or [], ledger or [], REGISTRY)
 def test_empty_registers_are_valid_but_not_bank_evidence(self):
  r=self.report()
  self.assertEqual(r["status"],"validated")
  self.assertFalse(r["revenue"]["independently_verified_bank_balance"])
  self.assertEqual(r["approved_spend_ceiling_cad"],"0.00")
 def test_zero_spend_ceiling_rejects_positive_commitment(self):
  row={"id":"C1","division_id":"finance","currency":"CAD","estimated_amount":"10","approved_amount":"10","committed_amount":"10","paid_amount":"0","payment_status":"unpaid","approval_status":"approved","approval_reference":"owner-decision-1"}
  r=self.report([row])
  self.assertEqual(r["status"],"invalid")
  self.assertTrue(any("CAD 0 approved ceiling" in e for e in r["errors"]))
 def test_paid_amount_requires_proof(self):
  policy=dict(POLICY,approved_spend_ceiling_cad=100,incremental_spend_cad=100)
  row={"id":"C2","division_id":"finance","currency":"CAD","approved_amount":"10","committed_amount":"10","paid_amount":"5","payment_status":"partially_paid","approval_status":"approved","approval_reference":"owner-decision-2"}
  r=self.report([row],policy=policy)
  self.assertTrue(any("proof_reference" in e for e in r["errors"]))
 def test_committed_cannot_exceed_approved(self):
  policy=dict(POLICY,approved_spend_ceiling_cad=100,incremental_spend_cad=100)
  row={"id":"C3","division_id":"finance","currency":"CAD","approved_amount":"5","committed_amount":"7","paid_amount":"0","payment_status":"unpaid","approval_status":"approved","approval_reference":"owner-decision-3"}
  r=self.report([row],policy=policy)
  self.assertTrue(any("exceeds approved" in e for e in r["errors"]))
 def test_aggregate_commitments_cannot_exceed_ceiling(self):
  policy=dict(POLICY,approved_spend_ceiling_cad=10,incremental_spend_cad=10)
  rows=[]
  for i in range(2):
   rows.append({"id":f"AG{i}","division_id":"finance","currency":"CAD","approved_amount":"8","committed_amount":"8","paid_amount":"0","payment_status":"unpaid","approval_status":"approved","approval_reference":f"decision-{i}"})
  r=self.report(rows,policy=policy)
  self.assertTrue(any("Aggregate committed CAD amount" in e for e in r["errors"]))
 def test_non_cad_positive_commitment_requires_fx_review(self):
  policy=dict(POLICY,approved_spend_ceiling_cad=100,incremental_spend_cad=100)
  row={"id":"USD1","division_id":"finance","currency":"USD","approved_amount":"5","committed_amount":"5","paid_amount":"0","payment_status":"unpaid","approval_status":"approved","approval_reference":"decision-usd"}
  r=self.report([row],policy=policy)
  self.assertTrue(any("non-CAD commitments require documented FX" in e for e in r["errors"]))
 def test_non_cad_is_not_silently_converted(self):
  row={"id":"C4","division_id":"finance","currency":"USD","estimated_amount":"100","approved_amount":"0","committed_amount":"0","paid_amount":"0","payment_status":"not_due","approval_status":"not_requested"}
  r=self.report([row])
  self.assertTrue(any("excluded from CAD totals" in w for w in r["warnings"]))
 def test_sensitive_financial_activity_is_flagged_for_review(self):
  row={"id":"C5","division_id":"crypto","activity_type":"yield","currency":"CAD","estimated_amount":"1","approved_amount":"0","committed_amount":"0","paid_amount":"0","payment_status":"not_due","approval_status":"not_requested","halal_review_status":"not_assessed"}
  r=self.report([row])
  self.assertEqual(r["halal_screening"]["flagged_sensitive_activity_count"],1)
 def test_received_cash_uses_only_received_statuses(self):
  ledger=[{"payment_status":"not_due","currency":"CAD","net_received_cad":"50"},{"payment_status":"settled","currency":"CAD","net_received_cad":"12","proof_reference":"receipt-1"}]
  r=self.report(ledger=ledger)
  self.assertEqual(r["revenue"]["cash_received_cad_by_ledger_status"],"12.00")
 def test_received_revenue_without_proof_is_excluded_and_invalid(self):
  ledger=[{"payment_status":"received","currency":"CAD","net_received_cad":"75"}]
  r=self.report(ledger=ledger)
  self.assertEqual(r["revenue"]["cash_received_cad_by_ledger_status"],"0.00")
  self.assertTrue(any("requires proof_reference" in e for e in r["errors"]))
 def test_non_cad_received_revenue_is_not_silently_converted(self):
  ledger=[{"payment_status":"settled","currency":"USD","net_received_cad":"75","proof_reference":"receipt-usd"}]
  r=self.report(ledger=ledger)
  self.assertEqual(r["revenue"]["cash_received_cad_by_ledger_status"],"0.00")
  self.assertTrue(any("non-CAD cash receipt" in e for e in r["errors"]))
 def test_malformed_division_registry_fails_closed_without_crashing(self):
  r=build_report(POLICY, [], [], {"divisions":"invalid"})
  self.assertEqual(r["status"],"invalid")
  self.assertTrue(any("divisions must be a list" in e for e in r["errors"]))
 def test_duplicate_commitment_id_is_rejected(self):
  row={"id":"DUP","division_id":"finance","currency":"CAD","estimated_amount":"0","approved_amount":"0","committed_amount":"0","paid_amount":"0","payment_status":"not_due","approval_status":"not_requested"}
  r=self.report([row,row])
  self.assertTrue(any("unique non-empty id" in e for e in r["errors"]))
 def test_halal_review_requires_source_and_notes(self):
  row={"id":"C6","division_id":"crypto","activity_type":"trading","currency":"CAD","estimated_amount":"0","approved_amount":"0","committed_amount":"0","paid_amount":"0","payment_status":"not_due","approval_status":"not_requested","halal_review_status":"reviewed_with_advisory_source"}
  r=self.report([row])
  self.assertTrue(any("source reference and reviewer notes" in e for e in r["errors"]))

if __name__=="__main__":unittest.main()
