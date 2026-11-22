# Security & Recovery — Incident Register, Corrective Actions & Recovery Assurance Standard

**Status:** Control specification; incident register intentionally empty.  
**Owner:** Organization-level Security & Recovery Division, with separate company incident owners.  
**Authority:** Record, assess, coordinate and recommend. No automatic or unapproved operational action.

## 1. Purpose and scope

Provide a consistent incident lifecycle while preserving independent company records, authority and evidence. Each company maintains its own incident records. A cross-company event receives linked but separate company records plus a minimal shared coordination record where disclosure is approved.

The register starts empty. Do not invent incidents, severities, owners, affected systems, containment, completion, recovery or closure. A near miss or control observation must be classified honestly and must not be inflated into a confirmed breach.

## 2. Incident record schema

Required fields: incident ID and version; created/updated timestamps and timezone; reporting channel and reporter role; affected company and exact system/service/data scope; event and detection times with time-source confidence; severity and rationale; confirmed facts vs hypotheses; confidentiality, integrity, availability, authenticity and safety impact; affected identities/credentials/assets/dependencies (never secret values); indicators/evidence references, provenance, hashes and chain of custody; operational state and known blast radius; immediate risks and containment options/side effects; incident commander, company executive and risk owner roles; approved actions, approver, scope, timestamp and result; notification/legal/regulatory review and approval state; recovery plan, approved RPO/RTO, backup candidate and integrity state; recovery actions and validation evidence; linked risk/decision/task/corrective-action IDs; post-incident review, lessons, owners and due dates; closure decision, approving owner and evidence.

Never place passwords, API keys, seed phrases, private keys, authentication tokens or raw secrets in the register. Reference a secure separately controlled evidence store only if one is later approved.

## 3. Incident lifecycle

1. REPORTED_UNVERIFIED — report received; truth and scope not established.
2. TRIAGE — assess credibility, severity, affected scope and urgency.
3. CONFIRMED / NOT_CONFIRMED / DUPLICATE — evidence-based disposition.
4. ESCALATED — risk owner and company executive engaged per approved route.
5. RESPONSE_PLAN_PENDING_APPROVAL — response options, risks and exact scope documented.
6. RESPONSE_AUTHORIZED — named authority approved specific action and boundaries.
7. CONTAINMENT_IN_PROGRESS / CONTAINED — only if authorized and evidence recorded.
8. INVESTIGATION — preserve evidence, establish timeline, determine root cause and impact.
9. RECOVERY_PLAN_PENDING_APPROVAL — target, backup, restore/rollback and verification steps reviewed.
10. RECOVERY_AUTHORIZED — exact recovery action and target approved.
11. RECOVERY_IN_PROGRESS / RECOVERY_VALIDATION — actions and checks recorded.
12. SERVICE_RESTORED_PENDING_OWNER_ACCEPTANCE — technical health observed; owner acceptance pending.
13. POST_INCIDENT_REVIEW — impact, cause, response and recovery reviewed.
14. CORRECTIVE_ACTIONS_OPEN — owners and deadlines assigned.
15. CLOSED — only after closure criteria are met and approved.

Holding/terminal states: ON_HOLD, FALSE_ALARM, DUPLICATE_LINKED, CANCELLED_WITH_REASON, REOPENED. No transition is implied by elapsed time.

## 4. Severity and escalation

SEV-0 Critical and SEV-1 High: immediate escalation through Risk owner → Executive → affected division/system owner. Cross-company incidents follow each affected company's chain independently.

SEV-2 Moderate: notify accountable company security owner and risk owner within the approved response window. SEV-3 Low: queue for accountable owner review and trend analysis. OBSERVATION: control improvement, not incident.

Response windows and contact methods must be approved by each company; do not invent service-level promises. If an approver is unavailable, follow the approved deputy chain. No AI agent or OCC can appoint itself incident commander.

## 5. Containment and response safeguards

The register may capture recommendations, but it does not execute them. Account lockouts, key rotation, network isolation, process termination, trading pause, wallet action, customer/regulator notification, deletion, rollback, restore and restart each require exact target/scope; impact and side-effect assessment; named authorized owner; explicit approval; timestamp and result evidence; verification and rollback/compensation plan where appropriate.

No automatic containment, rollback, notifications, recovery or approvals. Do not destroy evidence while attempting containment. Preserve logs and relevant snapshots through an approved method.

## 6. Evidence integrity and chain of custody

