# OCC Workforce & Queue Observability Contract

**Status:** Read-only interface specification; no live adapters or feeds are deployed.
**Consumers:** Main Hub / OCC only.
**Producers:** AI Revenue, Trading & Technology and Research & Intelligence through separately owned publishers.

## 1. Purpose and hard boundary

The OCC may display whether each tenant's workforce and queues appear healthy. It is not a queue manager, scheduler, workforce supervisor, policy engine or command bus. It cannot claim, cancel, reprioritize, reassign, approve, retry, release or dispatch tasks. It cannot read raw task payloads, prompts, customer data, trading strategies, account data, private memory, credentials or source-vault contents.

Each producer decides what to publish and signs its own scoped snapshot. OCC validates publisher identity, audience, source revision, freshness, schema and replay/order state before display. Authentication proves origin/integrity, not truth, readiness or permission.

## 2. Separate tenant channels

Maintain three distinct namespaces: `ai_revenue`, `trading_technology`, and `research_intelligence`. The first two remain the only operating companies; Research is an organization-level division. Separate publisher identities, trust records, sequence counters, storage partitions, audit events and retention rules are mandatory. No shared bearer token or common unrestricted publisher.

## 3. Allowlisted aggregate payload

Permitted fields only:
- tenant ID, publisher ID, schema/version, snapshot ID and source revision;
- issued-at, expires-at, sequence number and snapshot digest;
- overall feed health: HEALTHY, DEGRADED, STALE, UNKNOWN or QUARANTINED;
- queue ID from an approved registry, priority band, counts by coarse state, oldest-age band and last successful update time;
- aggregate active/blocked/dead-letter counts, without task identifiers or payloads;
- sanitized incident severity/count and approved incident reference;
- coverage status and missed-coverage indicator;
- policy-denied attempt count and approval-wait count as aggregate telemetry only.

No agent names, principal IDs, task IDs, task text, customer identifiers, instrument/venue/strategy identifiers, exact monetary values, credentials, memory excerpts or source documents are allowed. Exact fields and thresholds are versioned allowlists owned by the publisher and reviewed before adapter implementation.

## 4. Validation and quarantine

Reject or quarantine malformed schemas, unknown tenants, wrong audience, unknown publisher/key, stale or expired snapshots, duplicate/replayed sequence, sequence gaps beyond policy, digest/signature mismatch, unsupported schema version, unexpected fields and contradictory source revisions. Never silently merge across tenant namespaces. Last-known-good may be shown only with its age and STALE label; it is not treated as current. A trust-registry refresh failure blocks ingestion rather than extending stale trust indefinitely.

OCC must display missing data as UNKNOWN, not zero. A count of zero is valid only when the authenticated producer explicitly publishes zero for that interval. A missing queue is not evidence that the queue is empty. Quarantine and rejection events remain visible in OCC's own audit.

## 5. Freshness and degraded states

Each feed defines a maximum age and expiry. On expiry, display STALE and stop using the snapshot for current health conclusions. If the producer is unreachable, preserve the last verified snapshot with age and mark the feed DEGRADED/STALE. If integrity or identity checks fail, mark QUARANTINED and suppress its content. Never synthesize health status from model interpretation.

## 6. Read-only UI and access

OCC operators may view approved aggregate metrics and evidence references. There are no task action buttons, command shell, agent prompt editor, policy editor, wallet/trade/payment controls or permission mutation paths. Access to OCC does not grant access to company systems. Company-owned adapters may publish only their own approved summaries.

## 7. Acceptance criteria

- Tenant namespaces and publisher identities are cryptographically and operationally isolated.
- Payload allowlists reject raw/private fields and unknown properties.
- Missing, zero, stale, replayed and quarantined data are distinguishable.
- OCC cannot invoke any queue or company action.
- A tenant outage or OCC outage does not stop company-local queue operation.
- No company can read another company's queue or Research's raw source vault.
- Audit and recovery preserve publisher sequence, source revision and last-known-good provenance.

This contract is a design target. No feed, authentication mechanism or live queue integration is claimed to exist.

## 8. Research publication observability

Research publication counts, recipient-scoped delivery states, freshness bands and acknowledgement status may be exposed only through the [Recipient-Scoped Intelligence Delivery Contract](../research/recipient-scoped-intelligence-delivery-contract.md) and the existing aggregate allowlist. OCC does not receive report bodies, raw source records or company-private task content.
