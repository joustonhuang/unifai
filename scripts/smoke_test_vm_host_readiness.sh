#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM host readiness helper ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
READYNESS_SCRIPT="$REPO_ROOT/scripts/check_vm_host_readiness.sh"
TMP_DIR="$(mktemp -d -t unifai-vm-host-readiness-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
mkdir -p "$BIN_DIR"

for bin in jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen scp timeout; do
  cat > "$BIN_DIR/$bin" <<'EOF'
#!/bin/bash
exit 0
EOF
  chmod +x "$BIN_DIR/$bin"
done

cat > "$BIN_DIR/hostname" <<'EOF'
#!/bin/bash
echo synthetic-host
EOF
chmod +x "$BIN_DIR/hostname"

cat > "$BIN_DIR/dirname" <<'EOF'
#!/bin/bash
input="${1:-}"
if [[ "$input" == */* ]]; then
  printf '%s\n' "${input%/*}"
else
  printf '.\n'
fi
EOF
chmod +x "$BIN_DIR/dirname"

run_case() {
  local gh_mode="$1"
  local token_mode="${2:-none}"
  local label="${3:-$gh_mode}"
  local output

  rm -f "$BIN_DIR/gh"
  if [ "$gh_mode" != "missing" ]; then
    cat > "$BIN_DIR/gh" <<EOF
#!/usr/bin/env bash
if [ "\${1:-}" = "auth" ] && [ "\${2:-}" = "status" ]; then
  exit $gh_mode
fi
exit 0
EOF
    chmod +x "$BIN_DIR/gh"
  fi

  local smoke_path="$BIN_DIR:/usr/bin:/bin"
  if [ "$gh_mode" = "missing" ]; then
    smoke_path="$BIN_DIR"
  fi

  if [ "$token_mode" = "gh_token" ]; then
    output="$(PATH="$smoke_path" GH_TOKEN=synthetic-token /bin/bash "$READYNESS_SCRIPT" 2>&1)"
  elif [ "$token_mode" = "github_token" ]; then
    output="$(PATH="$smoke_path" GITHUB_TOKEN=synthetic-token /bin/bash "$READYNESS_SCRIPT" 2>&1)"
  else
    output="$(PATH="$smoke_path" /bin/bash "$READYNESS_SCRIPT" 2>&1)"
  fi
  printf '%s\n' "$output"
  printf '%s' "$output" > "$TMP_DIR/output-$label.txt"
}

run_case 1 none unauth
UNAUTH_OUTPUT="$(cat "$TMP_DIR/output-unauth.txt")"

if ! grep -Eq 'Summary: 9 pass, [23] warn, 0 fail' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected unauthenticated synthetic readiness summary missing or drifted."
  exit 1
fi

if [ -e /dev/kvm ] && ! grep -Eq '\[WARN\] /dev/kvm exists but is not writable; verifier will fall back to TCG emulation' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected /dev/kvm warning missing on non-writable host."
  exit 1
fi

if ! grep -q '\[WARN\] gh is installed but not authenticated; curl fallback or token env will be used' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected unauthenticated gh warning missing."
  exit 1
fi

if ! grep -q '\[WARN\] No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected token warning missing."
  exit 1
fi

if ! grep -q 'Suggested next actions:' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected suggested next actions section missing."
  exit 1
fi

if ! grep -q 'Authenticate gh on this host before the first GitHub-visible VM proof' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected unauthenticated gh recovery guidance missing."
  exit 1
fi

if [ -e /dev/kvm ] && ! grep -q 'Likely fix path: ensure the operator user can access /dev/kvm' <<<"$UNAUTH_OUTPUT"; then
  echo "[FAIL] Expected actionable /dev/kvm recovery guidance missing."
  exit 1
fi

run_case 0 none auth
AUTH_OUTPUT="$(cat "$TMP_DIR/output-auth.txt")"

if ! grep -Eq 'Summary: 11 pass, [12] warn, 0 fail' <<<"$AUTH_OUTPUT"; then
  echo "[FAIL] Expected authenticated synthetic readiness summary missing or drifted."
  exit 1
fi

if ! grep -q '\[PASS\] gh is installed and authenticated' <<<"$AUTH_OUTPUT"; then
  echo "[FAIL] Expected authenticated gh pass missing."
  exit 1
fi

if ! grep -q '\[PASS\] Authenticated gh covers normal GitHub API reads without token-only fallback' <<<"$AUTH_OUTPUT"; then
  echo "[FAIL] Expected authenticated-gh token-independence pass missing."
  exit 1
fi

if grep -q '\[WARN\] No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed' <<<"$AUTH_OUTPUT"; then
  echo "[FAIL] Authenticated gh case should not warn about missing GitHub token env."
  exit 1
fi

if grep -q 'Authenticate gh on this host before the first GitHub-visible VM proof' <<<"$AUTH_OUTPUT"; then
  echo "[FAIL] Authenticated gh guidance should not be printed."
  exit 1
fi

if grep -q 'Export GH_TOKEN or GITHUB_TOKEN if you want curl fallback to avoid unauthenticated GitHub API limits.' <<<"$AUTH_OUTPUT"; then
  echo "[FAIL] Authenticated gh case should not print token-export guidance."
  exit 1
fi

run_case 1 gh_token unauth-token
UNAUTH_TOKEN_OUTPUT="$(cat "$TMP_DIR/output-unauth-token.txt")"

if ! grep -Eq 'Summary: 10 pass, [12] warn, 0 fail' <<<"$UNAUTH_TOKEN_OUTPUT"; then
  echo "[FAIL] Expected token-backed synthetic readiness summary missing or drifted."
  exit 1
fi

if ! grep -q '\[PASS\] GitHub token env is present for curl fallback' <<<"$UNAUTH_TOKEN_OUTPUT"; then
  echo "[FAIL] Expected token-present pass missing."
  exit 1
fi

if grep -q '\[WARN\] No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed' <<<"$UNAUTH_TOKEN_OUTPUT"; then
  echo "[FAIL] Token-present case should not warn about missing GitHub token env."
  exit 1
fi

if grep -q 'Export GH_TOKEN or GITHUB_TOKEN if you want curl fallback to avoid unauthenticated GitHub API limits.' <<<"$UNAUTH_TOKEN_OUTPUT"; then
  echo "[FAIL] Token-present case should not print token-export guidance."
  exit 1
fi

if ! grep -q 'Authenticate gh on this host before the first GitHub-visible VM proof' <<<"$UNAUTH_TOKEN_OUTPUT"; then
  echo "[FAIL] Unauthenticated gh recovery guidance should still appear when only token fallback is present."
  exit 1
fi

run_case 1 github_token unauth-github-token
UNAUTH_GITHUB_TOKEN_OUTPUT="$(cat "$TMP_DIR/output-unauth-github-token.txt")"

if ! grep -Eq 'Summary: 10 pass, [12] warn, 0 fail' <<<"$UNAUTH_GITHUB_TOKEN_OUTPUT"; then
  echo "[FAIL] Expected GITHUB_TOKEN-backed synthetic readiness summary missing or drifted."
  exit 1
fi

if ! grep -q '\[PASS\] GitHub token env is present for curl fallback' <<<"$UNAUTH_GITHUB_TOKEN_OUTPUT"; then
  echo "[FAIL] Expected GITHUB_TOKEN-present pass missing."
  exit 1
fi

if grep -q '\[WARN\] No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed' <<<"$UNAUTH_GITHUB_TOKEN_OUTPUT"; then
  echo "[FAIL] GITHUB_TOKEN-present case should not warn about missing GitHub token env."
  exit 1
fi

if grep -q 'Export GH_TOKEN or GITHUB_TOKEN if you want curl fallback to avoid unauthenticated GitHub API limits.' <<<"$UNAUTH_GITHUB_TOKEN_OUTPUT"; then
  echo "[FAIL] GITHUB_TOKEN-present case should not print token-export guidance."
  exit 1
fi

if ! grep -q 'Authenticate gh on this host before the first GitHub-visible VM proof' <<<"$UNAUTH_GITHUB_TOKEN_OUTPUT"; then
  echo "[FAIL] Unauthenticated gh recovery guidance should still appear when only GITHUB_TOKEN fallback is present."
  exit 1
fi

run_case missing none missing
MISSING_GH_OUTPUT="$(cat "$TMP_DIR/output-missing.txt")"

if ! grep -Eq 'Summary: 9 pass, [23] warn, 0 fail' <<<"$MISSING_GH_OUTPUT"; then
  echo "[FAIL] Expected missing-gh synthetic readiness summary missing or drifted."
  exit 1
fi

if ! grep -q '\[WARN\] gh is not installed; curl fallback or token env will be used' <<<"$MISSING_GH_OUTPUT"; then
  echo "[FAIL] Expected missing-gh warning missing."
  exit 1
fi

if grep -q 'Authenticate gh on this host before the first GitHub-visible VM proof' <<<"$MISSING_GH_OUTPUT"; then
  echo "[FAIL] Missing-gh case should not print unauthenticated-gh guidance."
  exit 1
fi

if ! grep -q 'Install/authenticate gh if you want API-backed verifier checks without token-only fallback.' <<<"$MISSING_GH_OUTPUT"; then
  echo "[FAIL] Expected missing-gh recovery guidance missing."
  exit 1
fi

echo "[PASS] VM host readiness helper behaves as expected."
