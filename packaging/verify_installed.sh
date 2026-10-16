#!/usr/bin/env bash
set -euo pipefail
verification_log="$(mktemp)"
trap 'rm -f "$verification_log"' EXIT
if ! packaging/run_checks.sh env -u PYTHONPATH python3 packaging/verify_installed.py > "$verification_log" 2>&1; then
  cat "$verification_log"
  exit 1
fi
cat "$verification_log"
if grep -Eq 'Failed to load icon|Unrecognized image file format|AdwSwitchRow .*can only be placed' "$verification_log"; then
  exit 1
fi
