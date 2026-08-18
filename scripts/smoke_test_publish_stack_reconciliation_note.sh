#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: publish-stack reconciliation note ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-publish-note-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

WORKTREE="$TMP_DIR/repo"
mkdir -p "$WORKTREE/scripts"
cp "$REPO_ROOT/scripts/compare_publish_branch_histories.py" "$WORKTREE/scripts/compare_publish_branch_histories.py"
cp "$REPO_ROOT/scripts/check_publish_stack_reconciliation_note.py" "$WORKTREE/scripts/check_publish_stack_reconciliation_note.py"
chmod +x "$WORKTREE/scripts/compare_publish_branch_histories.py"
chmod +x "$WORKTREE/scripts/check_publish_stack_reconciliation_note.py"

cd "$WORKTREE"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

cat > app.py <<'EOF'
print("base")
EOF
git add app.py
git commit -q -m "base"
git branch -M base

git checkout -q -b fix/older
cat > old_only.txt <<'EOF'
older only
EOF
git add old_only.txt
git commit -q -m "older unique"

git checkout -q base
git checkout -q -b transplant/cleaner
cat > clean_only.txt <<'EOF'
cleaner only
EOF
git add clean_only.txt
git commit -q -m "cleaner unique"

mkdir -p ci-artifacts
WRITE_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/compare_publish_branch_histories.py --write-reconciliation-note --generated-at '2026-08-09 18:20 Asia/Taipei' fix/older transplant/cleaner")"
printf '%s\n' "$WRITE_OUTPUT"

PASS_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_publish_stack_reconciliation_note.py --older-ref fix/older --cleaner-ref transplant/cleaner")"
printf '%s\n' "$PASS_OUTPUT"
grep -q "Publish-stack reconciliation note matches current branch-comparison state" <<<"$PASS_OUTPUT" || {
  echo "[FAIL] Expected publish-note checker to pass on a freshly generated reconciliation note."
  exit 1
}

mkdir -p docs
cat > docs/checkpoint.md <<'EOF'
cleaner bookkeeping
EOF
git add docs/checkpoint.md
git commit -q -m "docs: cleaner bookkeeping"

set +e
FAIL_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_publish_stack_reconciliation_note.py --older-ref fix/older --cleaner-ref transplant/cleaner" 2>&1)"
FAIL_STATUS=$?
set -e
printf '%s\n' "$FAIL_OUTPUT"

if [[ $FAIL_STATUS -eq 0 ]]; then
  echo "[FAIL] Expected publish-note checker to fail once the cleaner branch drifts past the tracked note."
  exit 1
fi
grep -q "Publish-stack reconciliation note is stale. Refresh it with:" <<<"$FAIL_OUTPUT" || {
  echo "[FAIL] Expected stale-note refresh guidance after live branch drift."
  exit 1
}
grep -q "expected" <<<"$FAIL_OUTPUT" || {
  echo "[FAIL] Expected a unified-diff preview in the stale-note failure output."
  exit 1
}

python3 scripts/compare_publish_branch_histories.py --write-reconciliation-note --generated-at '2026-08-09 18:20 Asia/Taipei' fix/older transplant/cleaner >/dev/null
git add ci-artifacts/publish-stack-reconciliation-next-step.txt
git commit -q -m "docs: settle publish reconciliation note"

STABLE_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_publish_stack_reconciliation_note.py --older-ref fix/older --cleaner-ref transplant/cleaner")"
printf '%s\n' "$STABLE_OUTPUT"
grep -q "Publish-stack reconciliation note matches current branch-comparison state" <<<"$STABLE_OUTPUT" || {
  echo "[FAIL] Expected publish-note checker to ignore a cleaner-only note settle commit."
  exit 1
}

echo "[PASS] publish-stack reconciliation note smoke test passed"
