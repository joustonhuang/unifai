#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier preflight fails clearly without a GitHub remote ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-preflight-no-gh-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

WORKTREE="$TMP_DIR/repo"
REMOTE_REPO="$TMP_DIR/non-github-origin.git"
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

git init -q --bare "$REMOTE_REPO"
git remote add origin "$REMOTE_REPO"
git push -q -u origin feature/no-github-remote
git fetch -q origin

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

SHORT_REMOTE_REF_STATUS=0
SHORT_REMOTE_REF_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "origin/feature/no-github-remote" 2>&1)" || SHORT_REMOTE_REF_STATUS=$?
printf '%s\n' "$SHORT_REMOTE_REF_OUTPUT"

if [ "$SHORT_REMOTE_REF_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected short remote-tracking ref on a non-GitHub remote to fail."
  exit 1
fi

if ! grep -q "points at remote 'origin', but that remote is not GitHub-backed" <<<"$SHORT_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected short remote-tracking ref non-GitHub failure message missing."
  exit 1
fi

if ! grep -q "Use a local branch with a GitHub upstream, a GitHub remote-tracking ref, or a GitHub-visible commit SHA before running VM verifier preflight." <<<"$SHORT_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected short remote-tracking ref non-GitHub recovery guidance missing."
  exit 1
fi

if grep -q "scripts/check_vm_host_readiness.sh" <<<"$SHORT_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Short remote-tracking ref non-GitHub case should fail before any preflight steps are planned."
  exit 1
fi

FULL_REMOTE_REF_STATUS=0
FULL_REMOTE_REF_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "refs/remotes/origin/feature/no-github-remote" 2>&1)" || FULL_REMOTE_REF_STATUS=$?
printf '%s\n' "$FULL_REMOTE_REF_OUTPUT"

if [ "$FULL_REMOTE_REF_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected full remote-tracking ref on a non-GitHub remote to fail."
  exit 1
fi

if ! grep -q "points at remote 'origin', but that remote is not GitHub-backed" <<<"$FULL_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected full remote-tracking ref non-GitHub failure message missing."
  exit 1
fi

if ! grep -q "Use a local branch with a GitHub upstream, a GitHub remote-tracking ref, or a GitHub-visible commit SHA before running VM verifier preflight." <<<"$FULL_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected full remote-tracking ref non-GitHub recovery guidance missing."
  exit 1
fi

if grep -q "scripts/check_vm_host_readiness.sh" <<<"$FULL_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Full remote-tracking ref non-GitHub case should fail before any preflight steps are planned."
  exit 1
fi

git checkout -q --detach

DETACHED_STATUS=0
DETACHED_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh 2>&1)" || DETACHED_STATUS=$?
printf '%s\n' "$DETACHED_OUTPUT"

if [ "$DETACHED_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected no-arg detached-HEAD case to fail."
  exit 1
fi

if ! grep -q "Detached HEAD; pass an explicit GitHub-visible ref." <<<"$DETACHED_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD failure message missing."
  exit 1
fi

if grep -q "scripts/check_vm_host_readiness.sh" <<<"$DETACHED_OUTPUT"; then
  echo "[FAIL] Detached-HEAD case should fail before any preflight steps are planned."
  exit 1
fi

echo "[PASS] VM verifier preflight fails clearly without a GitHub remote."
