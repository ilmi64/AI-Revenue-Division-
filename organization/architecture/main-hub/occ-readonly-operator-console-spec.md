# Main Hub / OCC — Read-Only Operator Console Specification

**Status:** UX and interface specification only; no OCC application is deployed.  
**Mode:** Read-only, evidence-first, two-company view plus shared-service health.  
**Authority:** OCC coordinates and reports; it does not direct company operations or grant authority.

## 1. Operator experience

The landing page shows three distinct zones:
1. **AI Revenue Company** — its own status, critical gates, blockers, incident summary, last verified update and evidence links.
2. **Trading & Technology Company** — a separate status card with its own gates, risk posture summary, blockers, incidents and evidence links.
3. **Organization Shared Services** — Main Hub/OCC, Research & Intelligence and optional shared infrastructure health, clearly labelled as non-company services.

Never combine the two company statuses into one organization-wide green badge. Never let a healthy shared service conceal a company failure or vice versa.

## 2. Company detail view

Each company view contains:
- identity and publisher/source revision;
- snapshot time, age, freshness and authentication state;
- company-reported overall status, with unknown/stale/quarantined states visible;
- department/workstream status and owner;
- critical launch gates individually shown as PASS, FAIL, BLOCKED, NOT_RUN or WAIVED;
- blockers with accountable company owner and last update;
- incident severity, count, state and last verified checkpoint;
- evidence register links and supersession history;
- company-specific workforce queue health summary (counts only unless access is separately authorized).

WAIVED is never rendered as PASS. NOT_RUN and missing evidence remain unresolved. No weighted readiness score may hide a critical failure.

## 3. Trading-specific panel

Show research/paper/live mode as three distinct states. Live mode is displayed as disabled unless the company provides independently authenticated evidence and the separate live-execution authorization record. Display CRO veto/hold state, market-data health, venue/contract incident summaries and kill-switch status as company-published evidence. OCC cannot clear a veto, enable a venue or submit an order.

## 4. AI Revenue-specific panel

Show offer/service readiness, delivery capacity, QA status, support coverage, pipeline summary, finance/cost controls and customer-impact incidents as company-published evidence. No customer personal data, prospect identities, private messages, invoice contents or raw sales records are displayed by default.

## 5. Research and shared-service panel

Research service panel shows desk coverage, queue backlog, source freshness, publication age, unresolved contradiction count, handover acceptance and explicit coverage gaps. Grok Desk/HyperGrok are shown as planned/not connected until proven otherwise. Shared infrastructure shows component health, tenant-isolation evidence, outage/degraded state and last failover rehearsal; it does not expose secrets or private payloads.

## 6. Data contracts and trust display

Every snapshot is treated as untrusted until publisher authentication, signature, audience, expiry, sequence/replay and schema checks pass. The UI separately displays:
- schema validity;
- publisher authentication;
- freshness;
- replay/order state;
- semantic evidence completeness;
- company-reported readiness.

Authentication proves message origin/integrity, not the truth of a claim or authority to act. If trust cannot be established, quarantine the snapshot and retain last-known-good data with a stale warning.

## 7. Navigation and audit

Primary navigation: Overview; AI Revenue; Trading & Technology; Research & Intelligence; Shared Infrastructure; Decisions; Evidence; Incidents; Audit; System Health. Every status and metric links to its source record, timestamp, revision and history. Filters must not erase the company scope. Export is read-only and records who exported what and when.

## 8. Access and interaction restrictions

Initial OCC users can view and export approved summaries only. No command console, remote shell, agent prompt editor, wallet panel, customer record browser, trade ticket, payment control, permission editor, deployment button or policy override. Any future write capability requires a separately reviewed design, explicit owner authorization, deterministic policy enforcement and an auditable approval workflow. A visual control must never imply an action that is not actually supported.

## 9. Accessibility and operational quality

Provide keyboard navigation, screen-reader labels, clear status text/icons, timezone-aware timestamps, mobile/tablet responsive layouts, contrast, no color-only status encoding and clear stale/unknown states. Show last refresh and source age. A failed refresh must not leave a misleading current-looking screen.

## 10. Acceptance criteria

Before calling the OCC usable: synthetic two-company snapshots render separately; stale, unauthenticated, duplicate, malformed and contradictory records are visibly blocked/quarantined; WAIVED never appears as PASS; missing/NOT_RUN gates remain unresolved; company data cannot cross tenant boundaries; Research and shared services remain separate; audit links resolve; outage/failover and restore are rehearsed; and no UI action can initiate an external or financial action.
