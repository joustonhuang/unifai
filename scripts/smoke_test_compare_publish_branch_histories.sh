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

git checkout -q -b fix/older
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
git checkout -q -b transplant/cleaner
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

OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/compare_publish_branch_histories.py fix/older transplant/cleaner")"
printf '%s\n' "$OUTPUT"

grep -q "Patch-equivalent commits already represented on transplant/cleaner:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing duplicate section for cleaner branch."
  exit 1
}
grep -q "older duplicate" <<<"$OUTPUT" || {
  echo "[FAIL] Expected older duplicate commit to be recognized."
  exit 1
}
grep -q "True branch-only commits on fix/older:" <<<"$OUTPUT" || {
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
grep -q "Patch-equivalent commits already represented on fix/older:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing duplicate section for older branch."
  exit 1
}
grep -q "cleaner duplicate" <<<"$OUTPUT" || {
  echo "[FAIL] Expected cleaner duplicate commit to be recognized."
  exit 1
}
grep -q "True branch-only commits on transplant/cleaner:" <<<"$OUTPUT" || {
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
grep -q "Code-only older commits already absorbed on transplant/cleaner:" <<<"$OUTPUT" || {
  echo "[FAIL] Missing explicit absorbed older-commit section."
  exit 1
}
grep -q "Replay-safe code-only older commits still unique to fix/older:" <<<"$OUTPUT" || {
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
grep -q "git checkout transplant/cleaner" <<<"$OUTPUT" || {
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
grep -q "code-only older commit(s) are already absorbed on transplant/cleaner and can stay out of replay" <<<"$OUTPUT" || {
  echo "[FAIL] Expected explicit absorbed-commit guidance."
  exit 1
}
grep -q "$older_absorbed older absorbed" <<<"$OUTPUT" || {
  echo "[FAIL] Expected absorbed older commit to be listed in the absorbed bucket."
  exit 1
}
grep -q "$older_absorbed older absorbed"$'\n'"    paths: absorbed.txt" <<<"$OUTPUT" || {
  echo "[FAIL] Expected absorbed older commit bucket to show touched paths."
  exit 1
}
grep -q "older branch still has 4 older-only commit(s) to review/drop consciously" <<<"$OUTPUT" || {
  echo "[FAIL] Expected unresolved older-only summary to exclude only absorbed churn, not replay/doc/mixed work."
  exit 1
}

mkdir -p "$WORKTREE/ci-artifacts"
WRITE_OUTPUT="$("$REAL_BASH" -lc "cd '$WORKTREE' && python3 scripts/compare_publish_branch_histories.py --write-reconciliation-note --generated-at '2026-08-09 14:20 Asia/Taipei' fix/older transplant/cleaner")"
printf '%s\n' "$WRITE_OUTPUT"

grep -q "Wrote reconciliation note to ci-artifacts/publish-stack-reconciliation-next-step.txt" <<<"$WRITE_OUTPUT" || {
  echo "[FAIL] Expected tracked-note refresh verdict."
  exit 1
}
grep -q "Generated: 2026-08-09 14:20 Asia/Taipei" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected deterministic reconciliation note timestamp."
  exit 1
}
grep -q "baseline branch is ahead 4 over fix/older" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record the live cleaner-ahead count."
  exit 1
}
grep -q "2 code-only older commits remain to replay from fix/older" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record replay-safe older commit count."
  exit 1
}
grep -q "1 older code-only commits are already absorbed on the baseline branch" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record absorbed older code-only count."
  exit 1
}
grep -q "1 older mixed docs+code commits remain for manual review" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record mixed older review count."
  exit 1
}
grep -q "1 older doc/checkpoint-only commits remain for manual review or drop" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record doc-only older review count."
  exit 1
}
grep -q "0 older commits are already reviewed and ready to drop" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record reviewed-drop count."
  exit 1
}
grep -q "3 cleaner-only commits remain on the baseline branch relative to the older local fix branch" "$WORKTREE/ci-artifacts/publish-stack-reconciliation-next-step.txt" || {
  echo "[FAIL] Expected reconciliation note to record cleaner-only baseline count."
  exit 1
}

ABSORB_DIR="$(mktemp -d -t unifai-compare-publish-history-absorbed-XXXXXX)"
trap 'rm -rf "$TMP_DIR" "$ABSORB_DIR"' EXIT
ABSORB_WORKTREE="$ABSORB_DIR/repo"
mkdir -p "$ABSORB_WORKTREE/scripts"
cp "$REPO_ROOT/scripts/compare_publish_branch_histories.py" "$ABSORB_WORKTREE/scripts/compare_publish_branch_histories.py"
chmod +x "$ABSORB_WORKTREE/scripts/compare_publish_branch_histories.py"

