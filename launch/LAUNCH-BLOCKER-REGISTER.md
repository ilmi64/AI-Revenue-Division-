# Organisation Launch Blocker Register

**Status:** Initial evidence-based register; owners and due dates require assignment

| ID | Priority | Area | Blocker | Exit evidence required |
|---|---|---|---|---|
| LB-001 | Critical | OCC governance | No verified accountable owners, backups or incident command across divisions | Owner-approved role/backup roster and tested escalation |
| LB-002 | Critical | Testing | Existing validators/regression suites have not been executed against current exact commits | Reproducible results, environment, commit SHAs and defect triage; no Actions until released |
| LB-003 | Critical | Security | No demonstrated production-grade secrets management, least privilege, isolation, access review or credential rotation | Security architecture review and tests; no secrets in repo/logs |
| LB-004 | Critical | Operations | No verified always-on runtime, monitoring, alert delivery, operator coverage or tested recovery | Supported host, named operators, uptime/alert/stop/restart evidence |
| LB-005 | High | Data governance | Market-source rights, terms, Canadian/Ontario availability and retention permissions pending | Source-by-source approval and documented permitted use |
| LB-006 | High | Research quality | Independent corroboration, freshness, outage and disagreement tests incomplete | Test evidence and validated source semantics |
| LB-007 | High | Finance | No verified bank connection, opening cash reconciliation, approved commitments or named sign-off owner | Reconciled records, owner assignments, reserve/liability review and close sign-off |
| LB-008 | High | Risk | Ratings provisional; incident/evidence records unpopulated; no protected evidence store or recovery rehearsal | Owner-reviewed risks, populated test records, access controls and recovery evidence |
| LB-009 | High | AI workforce | Qwen end-to-end unverified; Llama not installed; role templates are not staffed agents | Runtime benchmark, permissions, bounded task acceptance and human override tests |
| LB-010 | High | PolyBot | Real Pump.fun create/createV2 and CPI/inner-instruction coverage unverified | Read-only real transaction fixtures and independent review |
| LB-011 | High | PolyBot | Two independent RPC providers not configured/tested; failover not proven | Provider independence, failover, rate-limit and consistency evidence |
| LB-012 | High | Strategy validation | No qualifying real out-of-sample dataset; spread, impact, latency and exit assumptions uncalibrated | Timestamped representative dataset, bias controls, reproducible replay and independent review |
| LB-013 | High | PolyBot state | PR #42 staged-exit reconciliation tests not run in this session | Exact-head local test evidence; persistence/restart/no-fill/failure scenarios |
| LB-014 | High | Ontario/product compliance | Exact broker/product eligibility and legal structure require review; CFD/FX/derivative suitability not established | Current official terms, registration/eligibility review and qualified advice as required |
| LB-015 | High | TISRD data rights | Candidate platforms restrict scraping, profiling, monitoring, copying or commercial reuse | Permission for exact collection/use; excluded sources remain excluded |
| LB-016 | High | Revenue | No validated recurring revenue or reconciled operating cash demonstrated | Accepted work, completed delivery, invoicing and reconciled cash receipt |
| LB-017 | High | Ecommerce | Supplier, shipping, platform, tax, return, payout and demand inputs unverified | Supplier evidence, costed samples and verified unit economics; no purchase without approval |
| LB-018 | High | Business/Commercial | No approved offer catalogue, delivery capacity, contract/privacy terms or verified customer demand | Costed offers, legal review, capacity and owner-approved go-to-market |
| LB-019 | Medium | AI Revenue | Opportunities, Canada eligibility, fees and payout terms require refresh | Dated evidence and eligibility review before application |
| LB-020 | Medium | Documentation | Cross-repository dependency chain and PR base/head freshness need final review | Exact dependency graph, merge order, conflict review and owner approval |
| LB-021 | Medium | Animora | Animora intentionally paused by owner | No action; preserve work and keep excluded |
| LB-022 | Medium | GitHub Actions | Actions intentionally held to preserve next 2,000 minutes | Owner explicitly releases hold; prioritize essential validation only |

## Handling rules

- Every blocker needs an accountable owner role, target date, evidence and status before launch review.
- A blocked capability may be excluded from restricted launch only if dependencies are isolated and exclusion explicit.
- No critical blocker may be waived by an agent or model.
- High blockers cannot be silently reclassified to make launch appear ready.
- Closing a blocker requires evidence and reviewer acknowledgement, not narrative status.
