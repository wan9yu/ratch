#!/usr/bin/env bash
# Local equivalent of CI: install, test, self-host gate.
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python}"
"$PYTHON" -m pip install -e ".[dev]"
"$PYTHON" -m pytest -q
"$PYTHON" -m ratch check
