# Multi-Process Concurrency Validation Contract — Linearizable Control Store

Status: design/acceptance contract only. No multi-process test has been executed. This contract does not upgrade the SQLite reference to production status.

## Purpose

The existing 27-method suite uses multiple SQLite connections and threads in one Python process. That is useful but does not prove behavior across independent OS processes, process termination, or a production multi-node database. This contract defines the next validation layer using the exact same database file and independent process-owned connections.

## Test harness requirements

- Use a temporary local filesystem directory and one pre-created SQLite database file.
- Initialize schema and synthetic fixtures before starting worker processes.
- Each worker must construct and close its own `LinearizableControlStore` connection inside the child process. Never inherit or share a live SQLite connection across a process boundary.
- Use the multiprocessing `spawn` start method for portable process isolation. Do not depend on fork-inherited locks or connections.
- Coordinate race starts with a process-safe barrier/event and bounded timeouts. Do not use sleeps as the sole race-ordering mechanism.
- Set explicit process join timeouts; fail the test if a worker hangs. Capture child exceptions and return values through a process-safe result channel.
- Keep all data synthetic. No network, sender, wallet, broker, account, credential, or external service may be involved.
- Run against the exact fetched source/test commit and record Python version, SQLite version, OS, filesystem type, commit SHA, test command, full output and exit code.
- Run the same test suite separately against both company repository checkouts. Confirm source and test blob SHAs before comparing results.

## Required scenarios and invariants

1. **Dispatch versus quarantine, both possible serial orders**
   - Race one worker calling `authorize_and_start` against another calling `quarantine` for the same company/stream.
   - If dispatch authorization commits first, it may return allowed and the action must be recorded as `dispatch_started`; quarantine must then increment the epoch and quarantine the stream. The action remains potentially in flight and is never silently reset or auto-resubmitted.
   - If quarantine commits first, dispatch must be denied and must not consume the approval or set `dispatch_started`.
   - In either ordering, no dispatch authorization may commit after the quarantine transaction has committed while the stream remains quarantined.
   - Inspect audit ordering, epoch, approval consumption and action state after both processes exit.

2. **Two independent actions competing for one approval**
   - Enqueue two different immutable actions that reference the same approval.
   - Race two processes attempting authorization.
   - Exactly one action may consume the approval and enter `dispatch_started`; the other must fail closed. There must be one consumption record and no duplicate authorization.

3. **Release versus dispatch**
   - Start with a quarantined stream and an old queued action.
   - Race a release transaction against dispatch authorization for that old action.
   - The old action must never become dispatchable across release: if dispatch sees quarantine it is denied; after release the epoch mismatch must fence the old action.
   - A new action enqueued during quarantine must also remain fenced after release.

4. **Release replay across processes**
   - Race two processes presenting the same exact owner approval and nonce for one incident/checkpoint.
   - Exactly one release may commit; the other must be rejected as replay/conflict or observe the already-released state without performing a second transition.
   - Verify one consumption row, one release audit event, and one epoch increment.

5. **Quarantine idempotency across processes**
   - Race duplicate quarantine requests for the same company, stream, incident and checkpoint.
   - Resulting state must contain one effective epoch increment and one corresponding quarantine event for that incident/checkpoint.
   - A different incident/checkpoint must not be silently treated as the same request.

6. **Process crash before commit**
   - Terminate a worker while it holds an uncommitted transaction using a controlled test hook.
   - On restart, SQLite must recover a valid database; no partial approval consumption, action transition, audit append or quarantine/release state may remain.
   - Do not simulate this by killing a process at an uncontrolled arbitrary point only; record the exact injected crash point.

7. **Process crash after dispatch authorization commit**
   - Commit `dispatch_started`, then terminate the worker before any sender exists.
   - On restart, the action must remain in-flight/ambiguous and must not be automatically resent or have its approval reused.

8. **Busy timeout and lock contention**
   - Hold a write lock in one process while another attempts an operation.
   - Verify bounded timeout behavior, no partial state, no false replay classification and fail-closed handling when the lock cannot be acquired.
   - Record actual SQLite busy/locked exception mapping. If the reference leaks an unclassified storage exception, treat it as a defect to fix before claiming robustness.

9. **Database integrity and audit verification after restart**
   - Reopen the same database from a fresh process.
   - Verify SQLite integrity, per-company audit chains, stream status/epoch, approval consumption, action state and outbox contents.
   - Verify a corrupted database or audit chain blocks release/dispatch in the production integration; the local reference alone does not establish every production boundary.

10. **Company isolation under concurrent writers**
    - Race independent operations for two companies sharing the test file only as a stress fixture.
    - Verify every audit, approval, action, stream, release consumption and outbox event remains bound to its company and no cross-company read/write occurs through the public API.
    - Production must still use independently enforced company isolation; a shared SQLite test file is not evidence that one database is an acceptable multi-company production topology.

## Pass criteria

- Every required scenario executes repeatedly with deterministic synchronization and bounded completion.
- No duplicate approval/nonce/action consumption; no stale-epoch authorization; no partial transaction state; no silent automatic resend.
- Both company checkouts produce matching outcomes for identical source/test SHAs.
- Full test output, environment metadata, and all failure traces are retained.
- Any flaky test, uncaught storage failure, ambiguous state transition, or unexplained audit mismatch is a failure, not a warning.

## Non-goals and production blockers

- Passing these tests proves only behavior of the tested SQLite build and local filesystem configuration. It does not prove multi-host consensus, replicated-database behavior, failover fencing, cloud storage durability, or production transaction isolation.
- The sender and receiver remain absent. Receiver-side idempotency, destination binding, signed evidence, and recovery-epoch enforcement require separate integration tests.
- The production identity issuer, deterministic policy gateway, owner-approval verifier, recovery assessor, secure key custody, signed audit checkpoints, and independently administered WORM store remain mandatory.
- No live trading, wallet signing, funds transfer, broker/exchange order, withdrawal, or external publication is part of this validation.

## Decision gate

Do not merge or deploy based on this contract. First execute the current 27-method suite; then implement and execute this multi-process suite in an explicitly approved no-cost environment. Keep both pull requests draft until the full evidence package and independent review are complete.
