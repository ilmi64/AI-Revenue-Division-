"""PostgreSQL owner-approval repository adapter.

Offline-capable DB-API adapter. It expects a psycopg-compatible connection
factory configured with dict_row rows. No connection or credentials are
created here. Owner signature verification happens before issue(); callers
must pass claims from the trusted verifier, never agent-authored claims.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import re
import uuid


class ApprovalRepositoryError(RuntimeError):
    pass


GENESIS = "0" * 64
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = (
    "approval_id", "owner_id", "company_id", "stream_id", "agent_id",
    "session_id", "task_id", "operation", "resource", "policy_version",
    "audience", "nonce", "signer_key_id", "signed_payload_digest",
    "signature_digest",
)


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _unix(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ApprovalRepositoryError(field + "_invalid")
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ApprovalRepositoryError(field + "_out_of_range") from exc


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class PostgresOwnerApprovalRepository:
    """Trusted service adapter; no agent-facing DB access.

    connection_factory must return a psycopg-compatible connection whose
    cursors return mapping rows (for example psycopg.rows.dict_row).
    """

    def __init__(self, *, connection_factory, company_id, audience):
        if not callable(connection_factory) or not _nonempty(company_id) or not _nonempty(audience):
            raise ApprovalRepositoryError("repository_configuration_invalid")
        self._connect = connection_factory
        self._company = company_id
        self._audience = audience

    @contextmanager
    def _transaction(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            finally:
                raise
        finally:
            conn.close()

    @staticmethod
    def _validate_claims(claims, signed_envelope, now):
        if not isinstance(claims, dict):
            raise ApprovalRepositoryError("verified_claims_required")
        if any(not _nonempty(claims.get(k)) for k in REQUIRED):
            raise ApprovalRepositoryError("approval_claims_incomplete")
        if not isinstance(signed_envelope, dict):
            raise ApprovalRepositoryError("signed_envelope_required")
        if claims.get("single_use") is not True:
            raise ApprovalRepositoryError("single_use_required")
        issued = _unix(claims.get("issued_at"), "issued_at")
        expiry = _unix(claims.get("expires_at"), "expires_at")
        _unix(now, "trusted_now")
        if expiry <= issued or expiry <= _unix(now, "trusted_now"):
            raise ApprovalRepositoryError("approval_lifetime_invalid")
        if not HEX64.fullmatch(claims["signed_payload_digest"]):
            raise ApprovalRepositoryError("signed_payload_digest_invalid")
        if not HEX64.fullmatch(claims["signature_digest"]):
            raise ApprovalRepositoryError("signature_digest_invalid")
        if claims.get("intent_digest") is not None and not HEX64.fullmatch(claims["intent_digest"]):
            raise ApprovalRepositoryError("intent_digest_invalid")
        amount = claims.get("amount_minor")
        currency = claims.get("currency")
        if amount is not None:
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                raise ApprovalRepositoryError("amount_minor_invalid")
            if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
                raise ApprovalRepositoryError("currency_invalid")
        elif currency is not None:
            raise ApprovalRepositoryError("amount_currency_pair_invalid")
        try:
            json.dumps(signed_envelope, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ApprovalRepositoryError("signed_envelope_not_json") from exc
        return issued, expiry

    @staticmethod
    def _append_audit(conn, *, company, stream, event_type, occurred_at,
                      approval_id, action_id, payload):
        event_id = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO owner_approval_audit_heads "
                "(company_id,stream_id,last_sequence,head_hash) VALUES (%s,%s,0,%s) "
                "ON CONFLICT (company_id,stream_id) DO NOTHING",
                (company, stream, GENESIS),
            )
            cur.execute(
                "SELECT last_sequence,head_hash FROM owner_approval_audit_heads "
                "WHERE company_id=%s AND stream_id=%s FOR UPDATE",
                (company, stream),
            )
            head = cur.fetchone()
            if not isinstance(head, dict):
                raise ApprovalRepositoryError("audit_head_unavailable")
            sequence = head["last_sequence"] + 1
            previous = head["head_hash"]
            body = {
                "company_id": company, "stream_id": stream,
                "sequence": sequence, "event_id": event_id,
                "event_type": event_type, "occurred_at": occurred_at.isoformat(),
                "approval_id": approval_id, "action_id": action_id,
                "payload": payload, "previous_hash": previous,
            }
            event_hash = _digest(body)
            cur.execute(
                "INSERT INTO owner_approval_audit_events "
                "(company_id,stream_id,sequence,event_id,event_type,occurred_at,"
                "approval_id,action_id,payload,previous_hash,event_hash) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)",
                (company, stream, sequence, event_id, event_type, occurred_at,
                 approval_id, action_id, _canonical(payload), previous, event_hash),
            )
            cur.execute(
                "UPDATE owner_approval_audit_heads SET last_sequence=%s,head_hash=%s "
                "WHERE company_id=%s AND stream_id=%s",
                (sequence, event_hash, company, stream),
            )
        return event_id

    def issue(self, *, claims, signed_envelope, now):
        issued, expiry = self._validate_claims(claims, signed_envelope, now)
        if claims["company_id"] != self._company or claims["audience"] != self._audience:
            raise ApprovalRepositoryError("approval_company_or_audience_mismatch")
        approval_id = str(uuid.UUID(claims["approval_id"]))
        payload = dict(claims)
        with self._transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO owner_approval_records "
                    "(approval_id,company_id,stream_id,owner_id,principal_agent_id,session_id,"
                    "task_id,operation,resource,recipient,intent_digest,amount_minor,currency,"
                    "policy_version,audience,nonce,single_use,issued_at,expires_at,signer_key_id,"
                    "signed_payload_digest,signature_digest,signed_envelope) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s,%s,%s,%s,%s::jsonb)",
                    (approval_id, claims["company_id"], claims["stream_id"], claims["owner_id"],
                     claims["agent_id"], claims["session_id"], claims["task_id"],
                     claims["operation"], claims["resource"], claims.get("recipient"),
                     claims.get("intent_digest"), claims.get("amount_minor"), claims.get("currency"),
                     claims["policy_version"], claims["audience"], claims["nonce"], issued, expiry,
                     claims["signer_key_id"], claims["signed_payload_digest"],
                     claims["signature_digest"], _canonical(signed_envelope)),
                )
            event_id = self._append_audit(
                conn, company=self._company, stream=claims["stream_id"],
                event_type="approval_issued", occurred_at=_unix(now, "trusted_now"),
                approval_id=approval_id, action_id=None,
                payload={"scope_digest": _digest(payload), "nonce": claims["nonce"]},
            )
        return {
            "approval_id": approval_id, "company_id": self._company,
            "scope_digest": claims.get("scope_digest") or _digest(payload),
            "expires_at": claims["expires_at"], "audit_event_id": event_id,
        }

    def revoke(self, *, approval_id, company_id, actor_id, now):
        if company_id != self._company or not _nonempty(actor_id):
            raise ApprovalRepositoryError("revoke_scope_invalid")
        _unix(now, "trusted_now")
        approval_id = str(uuid.UUID(approval_id))
        with self._transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT stream_id,revoked_at FROM owner_approval_records "
                    "WHERE approval_id=%s AND company_id=%s FOR UPDATE",
                    (approval_id, self._company),
                )
                row = cur.fetchone()
                if not isinstance(row, dict):
                    raise ApprovalRepositoryError("approval_not_found")
                if row["revoked_at"] is not None:
                    return False
                cur.execute(
                    "UPDATE owner_approval_records SET revoked_at=%s,revoked_by=%s "
                    "WHERE approval_id=%s AND company_id=%s AND revoked_at IS NULL",
                    (_unix(now, "trusted_now"), actor_id, approval_id, self._company),
                )
            self._append_audit(
                conn, company=self._company, stream=row["stream_id"],
                event_type="approval_revoked", occurred_at=_unix(now, "trusted_now"),
                approval_id=approval_id, action_id=None, payload={"revoked_by": actor_id},
            )
        return True

    def consume_in_transaction(self, conn, *, approval_id, action_id, expected, now):
        """Consume approval inside caller's dispatch/recovery DB transaction.

        This method NEVER commits or rolls back conn. The caller must already
        have locked the authoritative stream/action rows and must append any
        unified dispatch audit/outbox records before committing that same
        transaction. It validates exact approval scope and single-use races.
        """
        if not isinstance(expected, dict) or expected.get("company_id") != self._company:
            raise ApprovalRepositoryError("consumption_scope_invalid")
        _unix(now, "trusted_now")
        approval_id = str(uuid.UUID(approval_id))
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM owner_approval_records WHERE approval_id=%s "
                "AND company_id=%s FOR UPDATE",
                (approval_id, self._company),
            )
            row = cur.fetchone()
            if not isinstance(row, dict):
                raise ApprovalRepositoryError("approval_not_found")
            exact = (
                "company_id", "stream_id", "owner_id", "principal_agent_id",
                "session_id", "task_id", "operation", "resource", "recipient",
                "intent_digest", "policy_version", "audience",
            )
            for key in exact:
                if row.get(key) != expected.get(key):
                    raise ApprovalRepositoryError("approval_" + key + "_mismatch")
            if row.get("revoked_at") is not None:
                raise ApprovalRepositoryError("approval_revoked")
            if row["expires_at"] <= _unix(now, "trusted_now"):
                raise ApprovalRepositoryError("approval_expired")
            if row.get("amount_minor") != expected.get("amount_minor") or row.get("currency") != expected.get("currency"):
                raise ApprovalRepositoryError("approval_amount_or_currency_mismatch")
            try:
                cur.execute(
                    "INSERT INTO owner_approval_consumptions "
                    "(approval_id,company_id,nonce,action_id,consumed_at) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (approval_id, self._company, row["nonce"], action_id,
                     _unix(now, "trusted_now")),
                )
            except Exception as exc:
                raise ApprovalRepositoryError("approval_replay_or_consumption_conflict") from exc
            self._append_audit(
                conn, company=self._company, stream=row["stream_id"],
                event_type="approval_consumed", occurred_at=_unix(now, "trusted_now"),
                approval_id=approval_id, action_id=action_id,
                payload={"nonce": row["nonce"]},
            )
        return {"approval_id": approval_id, "action_id": action_id, "consumed": True}
