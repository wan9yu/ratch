#!/usr/bin/env bash
# The gate: install, test, self-host. CI and publish call this file.
set -euo pipefail
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  PYTHON="${PYTHON:-python3}"
else
  PYTHON="${PYTHON:-python}"
fi
"$PYTHON" -m pip install -e ".[dev]"
"$PYTHON" -m pytest -q
"$PYTHON" -m ratch check --compact
