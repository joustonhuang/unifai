#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier red-path propagation ==="

TMP_DIR="$(mktemp -d -t unifai-vm-verifier-red-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT="$TMP_DIR/vm-bootstrap-report.txt"
STATUS=0

VM_REPORT="$REPORT" bash -s <<'EOF' || STATUS=$?
set -euo pipefail
FAILURES=0

mark_fail() {
  echo "[FAIL] $1"
  FAILURES=$((FAILURES + 1))
}

{
  echo "== red-path self-test =="
  mark_fail "Forced smoke failure for verifier red-path validation"
} > "$VM_REPORT" 2>&1

cat "$VM_REPORT"

if [ "$FAILURES" -ne 0 ]; then
  echo "[FAIL] VM verification found ${FAILURES} failing checks"
  exit 1
fi

echo "[PASS] VM verification checks passed"
EOF

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Verifier red-path self-test unexpectedly passed."
  exit 1
fi

if ! grep -q "Forced smoke failure for verifier red-path validation" "$REPORT"; then
  echo "[FAIL] Expected forced failure evidence missing from report."
  exit 1
fi

if ! grep -q "== red-path self-test ==" "$REPORT"; then
  echo "[FAIL] Expected report header missing from report."
  exit 1
fi

echo "[PASS] Verifier red-path self-test failed closed as expected."
