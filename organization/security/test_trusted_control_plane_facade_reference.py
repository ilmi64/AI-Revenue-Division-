"""Offline tests for the trusted control-plane façade reference."""
import unittest
from trusted_control_plane_facade_reference import (
    TrustedControlPlaneError, TrustedControlPlaneFacade,
)


class Clock:
    def now(self): return 100


class IdentityVerifier:
    def __init__(self, result=None, error=None): self.result=result; self.error=error
    def verify(self, assertion, *, expected, now):
        if self.error: raise self.error
        if expected != {"company_id":"revenue","audience":"runtime"} or now != 100:
            raise AssertionError("unexpected identity verification scope")
        return self.result


class Scheduler:
    def __init__(self, result=None, error=None): self.result=result; self.error=error
    def resolve_approval_scope(self, *, task_id, company_id, now):
        if self.error: raise self.error
        if task_id != "task-1" or company_id != "revenue" or now != 100:
            raise AssertionError("unexpected approval task lookup")
        return task_claims()
    def resolve(self, *, task_reference, principal, now):
        if self.error: raise self.error
        if task_reference != "task-ref" or principal.agent_id != "agent-1" or now != 100:
            raise AssertionError("unexpected trusted task lookup")
        return self.result


class OwnerVerifier:
    def __init__(self, result=None, error=None): self.result=result; self.error=error
    def verify(self, envelope, *, expected, now):
        if self.error: raise self.error
        if expected != {"company_id":"revenue","audience":"owner-approval","single_use":True} or now != 100:
            raise AssertionError("unexpected approval verification scope")
        return self.result


class ApprovalRepository:
    def __init__(self, result=None, error=None): self.result=result; self.error=error; self.calls=[]
    def issue(self, *, claims, signed_envelope, now):
        self.calls.append((claims,signed_envelope,now))
        if self.error: raise self.error
        return self.result


def principal_claims(**overrides):
    value={"agent_id":"agent-1","company_id":"revenue","role":"researcher",
           "session_id":"session-1","runtime_id":"runtime-1","identity_epoch":3,
           "issued_at":90,"expires_at":200}
    value.update(overrides); return {"verified":True,"claims":value}


def task_claims(**overrides):
    value={"task_id":"task-1","company_id":"revenue","assigned_agent_id":"agent-1",
           "stream_id":"research","allowed_operations":{"research.read"},
           "allowed_resources":{"market/public"},"policy_version":"p7","expires_at":180}
    value.update(overrides); return value


def approval_claims(**overrides):
    value={"owner_id":"owner-1","company_id":"revenue","stream_id":"research",
           "agent_id":"agent-1","session_id":"session-1","task_id":"task-1",
           "operation":"report.create","resource":"reports/daily",
           "policy_version":"p7","nonce":"nonce-1","audience":"owner-approval",
           "approval_id":"approval-1","scope_digest":"a"*64,"single_use":True,
           "issued_at":95,"expires_at":150}
    value.update(overrides); return {"verified":True,"claims":value}


def make_facade(*, identity=None, task=None, owner=None, repository=None, clock=None):
    return TrustedControlPlaneFacade(
        company_id="revenue", identity_audience="runtime",
        approval_audience="owner-approval", trusted_owner_ids={"owner-1"},
        clock=clock or Clock(),
        identity_verifier=IdentityVerifier(identity or principal_claims()),
        task_scheduler=Scheduler(task or task_claims()),
        owner_approval_verifier=OwnerVerifier(owner or approval_claims()),
        approval_repository=repository or ApprovalRepository({
            "approval_id":"approval-1","company_id":"revenue",
            "scope_digest":"a"*64,"expires_at":150,"audit_event_id":"audit-1"}),
    )


