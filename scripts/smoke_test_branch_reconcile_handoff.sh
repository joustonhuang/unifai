#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: branch-reconcile handoff checker ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-branch-reconcile-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

REMOTE="$TMP_DIR/remote.git"
WORKTREE="$TMP_DIR/work"

git init --bare "$REMOTE" >/dev/null
git clone "$REMOTE" "$WORKTREE" >/dev/null
mkdir -p "$WORKTREE/scripts"
cp "$REPO_ROOT/scripts/check_branch_reconcile_handoff.py" "$WORKTREE/scripts/check_branch_reconcile_handoff.py"
chmod +x "$WORKTREE/scripts/check_branch_reconcile_handoff.py"

cd "$WORKTREE"
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

mkdir -p docs ci-artifacts scripts
cat > logic.py <<'EOF'
print("base")
EOF
git add logic.py
git commit -q -m "base"
git branch -M fix/openclaw-config-path-and-local-mode
git push -u origin fix/openclaw-config-path-and-local-mode >/dev/null

git checkout -q -b transplant/fix-openclaw-config-path-and-local-mode-clean-stack
git branch --set-upstream-to=origin/fix/openclaw-config-path-and-local-mode >/dev/null

cat > logic.py <<'EOF'
print("logic change")
EOF
git add logic.py
git commit -q -m "tests: add logic commit"
logic_sha="$(git rev-parse --short HEAD)"

cat > docs/checkpoint.md <<'EOF'
doc-only checkpoint
EOF
git add docs/checkpoint.md
git commit -q -m "docs: refresh visible verifier boundary state"
docs_sha="$(git rev-parse --short HEAD)"

older_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack | awk '{print $1}')"
cleaner_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack | awk '{print $2}')"

cat > ci-artifacts/branch-reconcile-2026-07-10.md <<EOF
# Branch Reconcile Note — refreshed 2026-07-28 22:20 Asia/Taipei

## Current state

- \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` is the cleaner publish candidate.
- \`fix/openclaw-config-path-and-local-mode\` still carries extra legacy local-only history, but that history is now fully accounted for as absorbed, patch-equivalent, or intentional doc-only drop noise.
- The latest non-handoff branch tip captured by this note is \`${docs_sha}\`; later branch-reconcile-only note refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
- The last non-doc tracked publish-boundary checkpoint remains \`${logic_sha}\` until the current doc-only tip becomes GitHub-visible.
- Divergence count from \`git rev-list --left-right --count fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`:
  - \`fix/openclaw-config-path-and-local-mode\`: \`${older_count}\`
  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`${cleaner_count}\`

## Best next move

Use \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` as the canonical local publish baseline. The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block should stay focused on the external publish boundary: make the current transplant tip GitHub-visible, rerun \`Bootstrap Installer Preflight\` on that exact visible ref, then proceed to VM verifier preflight / proof if it stays green.
EOF
git add ci-artifacts/branch-reconcile-2026-07-10.md
git commit -q -m "docs: refresh branch reconcile publish handoff"
head_sha="$(git rev-parse --short HEAD)"

OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py")"
printf '%s\n' "$OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass on the synthetic handoff note."
  exit 1
}

python3 - <<PY
from pathlib import Path
path = Path("$WORKTREE/ci-artifacts/branch-reconcile-2026-07-10.md")
text = path.read_text(encoding="utf-8")
text = text.replace("${docs_sha}", "${head_sha}")
path.write_text(text, encoding="utf-8")
PY
STALE_TIP_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py" 2>&1 || true)"
printf '%s\n' "$STALE_TIP_OUTPUT"
grep -q "captured tip line is stale" <<<"$STALE_TIP_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to reject a note that captures the bookkeeping HEAD tip."
  exit 1
}

python3 - <<PY
from pathlib import Path
path = Path("$WORKTREE/ci-artifacts/branch-reconcile-2026-07-10.md")
text = path.read_text(encoding="utf-8")
text = text.replace("${head_sha}", "${docs_sha}")
text = text.replace("  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`${cleaner_count}\`", "  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`999\`")
path.write_text(text, encoding="utf-8")
PY
STALE_COUNT_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py" 2>&1 || true)"
printf '%s\n' "$STALE_COUNT_OUTPUT"
grep -q "cleaner divergence count is stale" <<<"$STALE_COUNT_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to reject stale divergence counts."
  exit 1
}

cat > logic.py <<'EOF'
print("second logic change")
EOF
git add logic.py
git commit -q -m "scripts: advance publish-boundary logic tip"
non_doc_head_sha="$(git rev-parse --short HEAD)"
older_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack | awk '{print $1}')"
cleaner_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack | awk '{print $2}')"

cat > ci-artifacts/branch-reconcile-2026-07-10.md <<EOF
# Branch Reconcile Note — refreshed 2026-07-29 08:20 Asia/Taipei

## Current state

- \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` is the cleaner publish candidate.
- \`fix/openclaw-config-path-and-local-mode\` still carries extra legacy local-only history, but that history is now fully accounted for as absorbed, patch-equivalent, or intentional doc-only drop noise.
- The latest non-handoff branch tip captured by this note is \`${non_doc_head_sha}\`; later branch-reconcile-only note refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
- The current branch tip is already the tracked non-doc publish-boundary checkpoint: \`${non_doc_head_sha}\`. It still needs to become GitHub-visible.
- Divergence count from \`git rev-list --left-right --count fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`:
  - \`fix/openclaw-config-path-and-local-mode\`: \`${older_count}\`
  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`${cleaner_count}\`

## Best next move

Use \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` as the canonical local publish baseline. The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block should stay focused on the external publish boundary: make the current transplant tip GitHub-visible, rerun \`Bootstrap Installer Preflight\` on that exact visible ref, then proceed to VM verifier preflight / proof if it stays green.
EOF

NON_DOC_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py")"
printf '%s\n' "$NON_DOC_OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$NON_DOC_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass when the tracked non-doc checkpoint is the current branch tip."
  exit 1
}

echo "[PASS] Branch-reconcile handoff smoke test passed"