cd "$ABSORB_WORKTREE"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

cat > absorbed.txt <<'EOF'
base
EOF
git add absorbed.txt
git commit -q -m "base"
git branch -M base

git checkout -q -b fix/older
cat > absorbed.txt <<'EOF'
absorbed from older
EOF
git add absorbed.txt
git commit -q -m "older absorbed"

git checkout -q base
git checkout -q -b transplant/cleaner
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

ABSORB_OUTPUT="$("$REAL_BASH" -lc "cd '$ABSORB_WORKTREE' && python3 scripts/compare_publish_branch_histories.py fix/older transplant/cleaner")"
printf '%s\n' "$ABSORB_OUTPUT"

grep -q "no code-only older commits remain to replay from fix/older" <<<"$ABSORB_OUTPUT" || {
  echo "[FAIL] Expected absorbed-only older history to skip replay guidance."
  exit 1
}
grep -q "code-only older commit(s) are already absorbed on transplant/cleaner and can stay out of replay" <<<"$ABSORB_OUTPUT" || {
  echo "[FAIL] Expected absorbed-only older history to report absorbed churn."
  exit 1
}
grep -q "no older-only commits remain" <<<"$ABSORB_OUTPUT" || {
  echo "[FAIL] Expected absorbed-only older history to clear the final unresolved summary."
  exit 1
}
if grep -q "older branch still has" <<<"$ABSORB_OUTPUT"; then
  echo "[FAIL] Absorbed-only older history should not claim unresolved older commits remain."
  exit 1
fi
grep -q "$older_unique_1 older unique" <<<"$OUTPUT" || {
  echo "[FAIL] Expected replay-safe older commit to be listed in the explicit replay bucket."
  exit 1
}
grep -q "$older_unique_1 older unique"$'\n'"    paths: old_only.txt" <<<"$OUTPUT" || {
  echo "[FAIL] Expected replay-safe older commit bucket to show touched paths."
  exit 1
}
grep -q "$older_mixed older mixed" <<<"$OUTPUT" || {
  echo "[FAIL] Expected mixed older commit to be listed in the mixed-review bucket."
  exit 1
}
grep -q "$older_mixed older mixed"$'\n'"    paths: docs/helper-notes.md, helper.py" <<<"$OUTPUT" || {
  echo "[FAIL] Expected mixed older commit bucket to show touched paths."
  exit 1
}
grep -q "$older_docs_only older docs only" <<<"$OUTPUT" || {
  echo "[FAIL] Expected doc-only older commit to be listed in the doc-only review bucket."
  exit 1
}
grep -q "$older_docs_only older docs only"$'\n'"    paths: docs/checkpoint.md" <<<"$OUTPUT" || {
  echo "[FAIL] Expected doc-only older commit bucket to show touched paths."
  exit 1
}

REFS_OUTPUT="$("$REAL_BASH" -lc "cd '$ABSORB_WORKTREE' && python3 scripts/compare_publish_branch_histories.py refs/heads/fix/older refs/heads/transplant/cleaner")"
printf '%s\n' "$REFS_OUTPUT"

grep -q "older:   refs/heads/fix/older" <<<"$REFS_OUTPUT" || {
  echo "[FAIL] Expected explicit refs/heads older ref to remain visible in output."
  exit 1
}
grep -q "cleaner: refs/heads/transplant/cleaner" <<<"$REFS_OUTPUT" || {
  echo "[FAIL] Expected explicit refs/heads cleaner ref to remain visible in output."
  exit 1
}

python3 - <<'PY'
import importlib.util
from pathlib import Path

