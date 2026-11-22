# PG-4 — Company-Local Policy Enforcement and Bypass-Resistance Architecture

**Status:** Architecture-only enforcement map; no runtime, gateway, network policy, deployment or test execution.  
**Applies independently:** AI Revenue and Trading & Technology.  
**Design rule:** Every consequential path is denied unless all required independent enforcement layers explicitly permit the exact operation. A policy decision is not an execution token.

## 1. Security objective

Prevent a model, agent, swarm, scheduler, connector, plugin, operator console or compromised worker from bypassing company policy by calling a tool, database, network endpoint, file path, API, account or external receiver directly.

A single policy gateway is insufficient if any alternate path can reach the protected resource. Enforcement must be layered at the task, runtime, data, cost, external-action, network and receiver boundaries. Every layer independently validates the relevant signed scope and current revocation/policy state.

## 2. Company-local topology

Each company has its own:

- identity issuer and trust registry;
- task scheduler and assignment store;
- deterministic policy service and policy version;
- approval authority and durable approval/control store;
- data gateway and tenant boundary;
- cost/resource meter;
- action outbox and dispatch authority;
- audit stream, checkpoint and recovery authority;
- service credentials, network policy and incident response.

The same open-source control-plane software may be reused only as isolated deployments/tenants after review. Shared code is not shared authority. The Research & Intelligence Division supplies scoped advisory findings; Main Hub/OCC receives only read-only allowlisted summaries. Neither can authorize company actions.

## 3. Enforcement-point contract

| Enforcement point | Authoritative inputs | Must enforce | Fail-closed behaviour |
|---|---|---|---|
| Task intake/scheduler | Verified principal, signed task, trusted task store | Company, assignment, queue, task state, allowed operation/resource, expiry, parent-child scope, data classes and resource bounds | Reject unknown, cancelled, expired, unassigned, cross-company or widened tasks |
| Runtime supervisor | Verified short-lived identity, task lease, policy version, runtime attestation | Process identity, tool allowlist, filesystem/workspace scope, runtime limits, task cancellation and lease fencing | Stop/deny tool calls on missing identity, stale lease, policy mismatch or cancellation |
| MCP/tool broker | Runtime identity, canonical operation, exact resource, single-use permit | Every tool call; no model-controlled tool name expansion, credential forwarding or arbitrary URL/command execution | Deny unknown tool/action; no direct connector access outside broker |
| Data gateway | Company identity, classification, field/resource scope, source provenance | Reads and writes, tenant isolation, redaction, export rules, source freshness and revision | Deny cross-company, unclassified, stale or unauthorized access; quarantine conflicting market data |
| Cost/resource meter | Signed task budget, provider price/usage metadata, current CAD policy | Preflight inference/API/compute/storage/network/egress cost and resource caps | Unknown price or unmetered usage is not zero; deny billable operation under CAD $0 |
| Policy decision service | Verified identity/task/data/cost/stop state | Canonical operation allowlist, company policy, separation of duties, hard denies and approval requirement | Default deny; unavailable/stale/contradictory dependencies deny |
| Owner approval service | Owner-authenticated session, signed exact-scope envelope, trusted key registry | Owner-only approval issuance, scope digest, recipient, amount/currency, expiry, nonce and single use | Agents cannot invoke or write approval records; any verification uncertainty denies |
| Control store/outbox | Trusted action intent, approval, task, recovery epoch, idempotency key | Atomic approval consumption, immutable intent, dispatch reservation, audit append and quarantine serialization | Transaction rollback on any mismatch or audit failure; no sender before commit |
| Network egress gateway | Service identity, destination allowlist, operation permit | Block arbitrary internet, raw sockets, unapproved domains, private network access and alternate external sender paths | Deny all non-allowlisted egress; no bypass route from agent runtime |
| External sender | Authenticated dispatch authority and committed outbox intent | Exact destination/account, recipient, amount/currency, payload digest, idempotency and recovery epoch | No action on stale permit, replay, mismatch, unknown policy or stale epoch |
| Receiver/evidence verifier | Signed receiver response, pinned receiver identity, action intent and nonce store | Verify destination, action digest, outcome, timestamp, idempotency and epoch; atomic evidence receipt | Mismatch or timeout remains unknown/quarantined; never infer success from a label |
| Audit/checkpoint service | Authenticated event source and canonical event schema | Append allow/deny, approval, dispatch, receiver, recovery and privileged-change evidence | Audit unavailable or append failure blocks consequential operations |

## 4. Required authorization sequence

For a future consequential action, the required sequence is:

1. Authenticate principal using company-specific identity issuer.
2. Resolve task assignment and scope from trusted scheduler; do not trust task claims supplied by model.
3. Resolve exact resource and classification through the company data/resource registry.
4. Determine canonical operation ID and verify it exists in the company policy profile.
5. Evaluate company policy, budget, risk state, emergency stop, revocation, freshness and separation of duties.
6. Apply hard-deny rules before any approval lookup. Trading live financial and protected risk-control operations remain hard-denied.
7. If the operation is eligible for approval, verify a separately authenticated owner approval bound to exact intent, recipient, amount/currency, company, principal/session, task, policy and expiry.
8. Create a short-lived request-bound decision permit. The permit is not transferable, cannot be widened, and is single-use.
9. Immediately before dispatch, re-resolve identity, task, policy, revocation, emergency-stop, cost and recovery epoch.
10. In one authoritative transaction consume approval, reserve immutable action/outbox intent and append audit.
11. Dispatch only after commit through the isolated sender; enforce receiver idempotency and epoch fencing.
12. Verify signed receiver evidence and atomically record the result. Ambiguous outcomes remain unknown and require reconciliation.

