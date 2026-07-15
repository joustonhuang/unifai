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
git branch -M feature/test-visibility

git remote add github git@github.com:example/unifai.git
REMOTE_SHA="$(git rev-parse HEAD)"
git update-ref refs/remotes/github/feature/test-visibility "$REMOTE_SHA"
git branch --set-upstream-to=github/feature/test-visibility feature/test-visibility >/dev/null

echo "=== UnifAI Smoke Test: GitHub branch visibility helper ==="
PASS_OUTPUT="$("$REAL_BASH" "$HELPER" feature/test-visibility)"
printf '%s\n' "$PASS_OUTPUT"

if ! grep -q "\[PASS\] Local branch matches the GitHub-visible branch head." <<<"$PASS_OUTPUT"; then
  echo "[FAIL] Expected PASS output when local and remote-tracking refs match."
  exit 1
fi

echo "beta" >> sample.txt
git add sample.txt
git commit -q -m "ahead locally"

set +e
FAIL_OUTPUT="$("$REAL_BASH" "$HELPER" feature/test-visibility 2>&1)"
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

if ! grep -q "\[INFO\] Local branch tip is not GitHub-visible yet; push it with: git push github feature/test-visibility" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected ahead-only push guidance missing after local divergence."
  exit 1
fi

if ! grep -q "\[INFO\] Review with: git log --oneline --left-right --cherry-pick feature/test-visibility...github/feature/test-visibility" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected review guidance missing after local divergence."
  exit 1
fi

echo "[PASS] GitHub branch visibility helper behaves as expected."
