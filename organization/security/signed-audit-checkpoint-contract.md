# Signed audit checkpoint and restore-verification contract

Status: proposed offline reference; not production-enforced.

## Checkpoint payload
Each independently signed checkpoint binds:
- company ID and audit stream ID;
- exact event sequence and event hash;
- checkpoint time, schema version and policy version;
- signer key ID; and
- digest of the previous checkpoint in the same company/stream chain.

The signature covers canonical JSON excluding only the signature field. A trusted
key registry determines which signer keys are valid. Workers cannot choose the
signer, trust roots, clock, company/stream binding or registry.

## Acceptance and anti-rollback
The registry verifies signature, signer allowlist, scope and time window before
acceptance. Per company/stream, the first checkpoint must link to the genesis
digest. Later checkpoints must link to the exact previously accepted checkpoint
digest and have a strictly increasing sequence. Exact duplicate delivery is
idempotent; lower sequence, same-sequence conflict, missing predecessor or
wrong chain link is rejected and raises an incident/quarantine condition.

## Restore gate
After restoring a database, the recovery authority must:
1. run database integrity checks and verify every event-chain link;
2. retrieve the latest checkpoint from independently administered immutable
   storage, not solely from the restored database;
3. verify its signature, signer status, company/stream, freshness and chain;
4. require restored sequence and event hash to equal the trusted checkpoint;
5. refresh revocations, emergency-stop state and key status; and
6. keep dispatch disabled until the owner approves release.

A checkpoint older than the trusted external head, a conflicting same-sequence
checkpoint, a missing checkpoint, or a restored stream that does not reach the
exact trusted sequence/hash must quarantine that company stream.

## Reference limitations
The SQLite registry is a local prototype and is not independent WORM storage.
Signer and signature verifier are injected callbacks; the test fixture uses a
deterministic SHA-256 construction and is NOT cryptographic signing. Production
requires Ed25519 or P-256 signatures, private keys in KMS/HSM, independently
administered public-key registry and WORM/object-lock storage, signed registry
receipts, trusted time, key rotation/revocation, multi-node consistency,
backup/restore/failover tests, monitoring and an independent recovery authority.
A hash chain or local checkpoint database alone cannot stop a privileged actor
from rewriting all local state. No trading, wallet, broker, transfer or external
side effect is implemented.
