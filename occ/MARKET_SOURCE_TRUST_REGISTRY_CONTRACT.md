# OCC Market-Source Trust Registry Contract

## Purpose

The registry schema records source/adapter review metadata and validates its
shape. It is not an authenticated approval system, provider verification
service, feed client or consensus engine.

## Required entry fields

Each record identifies source_id, adapter_id, venue, endpoint, transport,
parser_version, independence_group, complete canonical instrument_identity,
and review_state. Supported transport labels are HTTPS, WSS, LOCAL_FILE and
MANUAL. These are descriptive labels, not transport verification.

Review states:
- UNREVIEWED: no approval claim.
- REVIEW_REQUIRED: further evidence is needed.
- APPROVED_FOR_PAPER: a caller-supplied review claim, requiring reviewer_id,
  review_evidence_ref and reviewed_at_epoch.
- REVOKED: requires a revocation_reason.

Duplicate source/adapter/instrument identities are rejected. Venue must match
the venue in the canonical instrument identity. Future review timestamps are
rejected.

## Approval and independence trust boundary

All reviewer IDs, evidence references, endpoint strings, transport labels,
parser versions, independence groups and review states are caller-supplied.
The validator cannot authenticate a reviewer, inspect evidence, resolve an
endpoint, verify TLS, inspect parser code, prove provider ownership or establish
that two feeds are independent.

Consequently, even a structurally valid APPROVED_FOR_PAPER entry does not
make a source trusted or authorize paper use. The result always reports
registry_authority_authenticated=false, any_source_trusted=false,
paper_use_authorized=false and execution_eligible=false.

The independence helper reports only distinct declared group labels. It never
claims independence_verified or authorizes multi-source consensus.

A future trusted host must own the registry, authenticate reviewer roles,
bind approvals to immutable adapter/configuration hashes, retain evidence,
record change history, monitor revocations and fail closed when registry
integrity or freshness is uncertain. None of those mechanisms are implemented
here.

## Market safeguards

Approvals must be scoped to the exact instrument identity, venue, adapter and
parser version. Gold spot, gold futures, allocated bullion, tokenized gold and
CFDs require separate records. Gold evidence must separately address ownership,
possession, settlement, delivery, custody, financing and margin; this registry
does not issue legal or religious rulings.

## Release status

Tests are authored but not executed. GitHub Actions remain on quota hold.
No network, credentials, persistence, scheduler, notification, broker,
exchange, wallet or execution capability is present.
