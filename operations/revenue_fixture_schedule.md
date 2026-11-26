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
    request = ScheduledRequest("local-coding-example", fixed_review_scope("coding"), 130, priority=2)
    scheduler.schedule(request)           # QUEUED
    result = scheduler.run_next()        # REVIEW_READY for internal review
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

Queue order is lower integer priority first (0 to 9, default 5), then
earliest expiry, then lexical request ID. Priority is part of the exact
idempotent payload. It never changes cost, review or approval rules.
`run_next()` selects and claims the next eligible work in the same SQLite
transaction. `run_one(request_id)` only claims that request when it is next
in order. An occupied worker slot leaves other requests queued; no worker
is spawned in the background. The cap is one reserved worker per fixture
database, including across concurrent scheduler handles.

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
Late output cannot overwrite a supervisor hold. A hold from an interrupted
claim retains the reservation until the original worker actually returns.
An unknown worker outcome can block the queue indefinitely. The fixture
has no control to clear a reservation by assertion. This avoids starting a
second worker while the original is unaccounted for. The existing worker's
bounded local retries remain inside its single scheduled claim.

Create new databases with `revenue_fixture_schedule.sql`. With all clients
stopped, apply `revenue_fixture_schedule_v2.sql` once to a previously
provisioned v1 fixture database. Existing request bytes retain exact
idempotency under default priority 5. Legacy running claims and interrupted
holds preserve a reservation rather than assuming their worker stopped.
This single-database guarantee does not cover parallel copies or rollback.

## Authenticated recovery seam for in-process fixtures

A new claim records the Linux boot, process namespace, effective UID, PID
and start ticks with the reservation. With an independently provisioned
current `RecoveryAuthority`, `reservation_claim(request_id)` reads the
company-private held claim. Separate supervisor `ar_cto` and Security &
Recovery `sr_backup_recovery` principals sign `RecoveryAuthorization`
through the canonical `recovery_payload`, using distinct Ed25519 keys.
Signatures bind the exact company, request digest, deadline, process
identity, trust epoch and short validity window. Real provisioning,
revocation and independent authority remain commissioning requirements.

`release_interrupted_reservation(authorization)` checks current trust,
signatures and actual Linux process identity before atomically recording
private recovery custody and freeing the slot. The original request
remains terminal `SUPERVISOR_HOLD`. It cannot run again or produce a
delivery receipt. A later separate queued request may use the free slot.
Same-boot, namespace and UID checks are required. A kernel signal-0
existence check delivers no signal. A present original claimant, ambiguous
PID observation, expired/changed trust, mismatch or failed atomic write
leaves the reservation in place. Clock rollback or uncertainty blocks.

Only the coding, AI workflow and static fictional terms fixtures qualify
because their selected workers execute in-process. The app fixture can
spawn a child. A parent exit cannot establish custody of that descendant,
so its interrupted reservation remains blocked. Legacy untracked claims,
reboot/cross-namespace recovery, production process proof, remote work and
snapshot rollback are outside the supported boundary. The external trust
provider must maintain a genuinely current authority. SQLite compare-and-set
does not make external revocation atomic with local commit.

New fixture schemas include process ownership. For an existing v2 fixture
database, stop all scheduler clients and apply
`revenue_fixture_schedule_v3.sql` once. For v1, apply v2 first. No process
ownership is synthesized for an existing claim.

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
python -m unittest -v test_revenue_reservation_recovery test_revenue_priority_schedule test_revenue_fixture_schedule
python -m unittest discover -v
```
