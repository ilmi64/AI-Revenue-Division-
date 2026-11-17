# Gold Desk — XAUUSD Data Quality and Instrument Controls

**Status:** Research/paper contract only. No broker feed, live pricing, trading or product approval is implied.

## Instrument identity must remain explicit

Never collapse these into one continuous price series without a documented transformation:
- Indicative bullion spot (dealer/reference quote).
- Broker-specific XAUUSD spot-style quote.
- Gold CFD quote, including broker-specific contract terms.
- COMEX gold futures contract, with exact contract month and expiry.
- Synthetic test observations.

Each observation must preserve instrument type, provider/venue, exact symbol or contract code, quote basis, currency, unit, multiplier, source timestamp, receive timestamp and evidence reference.

## Mandatory Gold quality fields

For Gold observations, require:
- `gold_price_basis`: broker executable XAUUSD, indicative bullion spot, COMEX futures, gold CFD or synthetic test.
- `quote_unit`: explicit quote convention (for example USD per troy ounce) or contract unit.
- `unit_or_contract_multiplier`: verified instrument-specific quantity; never assume one ounce or one standard lot.
- `gold_session`: named session plus source timezone/calendar; unknown session blocks qualification.
- `quote_age_seconds`, `stale_threshold_seconds`, `is_stale`: stale if age exceeds threshold or the source marks it stale.
- `session_state`: open, closed, auction, halted or unknown.
- `roll_status`, `contract_code`, `expiry_utc`: mandatory for futures.
- `spot_futures_basis`: only when both legs are time-aligned and independently sourced; otherwise null.
- `financing_status` and `settlement_type`: explicit unknown/not-reviewed values are valid for research but block any product suitability claim.

## Hard data-quality stops

- Spot, futures, CFD or indicative bullion basis is ambiguous.
- Source or licence is unknown, stale, delayed beyond permitted research use, or incorrectly labelled.
- Quote is crossed, non-finite, missing bid/ask, or bid exceeds ask.
- Contract size, ounce conversion, currency conversion, expiry or roll mapping is unknown.
- Session/holiday calendar is unavailable or clock skew exceeds the desk's configured tolerance.
- A price is being carried forward after provider outage or silently spliced across providers.
- Financing, swap, settlement or counterparty structure is unknown where product suitability is being assessed.

## Halal and product-structure boundary

Gold as an asset does not make every instrument or transaction structure permissible. Physical allocated ownership, unallocated claims, spot-style broker products, CFDs and futures differ materially. Record possession/settlement, leverage/margin, shorting, financing/swap, rollover, counterparty and broker terms. Mark the assessment **unassessed** until an instrument-specific Shariah review is completed; do not let a model issue a blanket halal label.

## Research outputs

The Gold Desk may report data quality, basis observations, session/liquidity context, macro drivers, event risks, contract/roll issues and paper-study hypotheses. It may not issue orders, trade sizing, leverage settings or execution permission.
