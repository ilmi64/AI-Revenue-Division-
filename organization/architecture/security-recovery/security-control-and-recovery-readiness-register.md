# Security & Recovery — Control and Recovery Readiness Register (Blank)

**Status:** Empty-by-design assurance register; no controls are claimed effective.  
**Owner:** Organization-level Security & Recovery Division, with separate company records.  
**Authority:** Documentation and assurance only; no scans, configuration changes, backup jobs or recovery actions authorized.

## 1. Register rules

Maintain separate detailed registers for AI Revenue and Trading & Technology. Shared organization-level records may track approved control IDs, aggregate status and dependencies only. Do not place secrets, raw logs, customer data or full forensic evidence in a shared register.

A policy document is not proof of implementation. A configured control is not proof of effectiveness. A successful isolated test is not proof of production resilience. Every status requires evidence, scope, date, reviewer and expiry/retest trigger.

## 2. Control record template

| Field | Value |
|---|---|
| Control ID / version | NOT_REGISTERED |
| Company / scope | NOT_ASSIGNED |
| Asset/service/data class | UNKNOWN |
| Control objective | NOT_DEFINED |
| Threat/failure addressed | UNKNOWN |
| Control owner | UNASSIGNED |
| Implementation state | NOT_ASSESSED |
| Evidence reference | NONE |
| Test method / expected result | NOT_DEFINED |
| Last test / result | NOT_RUN |
| Independent reviewer | UNASSIGNED |
| Exception / residual risk | UNKNOWN |
| Approval / expiry | NOT_RECORDED |

## 3. Recovery asset record template

| Field | Value |
|---|---|
| Recovery record ID | NOT_REGISTERED |
| Company and service owner | NOT_ASSIGNED |
| Recovery owner / deputy | UNASSIGNED |
| System/data classification | UNKNOWN |
| Dependencies and recovery order | UNKNOWN |
| RPO / RTO | UNSET |
| Backup source / location | UNKNOWN |
| Backup identity/access separation | NOT_ASSESSED |
| Encryption / retention | UNKNOWN |
| Manifest / SHA-256 digest reference | NONE |
| Last integrity verification | NOT_RUN |
| Restore-after-corruption drill | NOT_RUN |
| Rollback target / procedure | NOT_DEFINED |
| Restart health checks | NOT_DEFINED |
| Owner acceptance | NOT_RECEIVED |
| Residual risks | UNKNOWN |

## 4. Required control families

Track separately: governance and risk; identity and access; secrets/key management; application and agent security; infrastructure/network/endpoint security; data protection/privacy; secure development and supply chain; logging and evidence integrity; threat intelligence and monitoring; incident response; business continuity; backup and disaster recovery; rollback and restart; third-party risk; human factors and training; company isolation and OCC reporting.

## 5. Evidence and readiness states

NOT_ASSESSED; DESIGN_ONLY; IMPLEMENTATION_PENDING; IMPLEMENTED_UNVERIFIED; EVIDENCE_SUBMITTED; INDEPENDENT_REVIEW; VERIFIED_FOR_SCOPED_USE; FAILED; EXCEPTION_APPROVED; EXPIRED; RETEST_REQUIRED.

Do not label a control VERIFIED_FOR_SCOPED_USE without a defined test, evidence, independent review and explicit scope. Exception approval must come from the proper company owner and must be time-limited.

## 6. Empty initialization

AI Revenue controls: []  
Trading & Technology controls: []  
Shared organization-level control summaries: []  
Recovery assets: []  
Verified backups: []  
Restore drills: []  
Approved RPO/RTO: []  
Open exceptions: []  
Last review: NOT_RECORDED

**Disposition:** NO CONTROL EFFECTIVENESS CLAIM; NO BACKUP/RESTORE/ROLLBACK/RESTART CLAIM; NO SECURITY MONITORING CLAIM.
