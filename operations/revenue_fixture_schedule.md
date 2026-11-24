# Aevora AI company-local fixture scheduling

The scheduler wraps the existing four synthetic commercial workflows,
including the static fictional security-terms review. It uses the standard
library and a deliberately provisioned separate SQLite database. It does
not install, configure or invoke Paperclip, Ruflo or a model. Production
commissioning and global approval gates remain on hold.

On a network-denied local checkout, run from `operations`:

```python
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from revenue_commercial_scope import fixed_review_scope
from revenue_fixture_schedule import FixtureScheduler, ScheduledRequest

with TemporaryDirectory() as temp:
    path = Path(temp) / "aevora-synthetic-schedule.sqlite"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(Path("revenue_fixture_schedule.sql").read_text())
    scheduler = FixtureScheduler(database=path, clock=lambda: 100)
    request = ScheduledRequest("local-coding-example", fixed_review_scope("coding"), 130)
    scheduler.schedule(request)           # QUEUED
    result = scheduler.run_one(request.request_id)  # REVIEW_READY for internal review
    private = scheduler.private_result(request.request_id)
    assert result.release_authorized is False
```

Only the exact synthetic AI Revenue company, recipient, work scope, service,
zero-cost request and denial of external approval can enter the queue.
An unexpired request must be between 1 and 300 seconds ahead of the trusted
fixture clock. The persistent clock rejects backwards observations. The
request ID is idempotent for the exact canonical payload. Reuse with another
payload blocks. A `BEGIN IMMEDIATE` transaction persists and checks one
claim before the existing anchored-only worker can run.

The claim closes after at most 30 seconds and never later than the request
expiry. Worker failure or late output becomes a terminal `SUPERVISOR_HOLD`.
An expired claim left by interruption can be marked held using the fixture
role `ar_cto`:

```python
scheduler.recover_interrupted(request.request_id, supervisor_role="ar_cto")
```

This fixture label is not real authenticated role authority. There is no
automatic restart, retry, publication or release. Retrying `run_one` after a
claim returns its persisted state and never starts a second work attempt.
Late output cannot overwrite a supervisor hold. The existing worker's
bounded local retries remain inside its single scheduled claim.

Successful private results retain the canonical report, anchored receipt
and exact report digest. Readback checks the digest, scope and no-release
invariants. The anchored demonstration's own temporary custody lifetime is
unchanged. This scheduler is not an independently administered audit store,
remote lease service, signature re-verifier or production rollback anchor.
A coordinated database rollback or corrupted host is outside its guarantee.
OCC continues to receive only the separate existing read-only aggregate.
Private scheduler state, results and review data remain company-local.

Production requires independently authenticated company roles, a trusted
clock and store, current revocation, witnessed recovery and durable evidence
custody. A native worker runtime must prove identity, scope and tool
isolation independently. No operational approval is granted by the fixture.

```sh
python -m unittest -v test_revenue_fixture_schedule
python -m unittest discover -v
```
