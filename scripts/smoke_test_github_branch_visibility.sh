#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$REPO_ROOT/scripts/check_github_branch_visibility.sh"
REAL_BASH="$(command -v bash)"
TMPDIR_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

WORKTREE="$TMPDIR_ROOT/repo"
mkdir -p "$WORKTREE"
cd "$WORKTREE"

git init -q

git config user.name "Little7 Smoke"
git config user.email "little7@example.invalid"

echo "alpha" > sample.txt
git add sample.txt
git commit -q -m "init"
git branch -M transplant/test-visibility

git remote add github git@github.com:example/unifai.git
REMOTE_SHA="$(git rev-parse HEAD)"
git update-ref refs/remotes/github/fix/test-visibility "$REMOTE_SHA"
git branch --set-upstream-to=github/fix/test-visibility transplant/test-visibility >/dev/null

echo "=== UnifAI Smoke Test: GitHub branch visibility helper ==="
PASS_OUTPUT="$("$REAL_BASH" "$HELPER" transplant/test-visibility)"
printf '%s\n' "$PASS_OUTPUT"

if ! grep -q "\[PASS\] Local branch matches the GitHub-visible branch head." <<<"$PASS_OUTPUT"; then
  echo "[FAIL] Expected PASS output when local and remote-tracking refs match."
  exit 1
fi

if ! grep -q "GitHub branch: github/fix/test-visibility" <<<"$PASS_OUTPUT"; then
  echo "[FAIL] Expected helper to print the tracked GitHub branch when it differs from the local branch name."
  exit 1
fi

HEADS_REF_OUTPUT="$("$REAL_BASH" "$HELPER" "refs/heads/transplant/test-visibility")"
printf '%s\n' "$HEADS_REF_OUTPUT"

if ! grep -q "Branch: transplant/test-visibility" <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Expected helper to normalize explicit refs/heads local branch refs."
  exit 1
fi

if ! grep -q "\[PASS\] Local branch matches the GitHub-visible branch head." <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Expected explicit refs/heads local branch ref to stay on the visible-branch path."
  exit 1
fi

echo "beta" >> sample.txt
git add sample.txt
git commit -q -m "ahead locally"

set +e
FAIL_OUTPUT="$("$REAL_BASH" "$HELPER" transplant/test-visibility 2>&1)"
FAIL_STATUS=$?
set -e
printf '%s\n' "$FAIL_OUTPUT"

if [ "$FAIL_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected helper to fail once local branch diverges from GitHub-visible ref."
  exit 1
fi

if ! grep -q "\[FAIL\] Local branch and GitHub branch differ (ahead 1, behind 0)." <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected ahead/behind failure message missing after local divergence."
  exit 1
fi

if ! grep -q "\[INFO\] Local branch tip is not GitHub-visible yet; push it with: git push github HEAD:fix/test-visibility" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected ahead-only push guidance to target the tracked GitHub branch after local divergence."
  exit 1
fi

if ! grep -q "\[INFO\] Review with: git log --oneline --left-right --cherry-pick transplant/test-visibility...github/fix/test-visibility" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected review guidance to reference the tracked GitHub branch after local divergence."
  exit 1
fi

echo "[PASS] GitHub branch visibility helper behaves as expected."