Read-only research operations may use a narrower path, but must still pass identity, task, company, data-source, data-classification, resource and audit checks. “Read-only” does not mean unrestricted data exfiltration or arbitrary network access.

## 5. Bypass threats and required controls

| Bypass attempt | Required prevention |
|---|---|
| Agent calls connector/tool directly instead of MCP broker | Tool credentials exist only in broker; runtime/network egress blocks direct connector paths |
| Agent supplies a fake company, role, task, owner or approval ID | Authenticated issuer and trusted scheduler/owner registry resolve authoritative identity; request fields are comparison data only |
| Model asks another agent/swarm to perform prohibited action | Every worker has its own company-scoped identity and every action is checked at the final boundary; delegation does not transfer authority |
| Agent writes directly to SQLite/PostgreSQL | No DB credentials or network route in model/runtime; narrow service APIs and least-privilege database roles |
| Agent uses arbitrary URL, shell, raw socket or file path | Runtime sandbox, path allowlists, network egress policy and broker-only external calls |
| Agent reuses a stale approval or policy allow | Short expiry, single-use nonce, durable replay consumption, final policy/revocation check |
| Task is reassigned or cancelled after approval | Scheduler version/assignment check and transactionally rechecked task status before dispatch |
| Quarantine occurs between enqueue and send | Shared recovery epoch/stream state locked with dispatch authorization; receiver epoch fencing |
| Cost is hidden in a model/tool/API call | Preflight and post-use metering at every billable boundary; unknown cost denies under CAD $0 |
| Agent edits policy or changes hard-deny list | Policy administration separate from runtime; signed versioned policy release and owner/security change control |
| Agent forges sender/receiver success | Sender result API accepts only verified signed evidence; no caller-supplied result labels |
| OCC or Research tries to command a company | OCC is read-only; Research publications are advisory and recipient-scoped; company-local policy still decides |
| Shared infrastructure outage causes permissive fallback | Fail closed for consequential actions; company can continue approved local read-only/offline work only if its independent policy and data path remain available |
| Main Hub or one company becomes unavailable | Other company remains isolated and independently operable; no implicit shared dependency or credential |

## 6. Resource and egress isolation

- Each runtime has explicit CPU, memory, disk, process, output-size and time bounds.
- Filesystem access is limited to a company workspace and task-specific paths; secrets and host credentials are not mounted into agent contexts.
- Network egress is denied by default. Allow only named, reviewed endpoints for a specific service identity and purpose; public web browsing for research must still respect provider terms and source policies.
- No arbitrary shell, package install, browser automation, account login, raw API call or connector action is implied by a research task.
- Tool adapters must expose typed operations, not generic unrestricted HTTP or filesystem primitives.
- Model inference and tool usage must be metered before billable execution. A free/open-source orchestrator does not prove that model inference, hosting or data access is free.
- Resource exhaustion, rate-limit response, provider outage or unknown charges must not trigger uncontrolled retries or fallback to paid providers.

## 7. Company-specific overlays

### AI Revenue

- Current CAD $0 incremental spend remains a hard budget.
- Internal research, analysis, drafting and approved local file preparation may proceed within exact task scope.
- Customer contact, publication, contract, quote commitment, purchases, payments, account/permission changes and deployment remain separate approval classes; none is authorized by this architecture.
- Customer data is private to AI Revenue and is not sent to external model/API providers without an approved data-processing basis and exact scope.

### Trading & Technology

- READ_ONLY_RESEARCH, BACKTEST and PAPER_SIMULATION only.
- Live execution, exchange/broker account access, wallet connection/signing, deposits, transfers, withdrawals and risk-limit/HALT/STOP changes are hard-denied at policy and execution boundaries.
- Independent risk authority is a mandatory final gate for paper strategy workflows and retains veto; unavailable risk service denies consequential Trading operations.
- Market data must include provenance, timestamps, freshness and transformation lineage. Conflicting/stale sources are quarantined.
- Halal/Shafi'i review flags are maintained separately and cannot be inferred by a model or automated policy engine.

## 8. Recovery and independent operation

- A company must remain safe if Main Hub/OCC, Research & Intelligence, Paperclip, Ruflo, a model provider or shared infrastructure fails.
- Shared control-plane failure cannot cause an allow-by-default fallback.
- Each company retains local policy, identity/revocation cache with bounded freshness, task cancellation, audit and recovery state.
- A company may continue only those offline/read-only activities explicitly allowed by its local policy and data availability; it must stop consequential work if required trust dependencies are unavailable.
- Recovery requires independent assessment, owner release and fresh health/policy/key/revocation checks. Recovery never replays an ambiguous external action automatically.

## 9. Implementation and evidence gates

Before any runtime integration, require:

1. Exact inventory of every tool, connector, file, network, database and external side-effect path.
2. Threat model and bypass-path review for each path.
3. Company-specific service identities, key custody and signed policy distribution.
4. Enforcement prototypes with synthetic data and no external side effects.
5. Negative tests for every bypass row, outage, replay, revocation, task cancellation, cost uncertainty and cross-company access.
6. Multi-process race/fault testing, database rollback and restore evidence.
7. Independent security review and company owner acceptance.
8. Evidence register updates against exact source revisions.

Tests require separate user authorization. No installs, database changes, keys, network connections, GitHub Actions, deployments or live financial actions are authorized by this document.

**Disposition:** PG-4 enforcement map documented. No policy gateway is deployed or proven to cover every path; no autonomous external action is enabled.
