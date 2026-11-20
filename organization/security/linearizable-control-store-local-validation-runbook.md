# Local Validation Runbook — Unified Control Store

Status: instructions only; no test execution is claimed. Uses Python standard library and a temporary local SQLite database. No network sender, broker, wallet, payment, signing, or live financial action is invoked by this test suite.

## Preconditions

- Use a local checkout of the exact company branch containing this runbook.
- Confirm the reference source and test file are in the same directory.
- Use Python 3.10+ with the standard-library `sqlite3` module available.
- Do not use GitHub Actions, Codespaces, paid runners, paid APIs, or cloud compute for this validation.
- Run from an isolated scratch checkout or disposable worktree; tests create temporary SQLite databases and synthetic fixtures.

## AI Revenue Company

From the repository root:

```sh
python3 -m unittest discover -s organization/security -p 'test_linearizable_control_store_reference.py' -v
```

## Trading & Technology Company

From the repository root:

```sh
python3 -m unittest discover -s docs/security -p 'test_linearizable_control_store_reference.py' -v
```

## Expected scope

- The test suite is synthetic and offline.
- It validates local SQLite transaction behavior, approval consumption, quarantine/release fencing, audit rollback, company separation, amount limits, and hard-deny behavior.
- It does not validate production cryptography, multi-node database behavior, receiver idempotency, remote recovery-epoch enforcement, WORM checkpoints, or deployment security.
- A passing local suite is not a production-readiness decision and does not authorize external dispatch.

## Evidence to retain

- Exact repository, branch, commit SHA, Python version and operating system.
- Full command and complete stdout/stderr, including test count and exit code.
- Any failure logs, with secrets and personal data excluded.
- Do not edit tests or source to make a failed run pass without recording the change and repeating the review.

## Current status

The suite has not been executed in this work session. GitHub Actions and Codespaces were not started. A maintainer must run the command locally and provide the unedited result before the evidence register can move from NOT_RUN.
