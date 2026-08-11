#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/run_vm_verifier_preflight.sh [--dry-run] [github-visible-ref-or-sha]

Runs the cheap local checks before a fresh-VM verifier attempt:
1. VM host readiness check
2. bootstrap installer preflight
3. GitHub branch visibility check (when the ref is a local branch name)
4. GitHub required-check gate inspection

If no ref is provided, uses the current branch name.

Options:
  --dry-run  Print the planned commands instead of executing them.

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

local_branch_name() {
  local ref="$1"

  case "$ref" in
    refs/heads/*)
      printf '%s\n' "${ref#refs/heads/}"
      ;;
    *)
      printf '%s\n' "$ref"
      ;;
  esac
}

is_github_remote_head_alias() {
  local ref="$1"
  local remote=""
  local branch=""
  local url=""

  case "$ref" in
    refs/remotes/*)
      remote="${ref#refs/remotes/}"
      remote="${remote%%/*}"
      branch="${ref#refs/remotes/$remote/}"
      ;;
    */*)
      remote="${ref%%/*}"
      branch="${ref#*/}"
      ;;
    *)
      return 1
      ;;
  esac

  if [ "$branch" != "HEAD" ] || [ -z "$remote" ]; then
    return 1
  fi

  if ! url="$(git remote get-url "$remote" 2>/dev/null)"; then
    return 1
  fi

  case "$url" in
    *github.com*|git@github.com:*)
      return 0
      ;;
  esac

  return 1
}

explicit_remote_ref_remote() {
  local ref="$1"
  local remote=""
  local branch=""

  case "$ref" in
    refs/remotes/*)
      remote="${ref#refs/remotes/}"
      remote="${remote%%/*}"
      branch="${ref#refs/remotes/$remote/}"
      ;;
    */*)
      remote="${ref%%/*}"
      branch="${ref#*/}"
      if ! git remote get-url "$remote" >/dev/null 2>&1; then
        return 1
      fi
      ;;
    *)
      return 1
      ;;
  esac

  if [ -z "$remote" ] || [ -z "$branch" ] || [ "$branch" = "$ref" ]; then
    return 1
  fi

  printf '%s\n' "$remote"
}

reject_symbolic_github_remote_head_ref() {
  local ref="$1"
  local remote=""

  if ! is_github_remote_head_alias "$ref"; then
    return 0
  fi

  case "$ref" in
    refs/remotes/*)
      remote="${ref#refs/remotes/}"
      remote="${remote%%/*}"
      ;;
    *)
      remote="${ref%%/*}"
      ;;
  esac

  echo "[FAIL] '$ref' is the symbolic remote HEAD alias for GitHub remote '$remote', not a concrete GitHub-visible branch/ref." >&2
  echo "[INFO] Use a concrete branch/ref such as refs/remotes/$remote/<branch>, $remote/<branch>, or the resolved branch name before running VM verifier preflight." >&2
  exit 1
}

reject_non_github_remote_tracking_ref() {
  local ref="$1"
  local remote=""
  local url=""

  if ! remote="$(explicit_remote_ref_remote "$ref")"; then
    return 0
  fi

  if ! url="$(git remote get-url "$remote" 2>/dev/null)"; then
    return 0
  fi

  case "$url" in
    *github.com*|git@github.com:*)
      return 0
      ;;
  esac

  echo "[FAIL] '$ref' points at remote '$remote', but that remote is not GitHub-backed and cannot be used as a GitHub-visible verifier ref." >&2
  echo "[INFO] Use a local branch with a GitHub upstream, a GitHub remote-tracking ref, or a GitHub-visible commit SHA before running VM verifier preflight." >&2
  exit 1
}

github_visible_ref_for_verifier() {
  local ref="$1"
  local remote=""
  local branch=""
  local upstream_ref=""
  local url=""

  if git show-ref --verify --quiet "refs/heads/$ref"; then
    if upstream_ref="$(git rev-parse --abbrev-ref "$ref@{upstream}" 2>/dev/null)"; then
      remote="${upstream_ref%%/*}"
      branch="${upstream_ref#*/}"
      if [ -n "$remote" ] && [ -n "$branch" ] && [ "$branch" != "$upstream_ref" ]; then
        if url="$(git remote get-url "$remote" 2>/dev/null)"; then
          case "$url" in
            *github.com*|git@github.com:*)
              printf '%s\n' "$branch"
              return 0
              ;;
          esac
        fi
      fi
    fi
  fi

  case "$ref" in
    refs/remotes/*)
      remote="${ref#refs/remotes/}"
      remote="${remote%%/*}"
      branch="${ref#refs/remotes/$remote/}"
      ;;
    refs/*)
      printf '%s\n' "$ref"
      return 0
      ;;
    */*)
      remote="${ref%%/*}"
      branch="${ref#*/}"
      ;;
    *)
      printf '%s\n' "$ref"
      return 0
      ;;
  esac

  if [ -z "$remote" ] || [ -z "$branch" ] || [ "$branch" = "$ref" ]; then
    printf '%s\n' "$ref"
    return 0
  fi

  if ! url="$(git remote get-url "$remote" 2>/dev/null)"; then
    printf '%s\n' "$ref"
    return 0
  fi

  case "$url" in
    *github.com*|git@github.com:*)
      printf '%s\n' "$branch"
      ;;
    *)
      printf '%s\n' "$ref"
      ;;
  esac
}

