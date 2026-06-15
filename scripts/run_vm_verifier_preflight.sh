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
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ref="${1:-$(git rev-parse --abbrev-ref HEAD)}"
if [ "$ref" = "HEAD" ]; then
  echo "[FAIL] Detached HEAD; pass an explicit GitHub-visible ref." >&2
  exit 1
fi

echo "== VM verifier local preflight =="
echo "Repo: $REPO_ROOT"
echo "Ref: $ref"

echo
echo "== Step 1/3: bootstrap installer preflight =="
bash scripts/bootstrap_installer_preflight.sh

echo
if git show-ref --verify --quiet "refs/heads/$ref"; then
  echo "== Step 2/3: GitHub branch visibility =="
  bash scripts/check_github_branch_visibility.sh "$ref"
else
  echo "== Step 2/3: GitHub branch visibility =="
  echo "[INFO] '$ref' is not a local branch name; skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA."
fi

echo
echo "== Step 3/3: GitHub check gate =="
python3 scripts/check_github_check_gate.py "$ref"

echo
echo "[PASS] VM verifier local preflight is green for $ref"
echo "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $ref"
