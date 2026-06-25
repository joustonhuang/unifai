#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier announces unauthenticated gh fallback ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY_SCRIPT="$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-gh-unauth-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/gh" <<'EOF'
#!/usr/bin/env bash
if [ "${1:-}" = "auth" ] && [ "${2:-}" = "status" ]; then
  exit 1
fi
printf 'unexpected gh args: %s\n' "$*" >&2
exit 1
EOF

cat > "$BIN_DIR/curl" <<'EOF'
#!/usr/bin/env bash
printf '{"sha":null}\n'
EOF

chmod +x "$BIN_DIR/gh" "$BIN_DIR/curl"

STATUS=0
OUTPUT="$(PATH="$BIN_DIR:/usr/bin:/bin" WORK_DIR="$TMP_DIR/work" "$REAL_BASH" "$VERIFY_SCRIPT" 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Verifier unexpectedly succeeded with unauthenticated gh and an unresolvable SHA."
  exit 1
fi

if ! grep -q 'gh is installed but not authenticated; using curl-based GitHub API fallback' <<<"$OUTPUT"; then
  echo "[FAIL] Expected unauthenticated-gh fallback message missing."
  exit 1
fi

if ! grep -q 'Could not resolve commit SHA' <<<"$OUTPUT"; then
  echo "[FAIL] Expected SHA resolution failure message missing."
  exit 1
fi

echo "[PASS] Verifier announced unauthenticated gh fallback and failed closed as expected."
