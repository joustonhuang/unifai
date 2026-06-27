#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier preflight wrapper dry-run behavior ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"
REAL_BASH="$(command -v bash)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
LOCAL_ONLY_SHA="$(
  git -C "$REPO_ROOT" commit-tree \
    "$(git -C "$REPO_ROOT" rev-parse HEAD^{tree})" \
    -p "$(git -C "$REPO_ROOT" rev-parse HEAD)" \
    -m "smoke local-only sha" \
    2>/dev/null
)"
VISIBLE_SHA="$(git -C "$REPO_ROOT" rev-parse "github/$BRANCH")"

BRANCH_OUTPUT="$("$REAL_BASH" "$WRAPPER" --dry-run "$BRANCH")"
printf '%s\n' "$BRANCH_OUTPUT"

if ! grep -q "Mode: dry-run" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected dry-run mode banner missing for branch case."
  exit 1
fi

if ! grep -q "Ref: $BRANCH" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected branch ref missing in --dry-run flag case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_vm_host_readiness.sh" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected host-readiness command missing in branch case."
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

VISIBLE_SHA_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$VISIBLE_SHA")"
printf '%s\n' "$VISIBLE_SHA_OUTPUT"

if ! grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected explicit-ref skip message missing in GitHub-visible SHA case."
  exit 1
fi

if grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Branch visibility command should not run in GitHub-visible SHA case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_vm_host_readiness.sh" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected host-readiness command missing in GitHub-visible SHA case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $VISIBLE_SHA" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in GitHub-visible SHA case."
  exit 1
fi

set +e
UNKNOWN_OPTION_OUTPUT="$("$REAL_BASH" "$WRAPPER" --bogus 2>&1)"
UNKNOWN_OPTION_STATUS=$?
set -e
printf '%s\n' "$UNKNOWN_OPTION_OUTPUT"

if [ "$UNKNOWN_OPTION_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected unknown option case to fail."
  exit 1
fi

if ! grep -q "Unknown option: --bogus" <<<"$UNKNOWN_OPTION_OUTPUT"; then
  echo "[FAIL] Expected unknown option failure message missing."
  exit 1
fi

set +e
LOCAL_ONLY_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$LOCAL_ONLY_SHA" 2>&1)"
LOCAL_ONLY_STATUS=$?
set -e
printf '%s\n' "$LOCAL_ONLY_OUTPUT"

if [ "$LOCAL_ONLY_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected local-only SHA case to fail fast."
  exit 1
fi

if ! grep -q "exists locally but is not reachable from any GitHub-visible branch" <<<"$LOCAL_ONLY_OUTPUT"; then
  echo "[FAIL] Expected local-only SHA visibility failure message missing."
  exit 1
fi

if grep -q "python3 scripts/check_github_check_gate.py $LOCAL_ONLY_SHA" <<<"$LOCAL_ONLY_OUTPUT"; then
  echo "[FAIL] Local-only SHA case should fail before the GitHub check-gate step."
  exit 1
fi

echo "[PASS] VM verifier preflight wrapper dry-run behaves as expected."
