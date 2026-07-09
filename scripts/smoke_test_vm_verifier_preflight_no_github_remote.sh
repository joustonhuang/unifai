#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier preflight fails clearly without a GitHub remote ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-preflight-no-gh-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

WORKTREE="$TMP_DIR/repo"
mkdir -p "$WORKTREE/scripts"
cp "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh" "$WORKTREE/scripts/run_vm_verifier_preflight.sh"
chmod +x "$WORKTREE/scripts/run_vm_verifier_preflight.sh"

cd "$WORKTREE"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

echo "alpha" > sample.txt
git add sample.txt
git commit -q -m "init"
git branch -M feature/no-github-remote

LOCAL_SHA="$(git rev-parse HEAD)"

STATUS=0
OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "$LOCAL_SHA" 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected explicit local SHA case to fail when no GitHub remote exists."
  exit 1
fi

if ! grep -q "Could not auto-detect a GitHub-backed remote for explicit ref visibility checking." <<<"$OUTPUT"; then
  echo "[FAIL] Expected missing-GitHub-remote failure message missing."
  exit 1
fi

if ! grep -q "Set a GitHub upstream or add a GitHub remote such as origin before using local commit SHAs here." <<<"$OUTPUT"; then
  echo "[FAIL] Expected missing-GitHub-remote recovery guidance missing."
  exit 1
fi

if grep -q "scripts/check_vm_host_readiness.sh" <<<"$OUTPUT"; then
  echo "[FAIL] Missing-GitHub-remote case should fail before any preflight steps are planned."
  exit 1
fi

echo "[PASS] VM verifier preflight fails clearly without a GitHub remote."
