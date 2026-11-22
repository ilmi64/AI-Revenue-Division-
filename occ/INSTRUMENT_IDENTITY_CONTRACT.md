# OCC Canonical Instrument Identity Contract

## Purpose

`occ.instrument_identity` validates a descriptive identity for a market instrument before market-specific research or paper components consume it. It prevents components from silently treating products with similar symbols as interchangeable.

This is an identity and data-shape contract only. It does not authenticate the venue, verify contract specifications, fetch quotes, establish legal ownership, prove possession or delivery rights, evaluate halal compliance, or authorize execution.

## Required fields

- `market_class`: CRYPTO, FOREX, INDICES, METALS, EQUITIES or OTHER.
- `product_type`: SPOT, FX_SPOT, INDEX_CASH, CFD, FUTURE, OPTION, TOKEN, TOKENIZED_ASSET, ETF or OTHER.
- `venue`: explicit venue/provider/exchange/broker label supplied by the caller.
- `symbol`: exact venue-specific symbol or contract identifier.
- `quote_currency`: explicit quote/settlement currency code.
- `contract_unit`: explicit unit, such as `troy_ounce`, `one_eur`, `index_point`, `one_token`, or venue-defined contract unit.
- `settlement_method`: CASH, PHYSICAL_DELIVERY, NET_CASH, TOKEN_DELIVERY or UNKNOWN.

FX_SPOT additionally requires an explicit `base_currency`. FUTURE requires an explicit `expiry`. Spot/cash products reject a futures expiry. Optional `contract_multiplier` must be finite and positive.

## Explicit uncertainty fields

The normalized identity includes custody and financing models. Missing values default to UNKNOWN; they are never inferred from the product name or marketing description.

- Custody: ALLOCATED, UNALLOCATED, SELF_CUSTODY, NOT_APPLICABLE, UNKNOWN.
- Financing: NONE_CONFIRMED, OVERNIGHT_SWAP, INTEREST_BEARING, FUNDING_RATE, MARGIN_FINANCING, UNKNOWN.

The module always emits these safeguards as false:
- `venue_authenticated`
- `contract_terms_verified`
- `ownership_verified`
- `financing_verified`
- `execution_eligible`

A caller-provided venue label, quote currency, contract unit, custody model or financing model is not independently authenticated by this validator.

## Examples of non-interchangeable instruments

- XAUUSD spot quote: metal market, spot product, USD quote, explicit weight unit and unknown custody/settlement until evidenced.
- Gold future: metal market, future product, exact venue contract symbol, USD (or actual) quote, contract unit and explicit expiry.
- EURUSD spot: FX market, FX_SPOT product, EUR base, USD quote and explicit unit.
- Index cash quote: indices market, INDEX_CASH product and an explicit point/quote convention.
- Index future: indices market, FUTURE product, exact contract and expiry; never silently substituted for the cash index.
- Crypto token spot: crypto market and exact venue/token identity; never equated with a CFD or perpetual contract.

These are examples of required distinctions, not assertions that any named venue or instrument is currently supported.

## Integration rules

1. Market adapters must preserve the complete normalized identity with every quote or observation.
2. Consumers must compare the full identity, not just the symbol string.
3. Missing or mismatched identity fields must block the affected paper calculation.
4. Do not reuse CAD token exit marks for Gold, FX or index instruments.
5. A validated identity is not validated market data, strategy approval, risk approval, or operational readiness.
6. Gold requires separate evidence for ownership, possession, settlement timing, delivery rights, custody, financing and margin. The identity module cannot establish these facts.

## Verification status

Unit tests are authored but not executed. This proposed module has no network, broker, exchange, wallet, credential, scheduler, persistence, notification or order-execution capability. GitHub Actions remain on quota hold.
