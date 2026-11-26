"""Exact-scope signed recovery for interrupted, process-owned fixture reservations."""
from dataclasses import asdict, dataclass, replace
import os
from pathlib import Path
from typing import Mapping, Protocol
from uuid import UUID

from evidence_verifier import VerificationBlocked
from revenue_fixture_dispatch import canonical
from signed_audit_continuity import ContinuityKey, _verify_signature


_COMPANY = "ai_revenue"
_SUPERVISOR_ROLE = "ar_cto"
_WITNESS_ROLE = "sr_backup_recovery"
_MAX_FRESHNESS_SECONDS = 120
_IN_PROCESS_ONLY = frozenset({"coding", "ai_setup", "authorized_bug_bounty"})


@dataclass(frozen=True)
class ProcessIdentity:
    boot_id: str
    pid_namespace: str
    effective_uid: int
    pid: int
    start_ticks: int


@dataclass(frozen=True)
class ReservationClaim:
    company_id: str
    request_id: str
    request_sha256: str
    claim_until: int
    owner: ProcessIdentity


@dataclass(frozen=True)
class RecoverySignature:
    key_id: str
    signature: bytes


@dataclass(frozen=True)
class RecoveryAuthorization:
    claim: ReservationClaim
    trust_epoch: int
    observed_at: int
    expires_at: int
    supervisor: RecoverySignature
    witness: RecoverySignature


@dataclass(frozen=True)
class CurrentRecoveryTrust:
    company_id: str
    trust_epoch: int
    observed_at: int
    expires_at: int
    keys: Mapping[str, ContinuityKey]


class RecoveryAuthority(Protocol):
    """Provision current trusted signers outside both the request and database."""

    def current(self, company_id: str) -> CurrentRecoveryTrust: ...


def in_process_recovery_allowed(service: str) -> bool:
    """The app fixture subprocess requires separate descendant custody proof."""
    return service in _IN_PROCESS_ONLY


def _proc_identity(pid: int) -> ProcessIdentity:
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    fields = stat.rpartition(") ")[2].split()
    start_ticks = int(fields[19])
    return ProcessIdentity(
        str(UUID(Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip())),
        os.readlink("/proc/self/ns/pid"), os.geteuid(), pid, start_ticks,
    )


def capture_process_identity() -> ProcessIdentity:
    try:
        return _proc_identity(os.getpid())
    except (OSError, ValueError, IndexError, AttributeError) as exc:
        raise VerificationBlocked("fixture_process_identity_unavailable") from exc


def _kernel_pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (OSError, ValueError, OverflowError) as exc:
        raise VerificationBlocked("fixture_process_exit_unverified") from exc
    return True


def require_original_process_gone(owner: ProcessIdentity) -> None:
    local = capture_process_identity()
    if (
        not isinstance(owner, ProcessIdentity) or type(owner.pid) is not int
        or not 0 < owner.pid < 2**31 or type(owner.start_ticks) is not int or owner.start_ticks < 0
        or owner.boot_id != local.boot_id or owner.pid_namespace != local.pid_namespace
        or owner.effective_uid != local.effective_uid
    ):
        raise VerificationBlocked("fixture_process_identity_scope_mismatch")
    if not _kernel_pid_exists(owner.pid):
        return
    try:
        current = _proc_identity(owner.pid)
    except FileNotFoundError:
        if not _kernel_pid_exists(owner.pid):
            return
        raise VerificationBlocked("fixture_process_exit_unverified") from None
    except (OSError, ValueError, IndexError) as exc:
        raise VerificationBlocked("fixture_process_exit_unverified") from exc
    if current == owner:
        raise VerificationBlocked("fixture_claimant_still_present")
    if current.start_ticks <= owner.start_ticks:
        raise VerificationBlocked("fixture_process_exit_unverified")


def recovery_payload(authorization: RecoveryAuthorization, role: str, key_id: str) -> bytes:
    return canonical({
        "purpose": "aevora-scheduler-reservation-recovery-v1",
        "claim": asdict(authorization.claim),
        "trust_epoch": authorization.trust_epoch,
        "observed_at": authorization.observed_at,
        "expires_at": authorization.expires_at,
        "role": role,
        "key_id": key_id,
    })


def _fresh_window(observed_at: int, expires_at: int, now: int) -> bool:
    return (
        type(observed_at) is int and type(expires_at) is int
        and 0 <= observed_at <= now < expires_at
        and expires_at - observed_at <= _MAX_FRESHNESS_SECONDS
    )


def _read_authority(authority: RecoveryAuthority) -> CurrentRecoveryTrust:
    try:
        current = authority.current(_COMPANY)
        if not isinstance(current, CurrentRecoveryTrust) or not isinstance(current.keys, Mapping):
            raise VerificationBlocked("fixture_recovery_authority_unavailable")
        return replace(current, keys=dict(current.keys))
    except (OSError, RuntimeError) as exc:
        raise VerificationBlocked("fixture_recovery_authority_unavailable") from exc


def verify_recovery(
    authorization: RecoveryAuthorization, claim: ReservationClaim,
    authority: RecoveryAuthority | None, now: int,
) -> dict:
    if not isinstance(authorization, RecoveryAuthorization) or authorization.claim != claim:
        raise VerificationBlocked("fixture_recovery_claim_mismatch")
    if authority is None:
        raise VerificationBlocked("fixture_recovery_authority_unavailable")
    current = _read_authority(authority)
    if (
        current.company_id != _COMPANY
        or type(current.trust_epoch) is not int or current.trust_epoch <= 0
        or type(authorization.trust_epoch) is not int or authorization.trust_epoch != current.trust_epoch
        or not _fresh_window(current.observed_at, current.expires_at, now)
        or not _fresh_window(authorization.observed_at, authorization.expires_at, now)
        or authorization.observed_at < claim.claim_until
    ):
        raise VerificationBlocked("fixture_recovery_trust_stale_or_out_of_scope")

    signers = []
    for role, attestation in ((_SUPERVISOR_ROLE, authorization.supervisor), (_WITNESS_ROLE, authorization.witness)):
        if not isinstance(attestation, RecoverySignature) or not isinstance(attestation.key_id, str):
            raise VerificationBlocked("invalid_fixture_recovery_attestation")
        key = current.keys.get(attestation.key_id)
        if (
            not isinstance(key, ContinuityKey) or key.company_id != _COMPANY or key.purpose != role
            or not isinstance(key.principal_id, str) or not key.principal_id.strip()
            or key.revoked is not False or type(key.expires_at) is not int
            or authorization.expires_at > min(key.expires_at, current.expires_at)
        ):
            raise VerificationBlocked("untrusted_fixture_recovery_signer")
        _verify_signature(key.public_key, attestation.signature, recovery_payload(authorization, role, attestation.key_id))
        signers.append(key)
    if (
        signers[0].principal_id.strip().casefold() == signers[1].principal_id.strip().casefold()
        or signers[0].public_key == signers[1].public_key
    ):
        raise VerificationBlocked("fixture_recovery_roles_not_independent")
    require_original_process_gone(claim.owner)
    if _read_authority(authority) != current:
        raise VerificationBlocked("fixture_recovery_authority_changed")
    return {
        "claim": asdict(claim),
        "trust_epoch": authorization.trust_epoch,
        "observed_at": authorization.observed_at,
        "expires_at": authorization.expires_at,
        "supervisor_key_id": authorization.supervisor.key_id,
        "supervisor_signature": authorization.supervisor.signature.hex(),
        "witness_key_id": authorization.witness.key_id,
        "witness_signature": authorization.witness.signature.hex(),
        "release_authorized": False,
    }
