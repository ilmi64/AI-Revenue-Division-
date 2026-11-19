# OCC Independent-Feed Agreement Diagnostic Contract

## Purpose

This module compares caller-supplied observations for one exact canonical
instrument identity. It reports basic quote agreement or conflict for
diagnostic and engineering purposes only. It does not fetch, poll, subscribe
to, authenticate or persist market data.

## Inputs and validation

- A complete canonical instrument identity.
- A sequence of observations, each checked again using the OCC market-data
  observation validator.
- A caller-supplied source registry, structurally revalidated at the supplied
  current time.
- Exact source ID, adapter ID, provider ID, venue and instrument identity
  matching. Symbol-only matching is never used.
- One observation per source and adapter; duplicate source/event IDs are
  rejected. Positive ordered bid/ask, sequence and timestamps are rechecked.
- Only records claiming APPROVED_FOR_PAPER are included. This state is only a
  caller-supplied registry claim, not authenticated approval.

## Diagnostic method

The midpoint of each accepted bid/ask is calculated. The median midpoint is
reported as a diagnostic statistic, not an authoritative price. The spread is
(maximum midpoint - minimum midpoint) / median midpoint, expressed in basis
points. A configurable threshold defaults to 25 bps.

The module reports:
- INPUTS_REJECTED when any supplied observation cannot be matched or validated.
- INSUFFICIENT_SOURCES when fewer than the configured minimum (at least two)
  observations are accepted.
- DECLARED_GROUPS_NOT_INDEPENDENTLY_VERIFIED when too few distinct declared
  independence-group labels are present.
- CONFLICT_DETECTED when the diagnostic spread exceeds the threshold.
- AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED when the spread is within threshold.

A conflict is a diagnostic disagreement, not proof of which feed is wrong.
Agreement is not proof that any quote is accurate.

## Trust and release boundary

Independence-group labels, provider IDs, adapter IDs, venue labels, review
states and evidence references remain caller-supplied claims. Distinct group
labels do not establish distinct beneficial ownership, upstream liquidity,
hosting, infrastructure, data vendors or parser provenance.

Every result therefore sets independence_verified, provider_identity_authenticated,
registry_authority_authenticated, market_data_trusted, consensus_authorized,
paper_use_authorized and execution_eligible to false. Even an
AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED result is not a trusted consensus or
approved price.

The implementation has no network, credentials, persistence, scheduler,
notifications, broker, exchange, wallet or execution capability.

## Test and operational status

Tests are authored but have not been executed. GitHub Actions remain on quota
hold. No provider or feed is approved by this change.
