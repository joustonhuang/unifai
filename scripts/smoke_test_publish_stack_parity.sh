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
mkdir -p "$WORKTREE/ci-artifacts/bootstrap-preflight"
mkdir -p "$WORKTREE/ci-artifacts"

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
git remote add origin https://github.com/example/unifai.git
git update-ref refs/remotes/origin/base "$(git rev-parse base)"

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

git branch -q -f local-checkpoint candidate-good
git checkout -q expected
git branch --set-upstream-to=origin/base expected >/dev/null 2>&1
cat > docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md <<'EOF'
expected checkpoint docs refresh
EOF
git add docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md
git commit -q -m "docs only tip"
cat > ci-artifacts/bootstrap-preflight/commit-candidate.txt <<'EOF'
Commit candidate: publish-boundary maintenance bundle for visible-ref handoff @ deadbee
Current local checkpoint: local-checkpoint
Current checked-out branch tip: expected (docs only tip)
EOF
cat > ci-artifacts/branch-reconcile-2026-07-10.md <<'EOF'
# Branch Reconcile Note — synthetic

- differs only as checked-in handoff bookkeeping
EOF
git add ci-artifacts/branch-reconcile-2026-07-10.md
git commit -q -m "checked-in handoff note"

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

INFERRED_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_publish_stack_parity.py")"
printf '%s\n' "$INFERRED_OUTPUT"

if ! grep -q "\[INFO\] Inferred refs from current publish-boundary handoff:" <<<"$INFERRED_OUTPUT"; then
  echo "[FAIL] Expected inferred-handoff banner missing from parity output."
  exit 1
fi
if ! grep -q "  base: origin/base" <<<"$INFERRED_OUTPUT"; then
  echo "[FAIL] Expected inferred base ref missing from parity output."
  exit 1
fi
if ! grep -q "  candidate: local-checkpoint" <<<"$INFERRED_OUTPUT"; then
  echo "[FAIL] Expected inferred candidate ref missing from parity output."
  exit 1
fi
if ! grep -q "  expected: HEAD" <<<"$INFERRED_OUTPUT"; then
  echo "[FAIL] Expected inferred expected ref missing from parity output."
  exit 1
fi
if ! grep -q "\[PASS\] Candidate publish stack matches the expected functional tip." <<<"$INFERRED_OUTPUT"; then
  echo "[FAIL] Expected inferred-handoff parity pass verdict missing."
  exit 1
fi
if ! grep -q "Checked expected functional paths: 1" <<<"$INFERRED_OUTPUT"; then
  echo "[FAIL] Expected inferred-handoff parity run to ignore the doc-only tip delta."
  exit 1
fi

NO_UPSTREAM_DIR="$TMP_DIR/no-upstream"
cp -R "$WORKTREE" "$NO_UPSTREAM_DIR"
python3 - <<'PY' "$NO_UPSTREAM_DIR"
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
for path in root.rglob('.git'):
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
PY

cd "$NO_UPSTREAM_DIR"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"
git add .
git commit -q -m "snapshot"
git checkout -q -b no-upstream

STATUS=0
NO_UPSTREAM_OUTPUT="$("$REAL_BASH" -lc "cd '$NO_UPSTREAM_DIR' && python3 scripts/check_publish_stack_parity.py" 2>&1)" || STATUS=$?
printf '%s\n' "$NO_UPSTREAM_OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected inferred-handoff parity run to fail without an upstream."
  exit 1
fi
if ! grep -q "Could not infer refs: branch 'no-upstream' has no upstream; pass explicit refs instead." <<<"$NO_UPSTREAM_OUTPUT"; then
  echo "[FAIL] Expected no-upstream inferred-handoff failure message."
  exit 1
fi

DETACHED_DIR="$TMP_DIR/detached"
cp -R "$WORKTREE" "$DETACHED_DIR"
python3 - <<'PY' "$DETACHED_DIR"
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
for path in root.rglob('.git'):
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
PY

cd "$DETACHED_DIR"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"
git add .
git commit -q -m "snapshot"
git remote add origin https://github.com/example/unifai.git
git update-ref refs/remotes/origin/base "$(git rev-parse HEAD)"
git checkout -q --detach

STATUS=0
DETACHED_OUTPUT="$("$REAL_BASH" -lc "cd '$DETACHED_DIR' && python3 scripts/check_publish_stack_parity.py" 2>&1)" || STATUS=$?
printf '%s\n' "$DETACHED_OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Expected inferred-handoff parity run to fail from detached HEAD."
  exit 1
fi
if ! grep -q "Could not infer refs: detached HEAD does not provide a stable expected ref; pass explicit refs instead." <<<"$DETACHED_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD inferred-handoff failure message."
  exit 1
fi

cd "$WORKTREE"

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
