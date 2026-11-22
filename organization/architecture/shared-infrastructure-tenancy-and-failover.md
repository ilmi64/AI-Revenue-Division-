# Shared Infrastructure — Company Tenancy, Isolation & Failover Specification

**Status:** Architecture only; no shared runtime or federation is deployed.  
**Principle:** Shared infrastructure; no shared authority or private company data by default.

## 1. Permitted shared-service categories

Potentially shared as replaceable infrastructure: model adapters/runtimes, orchestration software, observability platform, artifact storage technology, CI-independent documentation tooling, and Main Hub/OCC transport/presentation components. A shared component is a convenience, never a company dependency or authority.

## 2. Mandatory tenant separation

Create separate tenant/configuration boundaries for AI Revenue and Trading & Technology across:
- agent identities, service accounts, runtime namespaces and workload labels;
- orchestration projects, swarms, queues, schedules and retry/dead-letter stores;
- memory stores, embeddings, retrieval indexes, caches and conversation histories;
- prompts, system policies, tool allowlists, model routing and evaluation datasets;
- secrets, encryption keys, credentials, certificates and signing identities;
- audit logs, traces, metrics labels, incident records and retention policies;
- databases, object prefixes/buckets, backups, restore keys and disaster-recovery procedures;
- budgets, cost attribution, usage limits and company reporting.

A shared physical host or platform must not imply shared logical tenancy. Where hard isolation cannot be demonstrated, do not place confidential company data there.

## 3. Cross-company exchange contract

Default deny. Exchange only through an explicit, authenticated, versioned interface with:
- named sending company and receiving company;
- data classification and purpose limitation;
- allowlisted schema/fields and maximum payload size;
- source revision, timestamp, expiry and replay identifier;
- authorization and policy decision recorded at both ends;
- provenance, integrity and audit evidence;
- receiver validation, idempotency and rejection/quarantine behavior;
- revocation and retention rules.

No raw memory, full task transcripts, credentials, customer records, wallets, private strategies, finance ledgers or unrestricted logs cross company boundaries. Research publications are separately scoped and sanitized.

## 4. Failure and degraded-mode requirements

Each company must retain its own local policy enforcement, identity authority, queues, memory, audit capture, data access rules, emergency stop and recovery authority. If shared orchestration, model provider, OCC, Research Division, network, storage or the other company fails:
1. stop new cross-company exchange;
2. keep local records and controls available;
3. degrade to approved local/manual workflow or pause safely;
4. preserve durable queued work and audit events;
5. mark shared status stale/unavailable;
6. recover only after integrity, sequence, revocation and backlog reconciliation.

Trading must fail closed for any missing risk service, market-data integrity, signing boundary or critical control. AI Revenue must stop affected delivery or fall back to an approved manual process when customer data, quality or security controls are uncertain.

## 5. Workforce manager and orchestrator boundaries

Paperclip remains a candidate workforce control plane; Ruflo remains a candidate multi-agent orchestrator. Neither is a security boundary or authority source. They must be deployed with separate company tenants and independently enforceable policy gateways. Disable broad unattended autonomy, unrestricted filesystem/network access, cross-tenant agent discovery and self-modifying permissions initially.

## 6. Model-agnostic adapter contract

Adapters expose capability metadata, model/runtime identity, version, context limits, tool capabilities, data-handling terms, availability, cost attribution, timeout/retry behavior and evaluation status. Model substitutions require evaluation and approval; the adapter cannot elevate permissions. Claude Code, Codex, Qwen, Llama, Gemini and other models are candidates subject to compatibility and policy checks.

## 7. Recovery and exit strategy

Maintain per-company exportable records, documented schemas, configuration-as-code, versioned prompts/policies, backup integrity checks, restore drills, and a migration path away from each shared provider. A company must be able to replace or remove shared orchestration without losing its local policy, memory, queue, audit or operating continuity.

## 8. Acceptance gates

Before any shared runtime is used with company data: threat model; tenant isolation test; cross-tenant denial test; identity and key separation; audit completeness; backup/restore; provider outage drill; revocation drill; data export/exit rehearsal; cost attribution; and explicit owner approval. No installation, paid service, API usage, deployment or permission change is authorized by this design.
