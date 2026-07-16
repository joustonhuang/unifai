#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: compare publish branch histories ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-compare-publish-history-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

WORKTREE="$TMP_DIR/repo"
mkdir -p "$WORKTREE/scripts"
cp "$REPO_ROOT/scripts/compare_publish_branch_histories.py" "$WORKTREE/scripts/compare_publish_branch_histories.py"
chmod +x "$WORKTREE/scripts/compare_publish_branch_histories.py"

cd "$WORKTREE"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

cat > app.py <<'EOF'
print("base")
EOF
cat > absorbed.txt <<'EOF'
base
EOF
git add app.py
git add absorbed.txt
git commit -q -m "base"
git branch -M base

git checkout -q -b older
cat > app.py <<'EOF'
print("patch-equivalent")
EOF
git add app.py
git commit -q -m "older duplicate"

cat > old_only.txt <<'EOF'
older only
EOF
git add old_only.txt
git commit -q -m "older unique"

cat > old_second_only.txt <<'EOF'
older second only
EOF
git add old_second_only.txt
git commit -q -m "older unique 2"

cat > absorbed.txt <<'EOF'
absorbed from older
EOF
git add absorbed.txt
git commit -q -m "older absorbed"

mkdir -p docs
cat > docs/checkpoint.md <<'EOF'
older checkpoint churn
EOF
git add docs/checkpoint.md
git commit -q -m "older docs only"

cat > helper.py <<'EOF'
print("helper")
EOF
git add helper.py
git commit -q -m "older mixed"
mkdir -p docs
cat > docs/helper-notes.md <<'EOF'
helper docs
EOF
git add docs/helper-notes.md
git commit -q --amend -m "older mixed"

git checkout -q base
git checkout -q -b cleaner
cat > app.py <<'EOF'
print("patch-equivalent")
EOF
git add app.py
git commit -q -m "cleaner duplicate"

cat > clean_only.txt <<'EOF'
cleaner only
EOF
git add clean_only.txt
git commit -q -m "cleaner unique"

cat > absorbed.txt <<'EOF'
absorbed temp
EOF
git add absorbed.txt
git commit -q -m "cleaner absorbed temp"

cat > absorbed.txt <<'EOF'
absorbed from older
EOF
git add absorbed.txt
git commit -q -m "cleaner absorbed via cleaner path"

OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/compare_publish_branch_histories.py older cleaner")"
printf '%s\n' "$OUTPUT"

