#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM host readiness helper ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
READYNESS_SCRIPT="$REPO_ROOT/scripts/check_vm_host_readiness.sh"
TMP_DIR="$(mktemp -d -t unifai-vm-host-readiness-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
mkdir -p "$BIN_DIR"

for bin in jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen timeout; do
  cat > "$BIN_DIR/$bin" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
  chmod +x "$BIN_DIR/$bin"
done

cat > "$BIN_DIR/gh" <<'EOF'
#!/usr/bin/env bash
if [ "${1:-}" = "auth" ] && [ "${2:-}" = "status" ]; then
  exit 1
fi
exit 0
EOF
chmod +x "$BIN_DIR/gh"

OUTPUT="$(PATH="$BIN_DIR:/usr/bin:/bin" bash "$READYNESS_SCRIPT" 2>&1)"
printf '%s\n' "$OUTPUT"

if ! grep -Eq 'Summary: 8 pass, [23] warn, 0 fail' <<<"$OUTPUT"; then
  echo "[FAIL] Expected synthetic readiness summary missing or drifted."
  exit 1
fi

if [ -e /dev/kvm ] && ! grep -Eq '\[WARN\] /dev/kvm exists but is not writable; verifier will fall back to TCG emulation' <<<"$OUTPUT"; then
  echo "[FAIL] Expected /dev/kvm warning missing on non-writable host."
  exit 1
fi

if ! grep -Eq '\[WARN\] (gh is installed but not authenticated; curl fallback or token env will be used|gh is not installed; curl fallback or token env will be used)' <<<"$OUTPUT"; then
  echo "[FAIL] Expected gh fallback warning missing."
  exit 1
fi

if ! grep -q '\[WARN\] No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed' <<<"$OUTPUT"; then
  echo "[FAIL] Expected token warning missing."
  exit 1
fi

if ! grep -q 'Suggested next actions:' <<<"$OUTPUT"; then
  echo "[FAIL] Expected suggested next actions section missing."
  exit 1
fi

if [ -e /dev/kvm ] && ! grep -q 'Likely fix path: ensure the operator user can access /dev/kvm' <<<"$OUTPUT"; then
  echo "[FAIL] Expected actionable /dev/kvm recovery guidance missing."
  exit 1
fi

echo "[PASS] VM host readiness helper behaves as expected."
