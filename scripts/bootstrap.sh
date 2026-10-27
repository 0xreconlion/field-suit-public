#!/usr/bin/env bash
# Get a fresh clone to a runnable state. No network, no installs, no API key.
#
# There is nothing to install: this kit has zero runtime dependencies on
# purpose. That is a security property (it removes the kit's own supply-chain
# surface) and a practical one (it runs on a locked-down machine that cannot
# pip-install anything).
set -euo pipefail
cd "$(dirname "$0")/.."

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    v=$("$c" -c 'import sys;print("%d%02d"%sys.version_info[:2])' 2>/dev/null || echo 0)
    if [ "$v" -ge 309 ]; then PY="$c"; break; fi
  fi
done
if [ -z "$PY" ]; then
  echo "need Python 3.9 or newer; none found" >&2; exit 1
fi

echo "interpreter: $PY ($($PY --version 2>&1))"
echo "dependencies: none"
echo
echo "run the gate suite:   $PY evals/run.py"
echo "configure for an org: $PY scripts/configure.py --template"
echo "verify public export: $PY scripts/verify-public-export.py"
