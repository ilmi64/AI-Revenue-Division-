# Cross-division stop and restart conditions

## Stop immediately

Stop the affected workflow and prevent dependent work from proceeding when any of these occur:

- A credential, secret, wallet key or private key may be exposed.
- An external action occurred without the required approval.
- Data source identity, licensing, Canadian availability or permitted use is unknown.
- Market data is stale, delayed, indicative, reference-only, incomplete or mapped to an uncertain instrument/venue.
- Order, fill, wallet or transaction state is uncertain or cannot be reconciled.
- A required risk limit, owner, approval, dependency or evidence record is missing.
- A deterministic validator or security control fails.
- A material provider, storage, identity or recovery dependency is unavailable.
- A SEV1 incident is declared.

## Containment boundary

The stop applies to the affected system and dependent workflows. Preserve unaffected read-only research where it is safe and lawful. Do not interpret a stop as permission to perform account changes, revoke credentials, contact third parties, move funds or alter production systems; those actions still require owner approval unless a separately approved emergency procedure explicitly covers them.

## Restart gate

Restart only after all applicable conditions are met:

1. Incident owner records the cause or clearly bounded residual uncertainty.
2. Evidence confirms containment and reconciled system state.
3. Required credentials, data sources, permissions and dependencies are verified.
4. Deterministic controls and relevant offline tests pass.
5. Recovery/rollback has been reviewed and is available.
6. Risk reviewer records findings; unresolved critical risks remain blockers.
7. Owner explicitly approves the specific restart scope.

A model-generated recommendation, green dashboard, passing synthetic test or verbal assumption is not restart approval.
