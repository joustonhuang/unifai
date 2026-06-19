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

detect_github_remote() {
  local branch="$1"
  local candidate=""
  local url=""

  if candidate="$(git rev-parse --abbrev-ref "$branch@{upstream}" 2>/dev/null)"; then
    candidate="${candidate%%/*}"
    if [ -n "$candidate" ] && url="$(git remote get-url "$candidate" 2>/dev/null)"; then
      case "$url" in
        *github.com*|git@github.com:*)
          printf '%s\n' "$candidate"
          return 0
          ;;
      esac
    fi
  fi

  for candidate in origin github; do
    if url="$(git remote get-url "$candidate" 2>/dev/null)"; then
      case "$url" in
        *github.com*|git@github.com:*)
          printf '%s\n' "$candidate"
          return 0
          ;;
      esac
    fi
  done

  while IFS=$'\t' read -r candidate url; do
    case "$url" in
      *github.com*|git@github.com:*)
        printf '%s\n' "$candidate"
        return 0
        ;;
    esac
  done < <(git remote -v | awk '$3 == "(fetch)" {print $1 "\t" $2}')

  return 1
}

ensure_ref_is_github_visible() {
  local ref="$1"
  local branch="$2"
  local remote=""

  if git show-ref --verify --quiet "refs/heads/$ref"; then
    return 0
  fi

  if ! git rev-parse --verify --quiet "$ref^{commit}" >/dev/null; then
    return 0
  fi

  if ! remote="$(detect_github_remote "$branch")"; then
    echo "[FAIL] Could not auto-detect a GitHub-backed remote for explicit ref visibility checking." >&2
    echo "[INFO] Set a GitHub upstream or add a GitHub remote such as origin before using local commit SHAs here." >&2
    exit 1
  fi

  if git branch -r --contains "$ref" | grep -Eq "^[[:space:]]*$remote/"; then
    return 0
  fi

  echo "[FAIL] '$ref' exists locally but is not reachable from any GitHub-visible branch on remote '$remote'." >&2
  echo "[INFO] Push the branch tip first, or use a GitHub-visible branch/ref before running VM verifier preflight." >&2
  exit 1
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

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" = "HEAD" ]; then
  current_branch="$ref"
fi

ensure_ref_is_github_visible "$ref" "$current_branch"

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
