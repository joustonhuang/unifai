#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/run_vm_verifier_preflight.sh [github-visible-ref-or-sha]

Runs the cheap local checks before a fresh-VM verifier attempt:
1. bootstrap installer preflight
2. GitHub branch visibility check (when the ref is a local branch name)
3. GitHub required-check gate inspection

If no ref is provided, uses the current branch name.

Environment:
  UNIFAI_VM_PREFLIGHT_DRY_RUN=1  Print the planned commands instead of executing them.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

run_step() {
  if [ "${UNIFAI_VM_PREFLIGHT_DRY_RUN:-0}" = "1" ]; then
    printf '[DRY_RUN]'
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

ref="${1:-$(git rev-parse --abbrev-ref HEAD)}"
if [ "$ref" = "HEAD" ]; then
  echo "[FAIL] Detached HEAD; pass an explicit GitHub-visible ref." >&2
  exit 1
fi

echo "== VM verifier local preflight =="
echo "Repo: $REPO_ROOT"
echo "Ref: $ref"
if [ "${UNIFAI_VM_PREFLIGHT_DRY_RUN:-0}" = "1" ]; then
  echo "Mode: dry-run"
fi

echo
echo "== Step 1/3: bootstrap installer preflight =="
run_step bash scripts/bootstrap_installer_preflight.sh

echo
if git show-ref --verify --quiet "refs/heads/$ref"; then
  echo "== Step 2/3: GitHub branch visibility =="
  run_step bash scripts/check_github_branch_visibility.sh "$ref"
else
  echo "== Step 2/3: GitHub branch visibility =="
  echo "[INFO] '$ref' is not a local branch name; skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA."
fi

echo
echo "== Step 3/3: GitHub check gate =="
run_step python3 scripts/check_github_check_gate.py "$ref"

echo
echo "[PASS] VM verifier local preflight is green for $ref"
echo "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $ref"
