#!/usr/bin/env bash
# Safe local OCC regression run. No network, GitHub Actions, credentials or writes
# to persistent OCC ledgers are used; tests operate on temporary fixtures.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT/organization/market-divisions"
python -m unittest discover -s specialist_research -t . -p 'test_*.py' -v

cd "$REPO_ROOT"
python -m unittest discover -s organization/tests -p 'test_build_organisation_dashboard.py' -v
