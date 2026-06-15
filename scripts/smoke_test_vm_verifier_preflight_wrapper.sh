#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier preflight wrapper dry-run behavior ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"
REAL_BASH="$(command -v bash)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"

BRANCH_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$BRANCH")"
printf '%s\n' "$BRANCH_OUTPUT"

if ! grep -q "Mode: dry-run" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected dry-run mode banner missing for branch case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh $BRANCH" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected branch visibility command missing in branch case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in branch case."
  exit 1
fi

SHA_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$SHA")"
printf '%s\n' "$SHA_OUTPUT"

if ! grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$SHA_OUTPUT"; then
  echo "[FAIL] Expected explicit-ref skip message missing in SHA case."
  exit 1
fi

if grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh" <<<"$SHA_OUTPUT"; then
  echo "[FAIL] Branch visibility command should not run in SHA case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $SHA" <<<"$SHA_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in SHA case."
  exit 1
fi

echo "[PASS] VM verifier preflight wrapper dry-run behaves as expected."
