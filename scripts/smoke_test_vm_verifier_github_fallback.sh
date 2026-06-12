#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier GitHub fallback fails closed ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY_SCRIPT="$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-fallback-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/curl" <<'EOF'
#!/usr/bin/env bash
printf '{"sha":null}\n'
EOF
chmod +x "$BIN_DIR/curl"

STATUS=0
OUTPUT="$(PATH="$BIN_DIR:/usr/bin:/bin" UNIFAI_VM_VERIFY_FORCE_NO_GH=1 WORK_DIR="$TMP_DIR/work" "$REAL_BASH" "$VERIFY_SCRIPT" 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Verifier unexpectedly succeeded without gh and without a resolvable SHA."
  exit 1
fi

if ! grep -Eq "gh (disabled by UNIFAI_VM_VERIFY_FORCE_NO_GH|not found); using curl-based GitHub API fallback" <<<"$OUTPUT"; then
  echo "[FAIL] Expected no-gh fallback message missing."
  exit 1
fi

if ! grep -q "Could not resolve commit SHA" <<<"$OUTPUT"; then
  echo "[FAIL] Expected SHA resolution failure message missing."
  exit 1
fi

echo "[PASS] Verifier GitHub fallback failed closed as expected."
