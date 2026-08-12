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

older_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...${logic_sha} | awk '{print $1}')"
cleaner_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...${logic_sha} | awk '{print $2}')"

cat > ci-artifacts/branch-reconcile-2026-07-10.md <<EOF
# Branch Reconcile Note — refreshed 2026-07-28 22:20 Asia/Taipei

## Current state

- \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` is the cleaner publish candidate.
- \`fix/openclaw-config-path-and-local-mode\` still carries extra legacy local-only history, but that history is now fully accounted for as absorbed, patch-equivalent, or intentional doc-only drop noise.
- The latest non-handoff branch tip captured by this note is \`${logic_sha}\`; later doc-only checkpoint or branch-reconcile-only handoff refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
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
git push origin HEAD:transplant/fix-openclaw-config-path-and-local-mode-clean-stack >/dev/null

OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py")"
printf '%s\n' "$OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass on the synthetic handoff note."
  exit 1
}

export WORKTREE_PATH="$WORKTREE"
export OLDER_COUNT="$older_count"
export CLEANER_COUNT="$cleaner_count"
python3 - <<'PY'
import os
from pathlib import Path
path = Path(os.environ["WORKTREE_PATH"]) / "ci-artifacts" / "branch-reconcile-2026-07-10.md"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
    "origin/fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)
text = text.replace(
    f"  - `fix/openclaw-config-path-and-local-mode`: `{os.environ['OLDER_COUNT']}`",
    f"  - `origin/fix/openclaw-config-path-and-local-mode`: `{os.environ['OLDER_COUNT']}`",
)
path.write_text(text, encoding="utf-8")
PY
REMOTE_OLDER_REF_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py --older-ref origin/fix/openclaw-config-path-and-local-mode")"
printf '%s\n' "$REMOTE_OLDER_REF_OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$REMOTE_OLDER_REF_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass when --older-ref uses the GitHub remote-tracking ref."
  exit 1
}
python3 - <<'PY'
import os
from pathlib import Path
path = Path(os.environ["WORKTREE_PATH"]) / "ci-artifacts" / "branch-reconcile-2026-07-10.md"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "- `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` is the cleaner publish candidate.",
    "- `origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack` is the cleaner publish candidate.",
)
text = text.replace(
    "origin/fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
    "fix/openclaw-config-path-and-local-mode...origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)
text = text.replace(
    f"  - `origin/fix/openclaw-config-path-and-local-mode`: `{os.environ['OLDER_COUNT']}`",
    f"  - `fix/openclaw-config-path-and-local-mode`: `{os.environ['OLDER_COUNT']}`",
)
text = text.replace(
    f"  - `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`: `{os.environ['CLEANER_COUNT']}`",
    f"  - `origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack`: `{os.environ['CLEANER_COUNT']}`",
)
path.write_text(text, encoding="utf-8")
PY
REMOTE_CLEANER_REF_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py --cleaner-ref origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack")"
printf '%s\n' "$REMOTE_CLEANER_REF_OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$REMOTE_CLEANER_REF_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass when --cleaner-ref uses the GitHub remote-tracking ref."
  exit 1
}
python3 - <<'PY'
import os
from pathlib import Path
path = Path(os.environ["WORKTREE_PATH"]) / "ci-artifacts" / "branch-reconcile-2026-07-10.md"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "- `origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack` is the cleaner publish candidate.",
    "- `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` is the cleaner publish candidate.",
)
text = text.replace(
    "fix/openclaw-config-path-and-local-mode...origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
    "fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)
text = text.replace(
    f"  - `origin/transplant/fix-openclaw-config-path-and-local-mode-clean-stack`: `{os.environ['CLEANER_COUNT']}`",
    f"  - `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`: `{os.environ['CLEANER_COUNT']}`",
)
text = text.replace(
    "origin/fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
    "fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)
text = text.replace(
    f"  - `origin/fix/openclaw-config-path-and-local-mode`: `{os.environ['OLDER_COUNT']}`",
    f"  - `fix/openclaw-config-path-and-local-mode`: `{os.environ['OLDER_COUNT']}`",
)
path.write_text(text, encoding="utf-8")
PY

python3 - <<PY
from pathlib import Path
path = Path("$WORKTREE/ci-artifacts/branch-reconcile-2026-07-10.md")
text = path.read_text(encoding="utf-8")
text = text.replace("${logic_sha}", "${head_sha}")
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
text = text.replace("${head_sha}", "${logic_sha}")
text = text.replace("  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`${cleaner_count}\`", "  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`999\`")
path.write_text(text, encoding="utf-8")
PY
STALE_COUNT_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py" 2>&1 || true)"
printf '%s\n' "$STALE_COUNT_OUTPUT"
grep -q "cleaner divergence count is stale" <<<"$STALE_COUNT_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to reject stale divergence counts."
  exit 1
}

export CLEANER_COUNT="$cleaner_count"
export WORKTREE_PATH="$WORKTREE"
python3 - <<'PY'
import os
from pathlib import Path
path = Path(os.environ["WORKTREE_PATH"]) / "ci-artifacts" / "branch-reconcile-2026-07-10.md"
text = path.read_text(encoding="utf-8")
text = text.replace("`999`", f"`{os.environ['CLEANER_COUNT']}`")
text += "\n\nAs of `deadbee`, the local branch-reconcile handoff is back in sync with the tree.\n"
path.write_text(text, encoding="utf-8")
PY
LEGACY_APPENDIX_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py" 2>&1 || true)"
printf '%s\n' "$LEGACY_APPENDIX_OUTPUT"
grep -q "legacy appendix is stale" <<<"$LEGACY_APPENDIX_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to reject stale legacy appendix text."
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
- The latest non-handoff branch tip captured by this note is \`${non_doc_head_sha}\`; later doc-only checkpoint or branch-reconcile-only handoff refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
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

git push origin HEAD:fix/openclaw-config-path-and-local-mode >/dev/null

older_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack | awk '{print $1}')"
cleaner_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack | awk '{print $2}')"

cat > ci-artifacts/branch-reconcile-2026-07-10.md <<EOF
# Branch Reconcile Note — refreshed 2026-07-29 09:10 Asia/Taipei

## Current state

- \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` is the cleaner publish candidate.
- \`fix/openclaw-config-path-and-local-mode\` still carries extra legacy local-only history, but that history is now fully accounted for as absorbed, patch-equivalent, or intentional doc-only drop noise.
- The latest non-handoff branch tip captured by this note is \`${non_doc_head_sha}\`; later doc-only checkpoint or branch-reconcile-only handoff refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
- The current branch tip is already the tracked non-doc publish-boundary checkpoint: \`${non_doc_head_sha}\`, and it is already GitHub-visible.
- Divergence count from \`git rev-list --left-right --count fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`:
  - \`fix/openclaw-config-path-and-local-mode\`: \`${older_count}\`
  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`${cleaner_count}\`

## Best next move

Use \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` as the canonical local publish baseline. The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block should stay focused on the visible publish boundary: rerun \`Bootstrap Installer Preflight\` on that exact visible ref, then proceed to VM verifier preflight / proof if it stays green.
EOF

VISIBLE_HEAD_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py")"
printf '%s\n' "$VISIBLE_HEAD_OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$VISIBLE_HEAD_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass when the tracked non-doc checkpoint is already GitHub-visible."
  exit 1
}

cat > docs/checkpoint.md <<'EOF'
doc-only checkpoint already visible
EOF
git add docs/checkpoint.md
git commit -q -m "docs: refresh visible branch reconcile checkpoint"
visible_doc_tip_sha="$(git rev-parse --short HEAD)"
git push origin HEAD:fix/openclaw-config-path-and-local-mode >/dev/null

older_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...${non_doc_head_sha} | awk '{print $1}')"
cleaner_count="$(git rev-list --left-right --count refs/heads/fix/openclaw-config-path-and-local-mode...${non_doc_head_sha} | awk '{print $2}')"

cat > ci-artifacts/branch-reconcile-2026-07-10.md <<EOF
# Branch Reconcile Note — refreshed 2026-07-29 09:40 Asia/Taipei

## Current state

- \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` is the cleaner publish candidate.
- \`fix/openclaw-config-path-and-local-mode\` still carries extra legacy local-only history, but that history is now fully accounted for as absorbed, patch-equivalent, or intentional doc-only drop noise.
- The latest non-handoff branch tip captured by this note is \`${non_doc_head_sha}\`; later doc-only checkpoint or branch-reconcile-only handoff refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
- The last non-doc tracked publish-boundary checkpoint remains \`${non_doc_head_sha}\` while the exact current doc-only tip is already GitHub-visible.
- Divergence count from \`git rev-list --left-right --count fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`:
  - \`fix/openclaw-config-path-and-local-mode\`: \`${older_count}\`
  - \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\`: \`${cleaner_count}\`

## Best next move

Use \`transplant/fix-openclaw-config-path-and-local-mode-clean-stack\` as the canonical local publish baseline. The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block should stay focused on the visible publish boundary: rerun \`Bootstrap Installer Preflight\` on that exact visible ref, then proceed to VM verifier preflight / proof if it stays green.
EOF

VISIBLE_DOC_ONLY_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/check_branch_reconcile_handoff.py")"
printf '%s\n' "$VISIBLE_DOC_ONLY_OUTPUT"
grep -q "\[PASS\] Branch-reconcile handoff note matches current publish-boundary state" <<<"$VISIBLE_DOC_ONLY_OUTPUT" || {
  echo "[FAIL] Expected branch-reconcile checker to pass when the current doc-only tip is already GitHub-visible."
  exit 1
}

echo "[PASS] Branch-reconcile handoff smoke test passed"
