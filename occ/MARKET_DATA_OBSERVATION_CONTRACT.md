# OCC Market-Data Observation Contract

## Purpose

This contract validates one caller-supplied quote against an exact canonical
instrument identity before a paper component consumes it. It is not a feed
client, provider registry, consensus engine, price oracle, strategy, risk
approval or execution interface.

## Required fields

- instrument_identity: complete identity accepted by the OCC instrument identity validator.
- provider_id and event_id: non-empty caller-supplied provenance labels.
- venue: must exactly match the expected identity's venue.
- bid and ask: finite, positive numbers with bid <= ask.
- observed_at_epoch: source observation time.
- received_at_epoch: receive time supplied by the caller.
- sequence: positive integer.

The consumer supplies expected_identity and now_epoch. Default maximum age is
30 seconds and allowed future skew is 5 seconds. Callers may tighten limits
for a particular market/session. Negative limits are rejected.

## Fail-closed rules

Reject if either identity is incomplete, any canonical identity field differs,
venue differs, provenance labels are missing, quotes are non-finite/non-positive/
crossed, sequence is invalid, timestamps are invalid/future/out of order, or
the observation is stale. Never silently replace a rejected observation with
a stale quote or another instrument's quote.

## Trust boundary

The result always sets source_authenticated, independent_source_verified,
market_data_trusted and execution_eligible to false. Provider IDs, event IDs,
venue labels, timestamps and quote values remain caller-supplied claims.
Passing validation does not authenticate transport/TLS, provider ownership,
exchange origin, clock discipline, event uniqueness, source independence or
contract correctness. A separately reviewed adapter registry and
independent-feed policy would be needed before any source could be approved
even for paper use.

## Market-specific safeguards

Gold spot, gold futures, physical bullion, tokenized gold and CFDs must retain
distinct identities. XAUUSD observations cannot be substituted for a futures
contract or evidence of bullion ownership, possession or delivery. FX, index
cash, index futures and crypto spot/perpetual products must likewise retain
distinct identities and quote/settlement conventions. CAD-denominated token
exit marks are not reusable for Gold, FX or indices.

## Release status

Tests are authored but not executed. GitHub Actions remain on quota hold.
This validator has no network, credentials, broker/exchange/wallet access,
persistence, scheduler, notification or order-execution capability.