For every evidence item, record source, collector role, collection time/timezone, method, original location, access restrictions, digest/hash, transformations, transfer history and reviewer. Keep originals immutable where feasible and work from controlled copies.

SHA-256 can detect byte changes against a previously recorded digest. A matching hash alone does not prove evidence authenticity, source cleanliness or completeness. Protect the digest and metadata against alteration. Never collect secrets or personal data beyond the minimum necessary.

## 7. Recovery assurance workflow

### 7.1 Before an incident

For each critical system/data set, document owner, dependencies, classification, approved backup schedule, retention, encryption, access separation, recovery objectives, restore steps and known-good release. Separate backup credentials and failure domains from production where feasible. Backups must not be writable by the same compromised identity that controls production.

### 7.2 Integrity checks

- Generate and securely record SHA-256 digests for approved backup artifacts and manifests.
- Verify digest after transfer and before restore.
- Keep manifest/version, source, time and tool/method with evidence.
- If digest mismatch occurs, quarantine the candidate and investigate; do not overwrite the only known-good copy.
- A digest match is evidence of byte consistency, not proof of a safe or complete backup.

### 7.3 Restore-after-corruption drill

A future approved non-production drill should use synthetic or specifically approved test data; preserve an untouched baseline; introduce controlled corruption; detect mismatch and quarantine the damaged copy; select a known-good backup by provenance; verify digest and restore into an isolated test environment; validate schema, completeness, permissions, dependencies and application health; reconcile records/events and check for missing or duplicate actions; record actual elapsed and hands-on time, defects and outcome; obtain independent reviewer and owner acceptance.

A successful file copy is not a successful restore drill. No drill has been run under this document.

### 7.4 Rollback and restart

Rollback requires an approved target version, data compatibility review, snapshot/backup, exact scope, owner approval and post-rollback validation. Restart requires dependency order, health checks, integrity checks, monitoring and owner acceptance. A service being reachable does not prove correct or safe operation.

### 7.5 Recovery status

Use NOT_ASSESSED, PLAN_DRAFT, BACKUP_UNVERIFIED, INTEGRITY_VERIFIED, RESTORE_DRILL_PASSED, RESTORE_DRILL_FAILED, ROLLBACK_READY, RESTART_CHECKS_PASSED, OWNER_ACCEPTED or RECOVERY_BLOCKED. Never use RECOVERED without evidence and authorized owner acceptance.

## 8. Corrective-action lifecycle

Each action records linked incident/risk, root cause, specific correction, owner role, due date, dependency, evidence required, independent verifier and closure approval.

States: PROPOSED, APPROVED, IN_PROGRESS, BLOCKED, EVIDENCE_SUBMITTED, INDEPENDENT_REVIEW, REJECTED_REWORK, VERIFIED_COMPLETE, CLOSED.

An action is not complete because someone says it is complete. The verifier checks evidence against acceptance criteria. Repeated/systemic failures require control redesign, not superficial repeated closure.

## 9. Post-incident review and closure

Closure requires incident facts and impact documented, including uncertainty; timeline and evidence chain reviewed; response/containment decisions and approvals recorded; recovery evidence and owner acceptance where recovery occurred; corrective actions completed or explicitly accepted as open residual risk by the proper owner; legal/regulatory/customer/third-party notification obligations reviewed by qualified people; independent post-incident challenge; approved owner decision and closure evidence.

Critical/high closure must not be self-approved solely by incident commander or implementer. If corrective actions remain open, record why and the accountable owner; do not imply all risk is eliminated.

## 10. Company isolation and OCC reporting

Maintain separate full incident registers for AI Revenue and Trading & Technology. Shared coordination records contain only minimum approved cross-company metadata. OCC receives aggregate status and approved evidence references, never raw forensic records, customer data, credentials, wallet secrets or private strategy information. Each company controls its own notifications, recovery, risk acceptance and closure.

## 11. Empty register initialization

The register begins with no incident entries. This is a schema, not evidence that the organization has no security risks or that monitoring has occurred.

Register status: EMPTY_BY_DESIGN  
Incidents: []  
Corrective actions: []  
Recovery drills: []  
Open exceptions: []  
Last reviewed at: NOT_RECORDED

## 12. Current disposition

STANDARD PREPARED; REGISTER EMPTY; NO INCIDENTS ASSERTED; NO SECURITY MONITORING; NO CONTAINMENT; NO NOTIFICATIONS; NO BACKUP JOBS; NO RESTORE/ROLLBACK/RESTART; NO RECOVERY DRILL; NO INCIDENT CLOSED.