module_path = Path("/home/little7/.openclaw/workspace/tmp/unifai-autonomous/scripts/compare_publish_branch_histories.py")
spec = importlib.util.spec_from_file_location("compare_publish_branch_histories", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

expected = module.reviewed_drop_candidates(
    "fix/openclaw-config-path-and-local-mode",
    "transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)
heads = module.reviewed_drop_candidates(
    "refs/heads/fix/openclaw-config-path-and-local-mode",
    "refs/heads/transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)
remote = module.reviewed_drop_candidates(
    "refs/remotes/github/fix/openclaw-config-path-and-local-mode",
    "refs/remotes/github/transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
)

if not expected:
    raise SystemExit("[FAIL] Expected known reviewed-drop candidates for the canonical branch pair.")
if heads != expected:
    raise SystemExit("[FAIL] refs/heads branch-pair lookup should match the canonical reviewed-drop candidate set.")
if remote != expected:
    raise SystemExit("[FAIL] refs/remotes branch-pair lookup should match the canonical reviewed-drop candidate set.")
PY

KNOWN_ABSORB_DIR="$(mktemp -d -t unifai-compare-publish-history-known-XXXXXX)"
trap 'rm -rf "$TMP_DIR" "$ABSORB_DIR" "$KNOWN_ABSORB_DIR"' EXIT
KNOWN_ABSORB_WORKTREE="$KNOWN_ABSORB_DIR/repo"
mkdir -p "$KNOWN_ABSORB_WORKTREE/scripts"
cp "$REPO_ROOT/scripts/compare_publish_branch_histories.py" "$KNOWN_ABSORB_WORKTREE/scripts/compare_publish_branch_histories.py"
chmod +x "$KNOWN_ABSORB_WORKTREE/scripts/compare_publish_branch_histories.py"

cd "$KNOWN_ABSORB_WORKTREE"
git init -q
git config user.name "UnifAI Smoke"
git config user.email "smoke@unifai.invalid"

mkdir -p scripts
cat > scripts/refresh_vm_verifier_checkpoint_state.py <<'EOF'
def refresh():
    return "base"
EOF
git add scripts/refresh_vm_verifier_checkpoint_state.py
git commit -q -m "base"
git branch -M base

git checkout -q -b fix/older
cat > scripts/refresh_vm_verifier_checkpoint_state.py <<'EOF'
def refresh():
    return "older-only tracking helper"
EOF
git add scripts/refresh_vm_verifier_checkpoint_state.py
git commit -q -m "scripts: stabilize verifier checkpoint refresh tracking"

git checkout -q base
git checkout -q -b transplant/cleaner
cat > scripts/refresh_vm_verifier_checkpoint_state.py <<'EOF'
CHECKPOINT_DOCS = {
    "docs/BOOTSTRAP_VM_VERIFICATION.md",
}


def is_checkpoint_doc_only_commit(ref: str) -> bool:
    return ref.startswith("docs/")


def refresh():
    tracked_ref = "HEAD"
    while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):
        tracked_ref = "parent"
    return tracked_ref
EOF
cat > scripts/smoke_test_vm_verifier_checkpoint_refresh.py <<'EOF'
def smoke_lines():
    run(["git", "commit", "-m", "docs: sync visible verifier boundary state"], work)
    subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)
    assert f"through `{stable_head}` (`{stable_subject}`), {stable_ahead} commits ahead in total" in stable_boundary
    assert f"Latest tracked local head in the stack: `{stable_head}`" in stable_checkpoint
    assert f"Tracked local branch state at checkpoint: ahead by {stable_ahead} commits over the GitHub-visible branch head" in stable_checkpoint
EOF
git add scripts/refresh_vm_verifier_checkpoint_state.py scripts/smoke_test_vm_verifier_checkpoint_refresh.py
git commit -q -m "cleaner: generalize checkpoint refresh tracking coverage"

KNOWN_ABSORB_OUTPUT="$("$REAL_BASH" -lc "cd '$KNOWN_ABSORB_WORKTREE' && python3 scripts/compare_publish_branch_histories.py fix/older transplant/cleaner")"
printf '%s\n' "$KNOWN_ABSORB_OUTPUT"

grep -q "Code-only older commits already absorbed on transplant/cleaner:" <<<"$KNOWN_ABSORB_OUTPUT" || {
  echo "[FAIL] Expected known-absorption smoke case to report an absorbed older code-only commit."
  exit 1
}
grep -q "scripts: stabilize verifier checkpoint refresh tracking" <<<"$KNOWN_ABSORB_OUTPUT" || {
  echo "[FAIL] Expected known-absorption smoke case to keep the absorbed checkpoint-refresh commit visible."
  exit 1
}
grep -q "no code-only older commits remain to replay from fix/older" <<<"$KNOWN_ABSORB_OUTPUT" || {
  echo "[FAIL] Expected known-absorption smoke case to suppress replay guidance once the marker path absorbs the older commit."
  exit 1
}
grep -q "no older-only commits remain" <<<"$KNOWN_ABSORB_OUTPUT" || {
  echo "[FAIL] Expected known-absorption smoke case to clear the unresolved older-only summary."
  exit 1
}

echo "[PASS] Compare publish branch histories behaves as expected."