grep -q "Patch-equivalent commits already represented on cleaner:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing duplicate section for cleaner branch."
  exit 1
}
grep -q "older duplicate" <<<"$OUTPUT" || {
  echo "[FAIL] Expected older duplicate commit to be recognized."
  exit 1
}
grep -q "True branch-only commits on older:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing unique-older section."
  exit 1
}
grep -q "older unique" <<<"$OUTPUT" || {
  echo "[FAIL] Expected older unique commit to be listed."
  exit 1
}
grep -q "older unique 2" <<<"$OUTPUT" || {
  echo "[FAIL] Expected second older unique commit to be listed."
  exit 1
}
grep -q "Patch-equivalent commits already represented on older:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing duplicate section for older branch."
  exit 1
}
grep -q "cleaner duplicate" <<<"$OUTPUT" || {
  echo "[FAIL] Expected cleaner duplicate commit to be recognized."
  exit 1
}
grep -q "True branch-only commits on cleaner:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing unique-cleaner section."
  exit 1
}
grep -q "cleaner unique" <<<"$OUTPUT" || {
  echo "[FAIL] Expected cleaner unique commit to be listed."
  exit 1
}
grep -q "paths: old_only.txt" <<<"$OUTPUT" || {
  echo "[FAIL] Expected touched paths for the first older unique commit."
  exit 1
}
grep -q "paths: old_second_only.txt" <<<"$OUTPUT" || {
  echo "[FAIL] Expected touched paths for the second older unique commit."
  exit 1
}
grep -q "paths: clean_only.txt" <<<"$OUTPUT" || {
  echo "[FAIL] Expected touched paths for the cleaner unique commit."
  exit 1
}
grep -q "Code-only older commits already absorbed on cleaner:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing explicit absorbed older-commit section."
  exit 1
}
grep -q "Replay-safe code-only older commits still unique to older:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing explicit replay-safe older-commit section."
  exit 1
}
grep -q "Older mixed docs+code commits requiring manual review:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing explicit mixed older-commit section."
  exit 1
}
grep -q "Older doc/checkpoint-only commits requiring manual review or drop:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing explicit doc-only older-commit section."
  exit 1
}
grep -q "Suggested next step:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing suggested next-step section."
  exit 1
}
grep -q "git checkout cleaner" <<<"$OUTPUT" || {
  echo "[FAIL] Expected checkout guidance for the cleaner branch."
  exit 1
}
grep -q "git cherry-pick" <<<"$OUTPUT" || {
  echo "[FAIL] Expected exact cherry-pick guidance."
  exit 1
}
older_unique_1="$(git log --format='%H %s' --all --grep '^older unique$' | head -n 1 | cut -d' ' -f1)"
older_unique_2="$(git log --format='%H %s' --all --grep '^older unique 2$' | head -n 1 | cut -d' ' -f1)"
older_absorbed="$(git log --format='%H %s' --all --grep '^older absorbed$' | head -n 1 | cut -d' ' -f1)"
older_docs_only="$(git log --format='%H %s' --all --grep '^older docs only$' | head -n 1 | cut -d' ' -f1)"
older_mixed="$(git log --format='%H %s' --all --grep '^older mixed$' | head -n 1 | cut -d' ' -f1)"
expected_pick="git cherry-pick $older_unique_1 $older_unique_2"
grep -q "$expected_pick" <<<"$OUTPUT" || {
  echo "[FAIL] Expected cherry-pick guidance to preserve replay-safe older-first order."
  exit 1
}
if grep -q "git cherry-pick .*${older_absorbed}" <<<"$OUTPUT"; then
  echo "[FAIL] Absorbed code-only churn should not be auto-included in cherry-pick guidance."
  exit 1
fi
if grep -q "git cherry-pick .*${older_docs_only}" <<<"$OUTPUT"; then
  echo "[FAIL] Doc-only churn should not be auto-included in cherry-pick guidance."
  exit 1
fi
if grep -q "git cherry-pick .*${older_mixed}" <<<"$OUTPUT"; then
  echo "[FAIL] Mixed docs+code churn should not be auto-included in cherry-pick guidance."
  exit 1
fi
grep -q "older mixed docs+code commit(s) remain for manual review before replay" <<<"$OUTPUT" || {
  echo "[FAIL] Expected explicit mixed-commit review guidance."
  exit 1
}
grep -q "older-only doc/checkpoint commit(s) remain for manual review or drop" <<<"$OUTPUT" || {
  echo "[FAIL] Expected explicit doc-only review guidance."
  exit 1
}
grep -q "code-only older commit(s) are already absorbed on cleaner and can stay out of replay" <<<"$OUTPUT" || {
  echo "[FAIL] Expected explicit absorbed-commit guidance."
  exit 1
}
grep -q "$older_absorbed older absorbed" <<<"$OUTPUT" || {
  echo "[FAIL] Expected absorbed older commit to be listed in the absorbed bucket."
  exit 1
}
grep -q "$older_unique_1 older unique" <<<"$OUTPUT" || {
  echo "[FAIL] Expected replay-safe older commit to be listed in the explicit replay bucket."
  exit 1
}
grep -q "$older_mixed older mixed" <<<"$OUTPUT" || {
  echo "[FAIL] Expected mixed older commit to be listed in the mixed-review bucket."
  exit 1
}
grep -q "$older_docs_only older docs only" <<<"$OUTPUT" || {
  echo "[FAIL] Expected doc-only older commit to be listed in the doc-only review bucket."
  exit 1
}

echo "[PASS] Compare publish branch histories behaves as expected."
