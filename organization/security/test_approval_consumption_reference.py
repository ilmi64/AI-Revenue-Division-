import unittest
from approval_consumption_reference import Approval, InMemoryApprovalConsumer

def item(**kw):
    d=dict(approval_id="ap-1", nonce="n-1", company_id="revenue", task_id="t-1",
           operation="publish.draft", resource="campaign/1", expires_at=200)
    d.update(kw); return Approval(**d)

class ApprovalConsumptionTests(unittest.TestCase):
    def test_one_time(self):
        s=InMemoryApprovalConsumer(); a=item()
        self.assertTrue(s.consume(a,now=100,company_id="revenue",task_id="t-1",
                                  operation="publish.draft",resource="campaign/1").allowed)
        self.assertEqual(s.consume(a,now=100,company_id="revenue",task_id="t-1",
                                   operation="publish.draft",resource="campaign/1").reason,"replay_detected")
    def test_scope_mismatch(self):
        r=InMemoryApprovalConsumer().consume(item(),now=100,company_id="trading",task_id="t-1",
                                              operation="publish.draft",resource="campaign/1")
        self.assertFalse(r.allowed)
    def test_expired(self):
        r=InMemoryApprovalConsumer().consume(item(),now=200,company_id="revenue",task_id="t-1",
                                              operation="publish.draft",resource="campaign/1")
        self.assertEqual(r.reason,"approval_expired")
    def test_revoked(self):
        s=InMemoryApprovalConsumer(); s.revoke("ap-1")
        self.assertEqual(s.consume(item(),now=100,company_id="revenue",task_id="t-1",
            operation="publish.draft",resource="campaign/1").reason,"approval_revoked")
    def test_cancelled(self):
        s=InMemoryApprovalConsumer(); s.cancel_task("t-1")
        self.assertEqual(s.consume(item(),now=100,company_id="revenue",task_id="t-1",
            operation="publish.draft",resource="campaign/1").reason,"task_cancelled")
    def test_no_owner_approval(self):
        self.assertFalse(InMemoryApprovalConsumer().consume(item(owner_approved=False),now=100,
            company_id="revenue",task_id="t-1",operation="publish.draft",resource="campaign/1").allowed)
    def test_resource_mismatch(self):
        r=InMemoryApprovalConsumer().consume(item(),now=100,company_id="revenue",task_id="t-1",
            operation="publish.draft",resource="campaign/2")
        self.assertEqual(r.reason,"scope_mismatch")
if __name__ == "__main__": unittest.main()
