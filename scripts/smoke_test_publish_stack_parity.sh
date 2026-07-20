#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: publish stack parity checker ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-publish-parity-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

WORKTREE="$TMP_DIR/repo"
mkdir -p "$WORKTREE/docs" "$WORKTREE/scripts"
cp "$REPO_ROOT/scripts/check_publish_stack_parity.py" "$WORKTREE/scripts/check_publish_stack_parity.py"
chmod +x "$WORKTREE/scripts/check_publish_stack_parity.py"

cd "$WORKTREE"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

cat > app.py <<'EOF'
print("base")
EOF
cat > docs/BOOTSTRAP_VM_VERIFICATION.md <<'EOF'
base docs
EOF
git add app.py docs/BOOTSTRAP_VM_VERIFICATION.md
git commit -q -m "base"
git branch -M base

git checkout -q -b expected
cat > app.py <<'EOF'
print("functional change")
print("expected shared line")
EOF
cat > docs/BOOTSTRAP_VM_VERIFICATION.md <<'EOF'
expected docs refresh
EOF
git add app.py docs/BOOTSTRAP_VM_VERIFICATION.md
git commit -q -m "expected"

git checkout -q base
git checkout -q -b candidate-good
cat > app.py <<'EOF'
print("functional change")
print("expected shared line")
print("candidate extension")
EOF
cat > docs/BOOTSTRAP_VM_VERIFICATION.md <<'EOF'
candidate docs refresh
EOF
cat > candidate_extra.py <<'EOF'
print("candidate-only helper")
EOF
git add app.py docs/BOOTSTRAP_VM_VERIFICATION.md
git add candidate_extra.py
git commit -q -m "candidate good"

PASS_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_publish_stack_parity.py base candidate-good expected")"
printf '%s\n' "$PASS_OUTPUT"

if ! grep -q "\[PASS\] Candidate publish stack matches the expected functional tip." <<<"$PASS_OUTPUT"; then
  echo "[FAIL] Expected passing parity verdict missing."
  exit 1
fi
if ! grep -q "Ignored candidate-only paths:" <<<"$PASS_OUTPUT"; then
  echo "[FAIL] Expected candidate-only path banner missing from parity pass output."
  exit 1
fi
if ! grep -q "candidate_extra.py" <<<"$PASS_OUTPUT"; then
  echo "[FAIL] Expected candidate-only helper path to be reported and ignored."
  exit 1
fi

git checkout -q base
git checkout -q -b candidate-bad
cat > app.py <<'EOF'
print("wrong functional change")
print("candidate extension")
EOF
cat > docs/BOOTSTRAP_VM_VERIFICATION.md <<'EOF'
candidate docs refresh
EOF
cat > candidate_extra.py <<'EOF'
print("candidate-only helper")
EOF
git add app.py docs/BOOTSTRAP_VM_VERIFICATION.md candidate_extra.py
git commit -q -m "candidate bad"

STATUS=0
FAIL_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_publish_stack_parity.py base candidate-bad expected" 2>&1)" || STATUS=$?
printf '%s\n' "$FAIL_OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected parity checker to fail on a functional mismatch."
  exit 1
fi

if ! grep -q "app.py" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected functional mismatch path missing from parity failure output."
  exit 1
fi
if ! grep -q "Ignored candidate-only paths:" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected candidate-only path banner missing from parity failure output."
  exit 1
fi
if ! grep -q "candidate_extra.py" <<<"$FAIL_OUTPUT"; then
  echo "[FAIL] Expected candidate-only helper path to be reported and ignored in failure output."
  exit 1
fi

echo "[PASS] Publish stack parity checker behaves as expected."
