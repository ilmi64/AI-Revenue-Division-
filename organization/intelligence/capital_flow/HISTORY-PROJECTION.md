# Capital Flow Event History Projection

`capital_flow_history.py` creates a read-only JSONL projection by combining normalized event records with the verified append-only review ledger.

## Behaviour

- Verifies the review ledger hash chain before projection.
- Requires unique, non-empty event IDs in the normalized event input.
- Fails closed if a review references an event absent from the supplied event file.
- Preserves the original normalized event object unchanged.
- Exposes the full review timeline, review count, current review status and latest review entry.
- A review action without an explicit new status does not erase the previous status.
- Projection is a derived research view, not the authoritative event or ledger record.

## Run

```sh
python capital_flow_history.py --events normalized.jsonl \
  --reviews review-history.jsonl --output event-history.jsonl
python -m unittest -v
```

The review ledger must be verified and the complete event file must be supplied. The output is a local JSONL file. No network, external service, wallet, trade or publishing capability exists.

## Tests

`test_capital_flow_history.py` covers timeline projection, preservation of source records, status carry-forward, duplicate IDs, orphan review rejection and empty review history. Tests are supplied but have not been run in this hosted repository environment.
