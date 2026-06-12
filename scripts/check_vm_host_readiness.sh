#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() {
  printf '[PASS] %s\n' "$1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

warn() {
  printf '[WARN] %s\n' "$1"
  WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
  printf '[FAIL] %s\n' "$1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_bin() {
  local bin="$1"
  if command -v "$bin" >/dev/null 2>&1; then
    pass "Found $bin"
  else
    fail "Missing $bin"
  fi
}

printf '== VM host readiness for verify_bootstrap_in_vm ==\n'
printf 'Host: %s\n' "$(hostname)"
printf 'Repo: %s\n' "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for bin in jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen timeout; do
  check_bin "$bin"
done

if [ -e /dev/kvm ]; then
  if [ -w /dev/kvm ]; then
    pass '/dev/kvm exists and is writable'
  else
    warn '/dev/kvm exists but is not writable; verifier will fall back to TCG emulation'
  fi
else
  warn '/dev/kvm is absent; verifier will fall back to TCG emulation'
fi

if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    pass 'gh is installed and authenticated'
  else
    warn 'gh is installed but not authenticated; curl fallback or token env will be used'
  fi
else
  warn 'gh is not installed; curl fallback or token env will be used'
fi

if [ -n "${GH_TOKEN:-}" ] || [ -n "${GITHUB_TOKEN:-}" ]; then
  pass 'GitHub token env is present for curl fallback'
else
  warn 'No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed'
fi

printf '\nSummary: %d pass, %d warn, %d fail\n' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -ne 0 ]; then
  exit 1
fi