class TrustedFacadeTests(unittest.TestCase):
    def test_resolves_verified_principal_and_task(self):
        result=make_facade().resolve_principal_and_task(
            identity_assertion={"signed":"identity"},task_reference="task-ref")
        self.assertEqual(result.principal.agent_id,"agent-1")
        self.assertEqual(result.task.task_id,"task-1")
        self.assertEqual(result.resolved_at,100)

    def test_unverified_identity_denied(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"identity_not_verified"):
            make_facade(identity={"verified":False}).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_identity_company_mismatch_denied(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"identity_company_mismatch"):
            make_facade(identity=principal_claims(company_id="other")).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_expired_identity_denied(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"identity_expired_or_invalid"):
            make_facade(identity=principal_claims(expires_at=100)).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_missing_identity_epoch_denied(self):
        claims=principal_claims(); claims["claims"].pop("identity_epoch")
        with self.assertRaisesRegex(TrustedControlPlaneError,"identity_epoch_invalid"):
            make_facade(identity=claims).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_task_assignment_mismatch_denied(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"task_assignment_or_company_mismatch"):
            make_facade(task=task_claims(assigned_agent_id="agent-2")).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_expired_task_denied(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"task_expired_or_invalid"):
            make_facade(task=task_claims(expires_at=100)).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_task_scope_must_be_nonempty(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"task_scope_invalid"):
            make_facade(task=task_claims(allowed_operations=set())).resolve_principal_and_task(
                identity_assertion={},task_reference="task-ref")

    def test_approval_requires_trusted_owner(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"owner_not_in_trusted_registry"):
            make_facade(owner=approval_claims(owner_id="intruder")).issue_owner_approval(
                owner_signed_envelope={})

    def test_approval_scope_must_be_single_use(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"approval_must_be_single_use"):
            make_facade(owner=approval_claims(single_use=False)).issue_owner_approval(
                owner_signed_envelope={})

    def test_amount_requires_currency(self):
        with self.assertRaisesRegex(TrustedControlPlaneError,"amount_requires_nonnegative_minor_units_and_currency"):
            make_facade(owner=approval_claims(amount_minor=500)).issue_owner_approval(
                owner_signed_envelope={})

    def test_approval_must_match_trusted_task_assignment(self):
        facade=TrustedControlPlaneFacade(
            company_id="revenue", identity_audience="runtime", approval_audience="owner-approval",
            trusted_owner_ids={"owner-1"}, clock=Clock(),
            identity_verifier=IdentityVerifier(principal_claims()),
            task_scheduler=Scheduler(task_claims(assigned_agent_id="agent-2")),
            owner_approval_verifier=OwnerVerifier(approval_claims()),
            approval_repository=ApprovalRepository({}))
        with self.assertRaisesRegex(TrustedControlPlaneError,"approval_task_scope_mismatch"):
            facade.issue_owner_approval(owner_signed_envelope={})

    def test_approval_operation_must_be_in_task_scope(self):
        facade=TrustedControlPlaneFacade(
            company_id="revenue", identity_audience="runtime", approval_audience="owner-approval",
            trusted_owner_ids={"owner-1"}, clock=Clock(),
            identity_verifier=IdentityVerifier(principal_claims()),
            task_scheduler=Scheduler(task_claims(allowed_operations={"research.read"})),
            owner_approval_verifier=OwnerVerifier(approval_claims()),
            approval_repository=ApprovalRepository({}))
        with self.assertRaisesRegex(TrustedControlPlaneError,"approval_outside_task_scope"):
            facade.issue_owner_approval(owner_signed_envelope={})

    def test_valid_owner_approval_persisted(self):
        repo=ApprovalRepository({"approval_id":"approval-1","company_id":"revenue",
            "scope_digest":"a"*64,"expires_at":150,"audit_event_id":"audit-1"})
        receipt=make_facade(repository=repo).issue_owner_approval(owner_signed_envelope={"signed":"owner"})
        self.assertEqual(receipt.approval_id,"approval-1")
        self.assertEqual(len(repo.calls),1)
        self.assertEqual(repo.calls[0][1],{"signed":"owner"})
        self.assertEqual(repo.calls[0][2],100)

    def test_invalid_repository_receipt_denied(self):
        repo=ApprovalRepository({"approval_id":"wrong","company_id":"revenue",
            "scope_digest":"a"*64,"expires_at":150,"audit_event_id":"audit-1"})
        with self.assertRaisesRegex(TrustedControlPlaneError,"approval_repository_scope_mismatch"):
            make_facade(repository=repo).issue_owner_approval(owner_signed_envelope={})

    def test_clock_failure_fails_closed(self):
        class BadClock:
            def now(self): return "100"
        with self.assertRaisesRegex(TrustedControlPlaneError,"trusted_clock_invalid"):
            make_facade(clock=BadClock()).issue_owner_approval(owner_signed_envelope={})


if __name__ == "__main__":
    unittest.main()
