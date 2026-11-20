# Linearizable Control Store Threat Model

Status: proposed architecture review; not an implementation certification.

## Scope
This threat model covers the company-scoped control store, identity and policy gateway, owner approvals, transactional outbox, recovery authority, audit chain, and the receiver boundary. It applies independently to AI Revenue and Trading & Technology. It does not authorize installation, deployment, live trading, or external dispatch.

## Assets to protect
- Company identity, role, task assignment, session and scoped credentials.
- Owner approvals, one-time nonces, revocation state and approval-consumption records.
- Immutable action intent, recipient/account binding, amount/currency limits and idempotency keys.
- Recovery state, monotonic recovery epoch, emergency-stop state and dispatch status.
- Audit events, signed checkpoints, recovery assessments and receiver evidence.
- Company-private data, budgets, ledgers, customer information and Trading risk controls.

## Security principals and trust boundaries
1. Owner approval authority: independently authenticates the owner and signs exact, time-bounded approvals.
2. Identity issuer: authenticates agents/runtimes and issues short-lived, audience-bound identities.
3. Deterministic policy gateway: evaluates current policy and trusted identity/task context; model output is never authority.
4. Company control store: authoritative transactional state for that company only.
5. Recovery authority: independent assessor and release-verification authority; cannot silently approve its own release.
6. Dispatcher: untrusted worker; receives only a narrow, single-action dispatch capability.
7. External receiver: must enforce stable idempotency and, where supported, recovery-epoch fencing.
8. OCC: summary/health visibility by default; no implicit access to company secrets, approvals, ledgers or risk controls.

## Threat actors and failure sources
- Prompt injection, malicious documents, poisoned market data and hostile tool output.
- Compromised or misconfigured agent, model runtime, orchestration platform or worker.
- Forged, replayed, expired, revoked or cross-company identity/approval claims.
- Concurrent workers, duplicate messages, stale leases and delayed network delivery.
- Process crash, host restart, database lock/error, partial restore or clock/key-service outage.
- Privileged database/operator compromise, backup tampering or signing-key compromise.
- Malicious or buggy receiver; ambiguous timeout after a remote side effect.
- Insider misuse or accidental overbroad permission/configuration.

## Required security properties
- Default deny; fail closed on missing, stale, contradictory or unavailable authority.
- No model, agent, Paperclip task metadata or Ruflo plan can mint identity, approval, policy or recovery authority.
- Company identity and records remain isolated; cross-company access requires a separately authenticated, owner-approved, scoped, expiring grant.
- Owner approval binds exact company, principal, session, task, operation, resource/recipient, amount and currency where relevant, policy version, expiry and one-time nonce.
- Approval consumption, dispatch-start transition and audit append share one transaction boundary.
- Quarantine and dispatch authorization serialize against the same authoritative company-stream state; quarantine advances the epoch.
- Old task leases and authorizations cannot become valid after recovery release.
- Unknown external outcomes are quarantined for reconciliation; never blindly resend.
- Trading live orders, wallet signing, transfers, withdrawals, broker/exchange orders and risk-control modification remain hard-denied in this architecture stage.
- Audit integrity is independently anchored; hash chaining alone is not tamper-proof.

## Principal attack scenarios and mandatory controls
| Scenario | Required control | Evidence required before production |
|---|---|---|
| Prompt injection asks an agent to transfer funds | Model output treated as untrusted request; gateway denies absent exact owner approval | Adversarial prompt-injection tests at every tool path |
| Agent forges company or role fields | Verify signed identity from independent issuer; ignore caller claims | Signature, expiry, audience and revocation tests |
| Approval replay or scope substitution | Atomic one-time consumption and exact intent binding | Concurrent duplicate-consumption and mutation-race tests |
| Cross-company data/dispatch attempt | Separate company stores and namespaces; explicit scoped delegation only | Isolation tests across scheduler, storage, tools, logs and backups |
| Quarantine races with dispatch | Shared transactional stream lock and epoch check | Multi-process race tests plus receiver-side epoch enforcement |
| Crash after dispatch-start | Mark outcome unknown; reconcile signed receiver evidence | Crash-point fault injection and no-blind-retry tests |
| Database or audit store unavailable | Fail closed; no dispatch | Fault-injection tests at every persistence boundary |
| Privileged rewrite of local audit chain | Signed checkpoints in independently administered immutable storage | Restore drill validating checkpoint signature and exact chain head |
| Receiver accepts duplicate or stale action | Receiver-enforced idempotency and epoch fencing | Contract tests against the actual receiver |
| Signing key compromised | Key isolation, rotation, revocation, dual control and incident recovery | KMS/HSM configuration review and key-rotation/revocation drill |

## Residual risks that must remain explicit
- A local gateway cannot prevent a stale request already in transit from arriving remotely unless the receiver itself validates idempotency and the current recovery epoch.
- A hash-linked audit log cannot resist a privileged actor rewriting the entire database and recomputing hashes without an independent signed checkpoint.
- A transactional local database cannot guarantee exactly-once effects across an unrelated external system.
- A signed approval is only as trustworthy as the owner's authentication, signing-key custody and approval display/confirmation channel.
- SQLite prototypes and synthetic verifier callbacks are not production security controls.
- Multi-node correctness depends on the selected database's documented isolation, locking, durability and failover behavior; this must be tested in the actual topology.
- Cryptographic correctness does not establish legal, regulatory, tax, customer-contract or halal/Shafi'i compliance.

## Production exit criteria
No production claim until all are true:
1. Threat model reviewed and accepted by owner and independent security reviewer.
2. Separate company identity issuers, signing authorities, stores, keys, backups and access policies demonstrated.
3. Asymmetric signatures, key rotation/revocation, trusted time and issuer registries implemented.
4. Deterministic gateway enforced at scheduler, runtime, tool/data, cost, outbox and external-action boundaries with no bypass.
5. Exact committed unit tests pass; multi-process race/fault-injection tests pass in the target database topology.
6. Receiver contract proves idempotency, recipient binding, evidence authenticity and epoch fencing.
7. Signed audit checkpoints stored independently; restore and quarantine/release drills pass.
8. Monitoring, incident response, backup/PITR, tested recovery and independent audit are operational.
9. Trading-specific risk authority and hard-deny controls independently validated; live trading remains separately disabled pending owner approval.
10. AI Revenue has separate commercial evidence; security readiness does not substitute for actual customer delivery and payment received.

## Current validation status
Documentation only. No code execution, cryptographic verification, multi-process test, external receiver test, installation, deployment, CI run or live action is claimed. All production exit criteria remain open until independently evidenced.
