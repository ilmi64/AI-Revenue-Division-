# Independent company authority and delegation contract

Status: proposed governance contract; no production authority service exists.

## Separate authorities
AI Revenue and Trading & Technology each require a separate owner-controlled
approval authority and company policy namespace. Shared OCC may publish
health summaries and coordinate requests but may not mint, alter, consume or
revoke company approvals.

The authority service must validate:
- owner identity through a separately administered authentication factor;
- exact company, principal, session, task, operation and resource;
- recipient/account, amount and currency where relevant;
- policy version, expiry, nonce and one-time consumption;
- current revocation and emergency-stop state.

## Separation of duties
- AI agents may propose; they cannot approve their own consequential actions.
- The model/runtime operator cannot administer owner signing keys.
- The policy administrator cannot silently rewrite immutable audit history.
- The audit verifier is read-only and independently administered.
- The receiver/evidence issuer is distinct from the agent requesting dispatch.
- OCC cannot approve a company's action merely because it coordinates the task.
- Company executives may approve only within their delegated, non-reserved scope.

## Delegation
A cross-company delegation must identify the source and destination company,
purpose, allowed fields/resources, permitted operation, maximum amount if any,
expiry, revocation path and audit destination. Default is deny. No wildcard
delegation, transitive authority, implicit consent or model-consensus approval.
The receiving company may narrow but never widen the granted scope.

## Reserved owner decisions
Owner approval remains required for spending, paid services, account or
permission changes, external publication/commitments, deployment, repository
merges, live trading, wallet signing, transfers, withdrawals, changes to risk
limits/halt controls and any irreversible external action.

## Incident independence
A company can stop its own actions without the other company's cooperation.
OCC can raise an incident and request a stop, but cannot silently clear a
company's stop. Recovery requires fresh identity, revocation, evidence and
audit checks plus the required owner authorization.

## Implementation blockers
Separate asymmetric signing keys and issuers; hardware-backed key custody;
durable approval consumption; independent audit storage; policy enforcement
at every gateway; verified tenant-aware data stores; break-glass procedure;
key rotation/revocation; tested backup/restore; and external security review.
