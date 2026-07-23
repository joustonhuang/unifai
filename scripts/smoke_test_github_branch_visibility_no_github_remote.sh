#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: GitHub branch visibility fails clearly without a GitHub remote ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$REPO_ROOT/scripts/check_github_branch_visibility.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-gh-visibility-no-remote-XXXXXX)"
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
git branch -M feature/no-github-remote

STATUS=0
OUTPUT="$("$REAL_BASH" "$HELPER" feature/no-github-remote 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected branch-visibility helper to fail when no GitHub remote exists."
  exit 1
fi

if ! grep -q "Could not auto-detect a GitHub-backed remote." <<<"$OUTPUT"; then
  echo "[FAIL] Expected missing-GitHub-remote failure message missing."
  exit 1
fi

if ! grep -q "Set GITHUB_REMOTE=<remote> or add a GitHub remote such as origin." <<<"$OUTPUT"; then
  echo "[FAIL] Expected missing-GitHub-remote recovery guidance missing."
  exit 1
fi

if grep -q "GitHub branch:" <<<"$OUTPUT"; then
  echo "[FAIL] Missing-GitHub-remote case should fail before reporting any GitHub branch state."
  exit 1
fi

echo "[PASS] GitHub branch visibility fails clearly without a GitHub remote."
