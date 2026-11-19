# Deterministic policy gateway contract

Status: reference implementation and test vectors only; not deployed, connected or independently security-reviewed.

## Trust boundaries
- Model output, prompts, Paperclip metadata, Ruflo plans and agent-supplied claims are untrusted requests.
- Identity verification, current policy version, emergency-stop state and owner-approval consumption are trusted infrastructure callbacks. They must be authenticated services outside model control.
- Gateway is the sole authorization decision point before a consequential tool/data/outbox operation. No direct model-to-tool bypass.
- The gateway returns a decision only; it does not execute actions, issue credentials or mint approvals.

## Mandatory checks, in order
1. Verify signed identity assertion and issuer/audience; check active status, session, expiry and revocation.
2. Match principal company, agent and role to the assigned task.
3. Check task expiry, allowed operation, exact resource, cost/amount bounds and policy version.
4. Read current company emergency-stop state; unavailable or uncertain means deny.
5. Deny protected control-plane changes and all Trading live-order, wallet-signing, funds-transfer, broker-order, withdrawal and risk HALT/STOP modification operations.
6. For actions requiring owner approval, consume a signed, short-lived, single-use approval bound to exact company, principal/session, task, operation, resource, amount/limits, policy version and nonce.
7. Recheck authorization immediately before dispatch at the enforcement gateway; do not rely on an earlier allow decision.

## Decision semantics
- Only explicit allow may proceed. All unknown operations, malformed claims, stale policy, expired identities/tasks, dependency failures, missing approval, revoked approval, emergency-stop uncertainty and scope mismatch deny.
- An allow decision is short-lived and bound to a request digest; production must use an authenticated, single-use permit or repeat checks at the final enforcement point.
- Policy callbacks must not be model-controlled or replaceable by the requesting agent.
- Audit both allow and deny decisions with correlation IDs, policy version and reason code, excluding secrets and reusable tokens.

## Production requirements
- Independent identity issuer, policy administration and owner-approval authority; asymmetric signatures and protected private keys.
- Highly available but fail-closed emergency-stop service; authenticated policy distribution and monotonic versioning.
- Gateway enforcement in scheduler, runtime/tool gateway, data gateway, cost meter and external-action/outbox dispatcher. Network segmentation prevents bypass.
- Company-specific policy namespaces, separate audit streams and least-privilege service identities.
- Rate limits, bounded request sizes, schema validation, clock synchronization/uncertainty handling, revocation propagation, tamper-evident audit and incident response.
- Threat model, independent code review, adversarial tests, concurrency/fault-injection tests, recovery rehearsal and owner approval before deployment.

## Non-goals
This reference does not implement cryptographic identity verification, durable approval consumption, distributed policy consensus, a secure clock, remote attestation or production authorization tokens. Passing unit tests does not establish production readiness.
