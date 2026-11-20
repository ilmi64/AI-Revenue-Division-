# Production Readiness Evidence Register

Status: open evidence register. This file records proof required; it does not mark any control as implemented, tested, approved or operational.

## Rules for evidence
- Every gate needs an evidence artifact, exact source revision, environment, operator, timestamp and result.
- A document describing a control is not evidence that the control runs.
- A test definition is not a test result. A locally reconstructed test is not execution of the committed test.
- A passing unit test is not production deployment evidence.
- Any changed source revision invalidates test evidence for the previous revision unless equivalence is demonstrated.
- Failures, skipped tests, flaky tests and unavailable dependencies must be recorded; never silently convert them to pass.
- Company-specific evidence belongs in that company's records. OCC receives a summary and evidence reference only.
- No gate may be waived by an agent, model, orchestration system or company executive acting alone.

## Gate register

| ID | Gate | Required proof | Current status | Release effect |
|---|---|---|---|---|
| EV-01 | Exact source identity | Commit SHA and hashes for source, tests and dependencies | Pending execution environment | Blocks validation claims |
| EV-02 | Committed unit tests | Full test output from exact checkout and SHA | Not executed | Blocks code-validation gate |
| EV-03 | Multi-process races | Separate OS processes, separate connections, deterministic barriers and retained logs | Specification only | Blocks concurrency claim |
| EV-04 | Fault injection | Crash at every transaction/sender boundary; restart and recovery evidence | Specification only | Blocks recovery claim |
| EV-05 | Identity authenticity | Real asymmetric issuer verification, expiry, audience, revocation and key-rotation tests | Synthetic/reference only | Blocks trusted identity |
| EV-06 | Owner approval authenticity | Independently authenticated owner signature, exact scope, nonce and revocation tests | Not implemented/verified | Blocks external approval |
| EV-07 | Policy gateway coverage | Demonstrated enforcement at scheduler, runtime, tools, data, cost, outbox and external gateway; bypass tests | Contract/reference only | Blocks autonomous actions |
| EV-08 | Company isolation | Cross-company adversarial tests for storage, memory, tools, logs, backups and credentials | Contract only | Blocks shared workforce |
| EV-09 | Durable audit | Signed checkpoints, independent immutable storage, key separation and restore verification | Hash-chain prototype only | Blocks audit assurance |
| EV-10 | Recovery authority | Independent assessor, owner approval, quarantine/release drills, revocation and epoch checks | Reference only | Blocks recovery release |
| EV-11 | Receiver safety | Actual receiver idempotency, immutable destination binding, signed evidence and epoch fencing | Not integrated | Blocks external dispatch |
| EV-12 | Production database | Selected topology, isolation/locking/durability evidence, failover and backup/PITR restore drills | SQLite reference only | Blocks multi-node claim |
| EV-13 | Monitoring and incident response | Alert routing, runbooks, stop controls, on-call ownership and incident exercises | Not operational | Blocks unattended operation |
| EV-14 | Legal/compliance review | Canada/Ontario obligations, privacy, tax, consumer and contractual review; product-specific review | Pending | Blocks relevant commercial launch |
| EV-15 | Trading risk independence | Independent risk authority, hard-deny tests, paper exit/reconciliation evidence and halal review flags | Not established | Blocks trading readiness |
| EV-16 | AI Revenue commercial proof | Actual customer, accepted delivery, invoice/transaction record and payment received | Not evidenced | Blocks AI Revenue launch |
| EV-17 | AI workforce autonomy | Persistent runtime, bounded permissions, durable queues/memory, supervision, recovery and 24/7 drills | Architecture only | Blocks autonomy claim |

## Evidence record template
For each gate, record:
- Gate ID and company.
- Source commit SHA; source/test/dependency hashes.
- Environment and exact command/configuration.
- Start/end timestamps and operator identity.
- Raw logs/artifact location and integrity digest.
- Pass/fail/skipped/blocked result, including all failures.
- Independent reviewer and review date.
- Known limitations and residual risks.
- Explicit owner decision where approval is required.

## Release decision rules
- PASS: all required evidence exists, is current, independently reviewable and meets the stated acceptance criteria.
- FAIL: evidence demonstrates a requirement is not met.
- BLOCKED: required environment, dependency, authority or approval is unavailable.
- NOT_RUN: no execution evidence exists.
- WAIVED: only where the owner explicitly approves a documented, legally permissible exception; security-critical hard-deny and financial approval boundaries are not waivable by agents.

No aggregate readiness percentage may conceal a failed or blocked critical gate. A single critical gate in FAIL, BLOCKED or NOT_RUN prevents the corresponding production claim.

## Current executive disposition
- AI Revenue: NOT READY / NOT OPERATIONAL; actual payment received has not been evidenced.
- Trading & Technology: NOT READY / PAPER-ONLY ARCHITECTURE; live trading and external financial dispatch remain disabled.
- OCC: governance and evidence coordination only; no company authority is transferred to OCC.
- January 2027 simultaneous launch remains a target, not a representation of readiness. If a critical gate remains open, report the gap and seek an owner decision; do not lower the gate or claim a launch that has not occurred.
