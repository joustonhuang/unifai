#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: GitHub branch visibility forced-remote override fails clearly ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$REPO_ROOT/scripts/check_github_branch_visibility.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-gh-visibility-forced-remote-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

WORKTREE="$TMP_DIR/repo"
mkdir -p "$WORKTREE"
cd "$WORKTREE"

git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

echo "alpha" > sample.txt
git add sample.txt
git commit -q -m "init"
git branch -M feature/forced-remote

STATUS=0
OUTPUT="$(GITHUB_REMOTE=github "$REAL_BASH" "$HELPER" feature/forced-remote 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected branch-visibility helper to fail when the forced GitHub remote is missing."
  exit 1
fi

if ! grep -q "Remote 'github' is not configured." <<<"$OUTPUT"; then
  echo "[FAIL] Expected forced-missing-remote failure message missing."
  exit 1
fi

if ! grep -q "Add it with: git remote add github https://github.com/<owner>/<repo>.git" <<<"$OUTPUT"; then
  echo "[FAIL] Expected forced-missing-remote recovery guidance missing."
  exit 1
fi

git remote add origin https://example.com/not-github/unifai.git

STATUS=0
OUTPUT="$(GITHUB_REMOTE=origin "$REAL_BASH" "$HELPER" feature/forced-remote 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected branch-visibility helper to fail when the forced remote is not GitHub-backed."
  exit 1
fi

if ! grep -q "Remote 'origin' is not GitHub-backed: https://example.com/not-github/unifai.git" <<<"$OUTPUT"; then
  echo "[FAIL] Expected forced-non-GitHub-remote failure message missing."
  exit 1
fi

if grep -q "GitHub branch:" <<<"$OUTPUT"; then
  echo "[FAIL] Forced-remote override failures should happen before any GitHub branch state is reported."
  exit 1
fi

echo "[PASS] GitHub branch visibility forced-remote override fails clearly."
