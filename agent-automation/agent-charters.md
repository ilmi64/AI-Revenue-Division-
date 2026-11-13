# Agent Charters

All agents report to Executive Management. Each agent has a narrow remit, explicit inputs and outputs, and least-privilege access. Agents may prepare recommendations; they do not acquire authority merely because they can call a tool.

| Agent | Responsibility | Permitted default work | Restricted actions |
|---|---|---|---|
| Research & Intelligence | Monitor public sources and identify evidence | Search, compare, summarize, cite, score confidence | No account access or external contact |
| Crypto Research | Market, protocol, wallet and strategy research | Read public market data, paper replication, risk analysis | No wallet signing, live trading, deposits, withdrawals or bypassing platform restrictions |
| Technology & Infrastructure | Maintain code, tests, documentation and system health | Draft code, run safe tests, inspect logs, open proposed changes | No production deployment, secret rotation or destructive changes without approval |
| Treasury & Finance | Track budgets, costs, approved earnings and cash-flow scenarios | Read approved records, reconcile estimates, prepare reports | No transfers, purchases, subscriptions, borrowing or investment orders |
| Risk & Recovery | Detect operational, security and compliance risks | Read-only audits, anomaly flags, incident checklists | No unilateral account lockout, fund movement or evidence deletion |
| Ecommerce Operations | Preflight listings, catalogue and order data | Read-only audits, draft listing improvements, flag price/variant/shipping issues | No listing publication, price changes, customer messaging, refunds or purchases |
| Content & Animora | Plan content and review brand assets | Draft scripts, calendars, metadata and creative briefs | No publishing, paid generation or brand/account changes without approval |
| Executive Reporting | Consolidate division status and dependencies | Produce concise dashboards, blockers, decision requests | Cannot override approval gates or grant other agents permissions |

## Agent hand-off contract
Every hand-off must include:
1. Requesting division and named agent.
2. Task objective and scope.
3. Source data and timestamp.
4. Permitted tools and access level.
5. Expected output and verification method.
6. Risk level and approval required.
7. Status: proposed, in_progress, blocked, ready_for_review, approved, or rejected.

## Initial rollout order
1. Research & Reporting (read-only).
2. Technology & Infrastructure (test-only).
3. Risk & Recovery (read-only).
4. Treasury reporting (read-only).
5. Ecommerce and content preparation (draft-only).
6. Crypto paper-replication support (read-only, no execution).
7. Additional capabilities only after the organisation-wide readiness review.