ensure_ref_is_github_visible() {
  local ref="$1"
  local branch="$2"
  local remote=""
  local local_branch_ref=""

  local_branch_ref="$(local_branch_name "$ref")"

  if git show-ref --verify --quiet "refs/heads/$local_branch_ref"; then
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

dry_run="${UNIFAI_VM_PREFLIGHT_DRY_RUN:-0}"
ref=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "[FAIL] Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [ -n "$ref" ]; then
        echo "[FAIL] Unexpected extra argument: $1" >&2
        usage >&2
        exit 1
      fi
      ref="$1"
      shift
      ;;
  esac
done

if [ "$#" -gt 0 ]; then
  if [ -z "$ref" ]; then
    ref="$1"
    shift
  fi
fi

if [ "$#" -gt 0 ]; then
  echo "[FAIL] Unexpected extra argument: $1" >&2
  usage >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

run_step() {
  if [ "$dry_run" = "1" ]; then
    printf '[DRY_RUN]'
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

ref="${ref:-$(git rev-parse --abbrev-ref HEAD)}"
if [ "$ref" = "HEAD" ]; then
  echo "[FAIL] Detached HEAD; pass an explicit GitHub-visible ref." >&2
  exit 1
fi

reject_symbolic_github_remote_head_ref "$ref"
reject_non_github_remote_tracking_ref "$ref"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" = "HEAD" ]; then
  current_branch="$ref"
fi

ensure_ref_is_github_visible "$ref" "$current_branch"

effective_ref="$(local_branch_name "$ref")"
verifier_ref="$(github_visible_ref_for_verifier "$effective_ref")"

echo "== VM verifier local preflight =="
echo "Repo: $REPO_ROOT"
echo "Ref: $effective_ref"
if [ "$dry_run" = "1" ]; then
  echo "Mode: dry-run"
fi

echo
echo "== Step 1/4: VM host readiness =="
run_step bash scripts/check_vm_host_readiness.sh

echo
echo "== Step 2/4: bootstrap installer preflight =="
run_step bash scripts/bootstrap_installer_preflight.sh

echo
if git show-ref --verify --quiet "refs/heads/$effective_ref"; then
  echo "== Step 3/4: GitHub branch visibility =="
  run_step bash scripts/check_github_branch_visibility.sh "$effective_ref"
else
  echo "== Step 3/4: GitHub branch visibility =="
  echo "[INFO] '$effective_ref' is not a local branch name; skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA."
fi

echo
echo "== Step 4/4: GitHub check gate =="
run_step python3 scripts/check_github_check_gate.py "$verifier_ref"

echo
echo "[PASS] VM verifier local preflight is green for $effective_ref"
echo "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $verifier_ref"
