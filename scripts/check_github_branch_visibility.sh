#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/check_github_branch_visibility.sh [branch]

Checks whether the current branch (or the named branch) is aligned with a
GitHub-backed remote-tracking branch so local work is actually GitHub-visible.

Environment:
  GITHUB_REMOTE   Remote name to force; otherwise auto-detected from upstream/origin
EOF
}

is_github_remote_url() {
  local url="$1"

  case "$url" in
    *github.com*|git@github.com:*)
      return 0
      ;;
  esac

  return 1
}

detect_github_remote() {
  local branch="$1"
  local candidate=""
  local url=""

  if candidate="$(git rev-parse --abbrev-ref "$branch@{upstream}" 2>/dev/null)"; then
    candidate="${candidate%%/*}"
    if [ -n "$candidate" ] && url="$(git remote get-url "$candidate" 2>/dev/null)" && is_github_remote_url "$url"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi

  for candidate in origin github; do
    if url="$(git remote get-url "$candidate" 2>/dev/null)" && is_github_remote_url "$url"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  while IFS=$'\t' read -r candidate url; do
    if is_github_remote_url "$url"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(git remote -v | awk '$3 == "(fetch)" {print $1 "\t" $2}')

  return 1
}

github_remote_branch_parts() {
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
    refs/*)
      return 0
      ;;
    */*)
      remote="${ref%%/*}"
      branch="${ref#*/}"
      ;;
    *)
      return 0
      ;;
  esac

  if [ -z "$remote" ] || [ -z "$branch" ] || [ "$branch" = "$ref" ]; then
    return 0
  fi

  if ! url="$(git remote get-url "$remote" 2>/dev/null)"; then
    return 0
  fi

  if ! is_github_remote_url "$url"; then
    return 0
  fi

  printf '%s\t%s\n' "$remote" "$branch"
}

local_branch_name() {
  local ref="$1"
  local branch=""

  case "$ref" in
    refs/heads/*)
      printf '%s\n' "${ref#refs/heads/}"
      ;;
    *)
      branch="$(tracked_local_branch_for_ref "$ref")"
      if [ -n "$branch" ]; then
        printf '%s\n' "$branch"
      else
        printf '%s\n' "$ref"
      fi
      ;;
  esac
}

tracked_local_branch_for_ref() {
  local ref="$1"
  local remote=""
  local branch=""

  if ! IFS=$'\t' read -r remote branch < <(github_remote_branch_parts "$ref"); then
    return 0
  fi

  if [ -z "$remote" ] || [ -z "$branch" ]; then
    return 0
  fi

  git for-each-ref --format='%(refname:short)	%(upstream:short)' refs/heads |
    awk -F '\t' -v upstream="$remote/$branch" '$2 == upstream {print $1; exit}'
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

branch="$(local_branch_name "${1:-$(git rev-parse --abbrev-ref HEAD)}")"

if [ "$branch" = "HEAD" ]; then
  echo "[FAIL] Detached HEAD; switch to a branch before checking GitHub visibility." >&2
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "[FAIL] Not inside a git repository." >&2
  exit 1
fi

if [ -n "${GITHUB_REMOTE:-}" ]; then
  if ! git remote get-url "$GITHUB_REMOTE" >/dev/null 2>&1; then
    echo "[FAIL] Remote '$GITHUB_REMOTE' is not configured." >&2
    echo "[INFO] Add it with: git remote add $GITHUB_REMOTE https://github.com/<owner>/<repo>.git" >&2
    exit 1
  fi
else
  if ! GITHUB_REMOTE="$(detect_github_remote "$branch")"; then
    echo "[FAIL] Could not auto-detect a GitHub-backed remote." >&2
    echo "[INFO] Set GITHUB_REMOTE=<remote> or add a GitHub remote such as origin." >&2
    exit 1
  fi
fi

remote_url="$(git remote get-url "$GITHUB_REMOTE")"
if ! is_github_remote_url "$remote_url"; then
  echo "[FAIL] Remote '$GITHUB_REMOTE' is not GitHub-backed: $remote_url" >&2
  exit 1
fi

if ! git show-ref --verify --quiet "refs/heads/$branch"; then
  echo "[FAIL] Local branch '$branch' does not exist." >&2
  exit 1
fi

upstream_ref=""
if upstream_ref="$(git rev-parse --abbrev-ref "$branch@{upstream}" 2>/dev/null)"; then
  :
else
  upstream_ref=""
fi

github_branch="$GITHUB_REMOTE/$branch"
if [ -n "$upstream_ref" ] && [ "${upstream_ref%%/*}" = "$GITHUB_REMOTE" ]; then
  github_branch="$upstream_ref"
fi

remote_ref="refs/remotes/$github_branch"
if ! git show-ref --verify --quiet "$remote_ref"; then
  echo "[FAIL] Remote branch '$github_branch' does not exist yet." >&2
  if [ -n "$upstream_ref" ] && [ "${upstream_ref%%/*}" = "$GITHUB_REMOTE" ]; then
    echo "[INFO] Push the tracked upstream ref first if this work is meant to be public signal." >&2
  else
    echo "[INFO] Push the branch first if this work is meant to be public signal." >&2
  fi
  exit 1
fi

local_sha="$(git rev-parse "$branch")"
remote_sha="$(git rev-parse "$github_branch")"

counts="$(git rev-list --left-right --count "$branch...$github_branch")"
read -r ahead behind <<< "$counts"

printf 'Branch: %s\n' "$branch"
printf 'GitHub remote: %s (%s)\n' "$GITHUB_REMOTE" "$remote_url"
printf 'GitHub branch: %s\n' "$github_branch"
if [ -n "$upstream_ref" ]; then
  printf 'Tracked upstream: %s\n' "$upstream_ref"
else
  printf 'Tracked upstream: %s\n' '(none)'
fi
printf 'Local HEAD: %s\n' "$local_sha"
printf 'GitHub HEAD: %s\n' "$remote_sha"

if [ "$upstream_ref" != "$github_branch" ]; then
  echo "[FAIL] Branch is not tracking the GitHub-visible upstream '$github_branch'." >&2
  echo "[INFO] Fix with: git branch --set-upstream-to=$github_branch $branch" >&2
  exit 1
fi

if [ "$local_sha" = "$remote_sha" ]; then
  echo "[PASS] Local branch matches the GitHub-visible branch head."
  exit 0
fi

if [ "$ahead" -ne 0 ] || [ "$behind" -ne 0 ]; then
  echo "[FAIL] Local branch and GitHub branch differ (ahead $ahead, behind $behind)." >&2
  if [ "$ahead" -gt 0 ] && [ "$behind" -eq 0 ]; then
    echo "[INFO] Local branch tip is not GitHub-visible yet; push it with: git push $GITHUB_REMOTE HEAD:${github_branch#"$GITHUB_REMOTE/"}" >&2
  elif [ "$ahead" -eq 0 ] && [ "$behind" -gt 0 ]; then
    echo "[INFO] Local branch is behind the GitHub-visible head; fast-forward or rebase before verifier work." >&2
  else
    echo "[INFO] Local and GitHub-visible history diverged; reconcile before verifier work." >&2
  fi
  echo "[INFO] Review with: git log --oneline --left-right --cherry-pick $branch...$github_branch" >&2
  exit 1
fi

echo "[FAIL] Branch SHAs differ unexpectedly." >&2
exit 1
