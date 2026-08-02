#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$REPO_ROOT/scripts/check_checkpoint_handoff_dirty_state.sh"

echo "=== UnifAI Smoke Test: checkpoint handoff dirty-state helper ==="

PASS_OUTPUT="$(env \
  UNIFAI_PREFLIGHT_PRE_REFRESH_HANDOFF_PATHS="" \
  UNIFAI_PREFLIGHT_REFRESHED_HANDOFF_PATHS="" \
  bash "$HELPER" 2>&1)"
if [[ -n "$PASS_OUTPUT" ]]; then
  echo "[FAIL] Expected helper to stay silent when no handoff artifacts are dirty."
  exit 1
fi

set +e
PREEXISTING_OUTPUT="$(env \
  UNIFAI_PREFLIGHT_PRE_REFRESH_HANDOFF_PATHS=$'docs/BOOTSTRAP_VM_VERIFICATION.md\ndocs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md' \
  UNIFAI_PREFLIGHT_REFRESHED_HANDOFF_PATHS=$'docs/BOOTSTRAP_VM_VERIFICATION.md\ndocs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md' \
  bash "$HELPER" 2>&1)"
PREEXISTING_STATUS=$?
set -e
if [ "$PREEXISTING_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected helper to fail closed when all dirty handoff artifacts were already dirty before refresh."
  exit 1
fi
grep -q "\[FAIL\] Bootstrap preflight checkpoint handoff artifacts were already dirty before refresh and are still not committed:" <<<"$PREEXISTING_OUTPUT" || {
  echo "[FAIL] Expected pre-existing-dirty failure message."
  exit 1
}
grep -q "docs/BOOTSTRAP_VM_VERIFICATION.md" <<<"$PREEXISTING_OUTPUT" || {
  echo "[FAIL] Expected pre-existing-dirty output to list BOOTSTRAP_VM_VERIFICATION.md."
  exit 1
}
if grep -q "Checkpoint handoff artifacts that were already dirty before this rerun and still need review" <<<"$PREEXISTING_OUTPUT"; then
  echo "[FAIL] Pre-existing-dirty case should not print the mixed-state informational heading."
  exit 1
fi

set +e
MIXED_OUTPUT="$(env \
  UNIFAI_PREFLIGHT_PRE_REFRESH_HANDOFF_PATHS=$'docs/BOOTSTRAP_VM_VERIFICATION.md' \
  UNIFAI_PREFLIGHT_REFRESHED_HANDOFF_PATHS=$'docs/BOOTSTRAP_VM_VERIFICATION.md\nci-artifacts/bootstrap-preflight/commit-candidate.txt' \
  bash "$HELPER" 2>&1)"
MIXED_STATUS=$?
set -e
if [ "$MIXED_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected helper to fail closed when refresh adds new dirty handoff artifacts."
  exit 1
fi
grep -q "\[FAIL\] Bootstrap preflight refreshed checkpoint handoff artifacts but they are not committed yet:" <<<"$MIXED_OUTPUT" || {
  echo "[FAIL] Expected refresh-induced dirty failure message."
  exit 1
}
grep -q "ci-artifacts/bootstrap-preflight/commit-candidate.txt" <<<"$MIXED_OUTPUT" || {
  echo "[FAIL] Expected refresh-induced dirty output to list the new dirty handoff artifact."
  exit 1
}
grep -q "\[INFO\] Checkpoint handoff artifacts that were already dirty before this rerun and still need review:" <<<"$MIXED_OUTPUT" || {
  echo "[FAIL] Expected mixed-state informational heading."
  exit 1
}
grep -q "docs/BOOTSTRAP_VM_VERIFICATION.md" <<<"$MIXED_OUTPUT" || {
  echo "[FAIL] Expected mixed-state output to list the pre-existing dirty handoff artifact."
  exit 1
}

echo "[PASS] Checkpoint handoff dirty-state helper smoke test passed"
