"""Independent checkpoint fixture for replay custody in offline OCC rehearsals."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from threading import Lock
from typing import Protocol


_DOMAIN = b"daivora.occ.receipt-anchor/synthetic-v1\x00"


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return sha256(_DOMAIN + encoded.encode("ascii")).hexdigest()


def custody_digest(trust):
    """Bind the exact company-approved publisher configuration."""
    binding = [
        "custody", trust.company_id, trust.publisher_id, trust.key_id, trust.public_key.hex(),
        trust.source_revision, trust.payload_source_revision, trust.valid_from.isoformat(),
        trust.valid_until.isoformat(), trust.revoked,
    ]
    if trust.divisional_telemetry:
        binding.append("divisional_telemetry_v1")
    return _digest(binding)


@dataclass(frozen=True)
class ReceiptCheckpoint:
    company_id: str
    journal_id: str
    custody_sha256: str
    count: int
    head_sha256: str
    witnessed_enrollment_sha256: str | None = None

    def __post_init__(self):
        if (
            self.company_id not in ("ai_revenue", "trading_technology")
            or not re.fullmatch(r"[a-zA-Z0-9._-]{1,80}", self.journal_id)
            or not all(re.fullmatch(r"[0-9a-f]{64}", digest)
                       for digest in (self.custody_sha256, self.head_sha256))
            or type(self.count) is not int or self.count < 0
            or self.witnessed_enrollment_sha256 is not None
            and not re.fullmatch(r"[0-9a-f]{64}", self.witnessed_enrollment_sha256)
        ):
            raise ValueError("invalid receipt checkpoint")

    @classmethod
    def genesis(cls, company_id, journal_id, custody_sha256):
        return cls(company_id, journal_id, custody_sha256, 0,
                   _digest(["genesis", company_id, journal_id, custody_sha256]))

    def append(self, row):
        company_id, publisher_id, key_id, sequence, snapshot_id, digest = row
        if (
            company_id != self.company_id
            or type(sequence) is not int or sequence < 1
            or not all(isinstance(item, str) for item in (publisher_id, key_id, snapshot_id, digest))
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError("invalid row in anchored receipt history")
        return replace(self, count=self.count + 1,
                       head_sha256=_digest(["receipt", self.head_sha256, list(row)]))


class ReceiptAnchor(Protocol):
    """Independent authority must return the latest committed checkpoint."""

    def read(self, company_id: str) -> ReceiptCheckpoint: ...

    def advance(self, expected: ReceiptCheckpoint, successor: ReceiptCheckpoint) -> None: ...


class FixtureReceiptAnchor:
    """Caller-owned in-memory authority for synthetic tests, separate from SQLite."""

    def __init__(self, scopes):
        self._lock = Lock()
        self._checkpoints = {}
        for company_id, (journal_id, trust) in scopes.items():
            if trust.company_id != company_id or trust.revoked is not False:
                raise ValueError("fixture company and publisher custody do not match")
            self._checkpoints[company_id] = ReceiptCheckpoint.genesis(
                company_id, journal_id, custody_digest(trust),
            )

    def read(self, company_id):
        with self._lock:
            try:
                return self._checkpoints[company_id]
            except KeyError:
                raise ValueError("independent checkpoint unavailable") from None

    def advance(self, expected, successor):
        with self._lock:
            company = expected.company_id
            if (
                self._checkpoints.get(company) != expected
                or successor.company_id != company
                or successor.journal_id != expected.journal_id
                or successor.custody_sha256 != expected.custody_sha256
                or successor.count != expected.count + 1
            ):
                raise ValueError("independent receipt checkpoint conflict")
            self._checkpoints[company] = successor
