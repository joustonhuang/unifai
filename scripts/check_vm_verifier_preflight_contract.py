#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = REPO_ROOT / "scripts" / "run_vm_verifier_preflight.sh"
SMOKE = REPO_ROOT / "scripts" / "smoke_test_vm_verifier_preflight_wrapper.sh"
NO_GITHUB_REMOTE_SMOKE = REPO_ROOT / "scripts" / "smoke_test_vm_verifier_preflight_no_github_remote.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = PREFLIGHT.read_text(encoding="utf-8")
smoke_text = SMOKE.read_text(encoding="utf-8")
no_github_remote_smoke_text = NO_GITHUB_REMOTE_SMOKE.read_text(encoding="utf-8")

required = [
    ('Usage: bash scripts/run_vm_verifier_preflight.sh [--dry-run] [github-visible-ref-or-sha]', "Wrapper usage documents the --dry-run flag"),
    ('local_branch_name() {', "Wrapper centralizes refs/heads normalization for local branch refs"),
    ('is_github_remote_head_alias() {', "Wrapper detects symbolic GitHub remote HEAD aliases before verifier handoff"),
    ('reject_symbolic_github_remote_head_ref() {', "Wrapper rejects symbolic GitHub remote HEAD aliases before planning proceeds"),
    ('explicit_remote_ref_remote() {', "Wrapper can classify explicit remote-tracking refs before planning proceeds"),
    ('reject_non_github_remote_tracking_ref() {', "Wrapper rejects explicit remote-tracking refs that point at non-GitHub remotes"),
    ('github_visible_ref_for_verifier() {', "Wrapper can normalize GitHub remote-tracking refs for the verifier handoff"),
    ('if git show-ref --verify --quiet "refs/heads/$ref"; then', "Wrapper detects when the verifier handoff starts from a local branch"),
    ('upstream_ref="$(git rev-parse --abbrev-ref "$ref@{upstream}" 2>/dev/null)"', "Wrapper can inspect a local branch upstream for verifier handoff normalization"),
    ('printf \'%s\\n\' "$branch"', "Wrapper can hand off the tracked GitHub-visible branch name to the verifier"),
    ('printf \'%s\\n\' "${ref#refs/heads/}"', "Wrapper strips the refs/heads/ prefix before local-branch handling"),
    ("is the symbolic remote HEAD alias for GitHub remote", "Wrapper fails clearly on symbolic GitHub remote HEAD aliases"),
    ("Use a concrete branch/ref such as refs/remotes/$remote/<branch>, $remote/<branch>, or the resolved branch name before running VM verifier preflight.", "Wrapper explains how to recover from a symbolic GitHub remote HEAD alias"),
    ("points at remote '$remote', but that remote is not GitHub-backed and cannot be used as a GitHub-visible verifier ref.", "Wrapper fails clearly on explicit non-GitHub remote-tracking refs"),
    ("Use a local branch with a GitHub upstream, a GitHub remote-tracking ref, or a GitHub-visible commit SHA before running VM verifier preflight.", "Wrapper explains how to recover from explicit non-GitHub remote-tracking refs"),
    ('dry_run="${UNIFAI_VM_PREFLIGHT_DRY_RUN:-0}"', "Wrapper derives dry-run mode from env by default"),
    ('--dry-run)', "Wrapper parses the --dry-run flag"),
    ('Unknown option: $1', "Wrapper fails clearly on unknown options"),
    ('ensure_ref_is_github_visible "$ref" "$current_branch"', "Wrapper fails fast when an explicit local SHA is not GitHub-visible"),
    ('git branch -r --contains "$ref"', "Wrapper checks whether an explicit local commit is reachable from a GitHub remote branch"),
    ('Could not auto-detect a GitHub-backed remote for explicit ref visibility checking.', "Wrapper fails clearly when no GitHub remote can be detected for explicit SHAs"),
    ('Set a GitHub upstream or add a GitHub remote such as origin before using local commit SHAs here.', "Wrapper explains how to recover when no GitHub remote can be detected"),
    ("Push the branch tip first, or use a GitHub-visible branch/ref before running VM verifier preflight.", "Wrapper explains how to recover from a local-only explicit SHA"),
    ("bash scripts/check_vm_host_readiness.sh", "Wrapper runs host readiness before deeper preflight checks"),
    ("bash scripts/bootstrap_installer_preflight.sh", "Wrapper runs bootstrap installer preflight after host readiness"),
    ('git show-ref --verify --quiet "refs/heads/$local_branch_ref"', "Wrapper resolves refs/heads inputs before local-branch visibility checks"),
    ('effective_ref="$(local_branch_name "$ref")"', "Wrapper normalizes local refs/heads inputs before downstream steps"),
    ('verifier_ref="$(github_visible_ref_for_verifier "$effective_ref")"', "Wrapper derives a GitHub-visible verifier handoff ref"),
    ('Detached HEAD; pass an explicit GitHub-visible ref.', "Wrapper fails clearly when no ref is provided from a detached HEAD"),
    ('current_branch="$ref"', "Wrapper reuses the explicit ref when HEAD is detached but a ref was passed"),
    ('bash scripts/check_github_branch_visibility.sh "$effective_ref"', "Wrapper checks GitHub branch visibility for normalized local branches"),
    ("skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA.", "Wrapper explains why branch visibility is skipped for explicit refs/SHAs"),
    ('python3 scripts/check_github_check_gate.py "$effective_ref"', "Wrapper runs GitHub check gate inspection on the normalized chosen ref"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $verifier_ref', "Wrapper points to the VM verifier with a GitHub-visible handoff ref"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

smoke_required = [
    ('DETACHED_WORKTREE_DIR="$(mktemp -d -t unifai-vm-preflight-detached-XXXXXX)"', "Wrapper smoke test creates a detached worktree for detached-HEAD coverage"),
    ('git -C "$REPO_ROOT" worktree add --detach "$DETACHED_WORKTREE_DIR" HEAD >/dev/null', "Wrapper smoke test enters a real detached-HEAD repo state without disturbing the main worktree"),
    ('cp "$WRAPPER" "$DETACHED_WORKTREE_DIR/scripts/run_vm_verifier_preflight.sh"', "Wrapper smoke test copies the live wrapper into the detached worktree before detached-HEAD checks"),
    ('detect_github_remote()', "Wrapper smoke test derives the GitHub-backed remote dynamically"),
    ('GITHUB_REMOTE="$(detect_github_remote)"', "Wrapper smoke test resolves the GitHub-backed remote before building a visible SHA"),
    ('Could not find a GitHub-backed remote for wrapper smoke coverage.', "Wrapper smoke test fails clearly when no GitHub-backed remote can be found for visible-ref coverage"),
    ('resolve_visible_remote_ref() {', "Wrapper smoke test provides a helper to pick a GitHub-visible remote ref"),
    ('VISIBLE_REMOTE_REF="$(resolve_visible_remote_ref "$GITHUB_REMOTE")"', "Wrapper smoke test resolves an explicit GitHub-visible remote-tracking ref"),
    ('Could not resolve a GitHub-visible remote ref for wrapper smoke coverage.', "Wrapper smoke test fails clearly when it cannot derive a visible remote ref"),
    ('VISIBLE_VERIFIER_REF="${VISIBLE_REMOTE_REF#refs/remotes/}"', "Wrapper smoke test derives a GitHub-visible verifier handoff ref from the remote-tracking ref"),
    ('VISIBLE_VERIFIER_REF="${VISIBLE_VERIFIER_REF#*/}"', "Wrapper smoke test strips the remote name from the verifier handoff ref"),
    ('BRANCH_VERIFIER_REF="$BRANCH"', "Wrapper smoke test derives the expected verifier handoff ref for the local branch path"),
    ('Expected branch case to hand off the GitHub-visible verifier ref.', "Wrapper smoke test explains the branch-path verifier handoff expectation"),
    ('Expected default no-arg case to hand off the GitHub-visible verifier ref.', "Wrapper smoke test explains the default-path verifier handoff expectation"),
    ('VISIBLE_SHA="$(git -C "$REPO_ROOT" rev-parse "$VISIBLE_REMOTE_REF")"', "Wrapper smoke test derives the visible SHA from the resolved remote-tracking ref"),
    ('cd "$DETACHED_WORKTREE_DIR" &&', "Wrapper smoke test runs detached-HEAD coverage from the detached worktree"),
    ('DEFAULT_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER")"', "Wrapper smoke test exercises the no-argument default-branch path"),
    ('Expected current branch to be used when no ref is provided.', "Wrapper smoke test explains the default-branch expectation"),
    ('Expected branch visibility command missing in default no-arg case.', "Wrapper smoke test checks branch visibility in the default no-arg case"),
    ('Expected check-gate command missing in default no-arg case.', "Wrapper smoke test checks the check-gate step in the default no-arg case"),
    ('DETACHED_VISIBLE_SHA_OUTPUT="$(', "Wrapper smoke test captures detached-HEAD output for an explicit visible SHA"),
    ('Expected explicit visible SHA to be preserved in detached-HEAD case.', "Wrapper smoke test explains the detached-HEAD explicit-SHA expectation"),
    ('Expected detached-HEAD visible-SHA case to skip branch visibility.', "Wrapper smoke test explains the detached-HEAD branch-visibility skip expectation"),
    ('Detached-HEAD visible-SHA case should not run branch visibility.', "Wrapper smoke test guards that detached-HEAD explicit-SHA flow skips branch visibility"),
    ('Expected detached-HEAD visible-SHA case to plan the check-gate command.', "Wrapper smoke test explains the detached-HEAD check-gate expectation"),
    ('DETACHED_REMOTE_REF_OUTPUT="$(', "Wrapper smoke test captures detached-HEAD output for an explicit remote-tracking ref"),
    ('Expected explicit remote-tracking ref to be preserved in detached-HEAD case.', "Wrapper smoke test explains the detached-HEAD explicit remote-ref expectation"),
    ('Expected detached-HEAD remote-ref case to skip branch visibility.', "Wrapper smoke test explains the detached-HEAD remote-ref branch-visibility skip expectation"),
    ('Detached-HEAD remote-ref case should not run branch visibility.', "Wrapper smoke test guards that detached-HEAD explicit remote-ref flow skips branch visibility"),
    ('Expected detached-HEAD remote-ref case to plan the check-gate command.', "Wrapper smoke test explains the detached-HEAD remote-ref check-gate expectation"),
    ('"$WRAPPER" "$VISIBLE_REMOTE_REF"', "Wrapper smoke test exercises the wrapper with an explicit remote-tracking ref"),
    ('python3 scripts/check_github_check_gate.py $VISIBLE_REMOTE_REF', "Wrapper smoke test keeps the explicit remote-tracking ref intact for the check-gate step"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $VISIBLE_VERIFIER_REF', "Wrapper smoke test normalizes explicit remote-tracking refs for the verifier handoff"),
    ('Expected symbolic remote HEAD alias case to fail fast.', "Wrapper smoke test explains the symbolic remote HEAD alias fail-closed expectation"),
    ('Expected symbolic remote HEAD alias failure message missing.', "Wrapper smoke test checks the symbolic remote HEAD alias failure message"),
    ('Expected symbolic remote HEAD alias recovery guidance missing.', "Wrapper smoke test checks the symbolic remote HEAD alias recovery guidance"),
    ('Symbolic remote HEAD alias case should fail before the GitHub check-gate step.', "Wrapper smoke test guards that symbolic remote HEAD aliases fail before check-gate planning"),
    ('"$WRAPPER" "$GITHUB_REMOTE/HEAD"', "Wrapper smoke test exercises the short-form symbolic remote HEAD alias"),
    ('Expected short-form symbolic remote HEAD alias case to fail fast.', "Wrapper smoke test explains the short-form symbolic remote HEAD alias fail-closed expectation"),
    ('Expected short-form symbolic remote HEAD alias failure message missing.', "Wrapper smoke test checks the short-form symbolic remote HEAD alias failure message"),
    ('Expected short-form symbolic remote HEAD alias recovery guidance missing.', "Wrapper smoke test checks the short-form symbolic remote HEAD alias recovery guidance"),
    ('Short-form symbolic remote HEAD alias case should fail before the GitHub check-gate step.', "Wrapper smoke test guards that short-form symbolic remote HEAD aliases fail before check-gate planning"),
    ('"$WRAPPER" "refs/heads/$BRANCH"', "Wrapper smoke test exercises the wrapper with an explicit refs/heads local branch ref"),
    ('Expected normalized branch ref missing in explicit refs/heads case.', "Wrapper smoke test explains the explicit refs/heads branch-ref expectation"),
    ('Expected branch visibility command missing in explicit refs/heads case.', "Wrapper smoke test checks branch visibility in the explicit refs/heads case"),
    ('Explicit refs/heads case should not skip branch visibility.', "Wrapper smoke test keeps explicit refs/heads inputs on the branch-visibility path"),
    ('Expected normalized check-gate command missing in explicit refs/heads case.', "Wrapper smoke test checks the check-gate step in the explicit refs/heads case"),
    ('Expected explicit refs/heads case to hand off the GitHub-visible verifier ref.', "Wrapper smoke test explains the explicit refs/heads verifier handoff expectation"),
    ('"$WRAPPER" -- "$BRANCH"', "Wrapper smoke test exercises the -- separator path"),
    ('Expected branch ref missing when passed after --.', "Wrapper smoke test explains the -- separator branch-ref expectation"),
    ('Expected branch visibility command missing when ref is passed after --.', "Wrapper smoke test checks branch visibility when ref is passed after --"),
    ('Expected check-gate command missing when ref is passed after --.', "Wrapper smoke test checks the check-gate step when ref is passed after --"),
    ('Expected -- separator case to hand off the GitHub-visible verifier ref.', "Wrapper smoke test explains the -- separator verifier handoff expectation"),
    ('"$WRAPPER" "$BRANCH" extra-arg', "Wrapper smoke test exercises the extra-argument failure path"),
    ('Unexpected extra argument: extra-arg', "Wrapper smoke test expects the extra-argument parser failure message"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

no_github_remote_required = [
    ('UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "$LOCAL_SHA"', "No-GitHub-remote smoke test exercises the wrapper with an explicit local SHA"),
    ('Could not auto-detect a GitHub-backed remote for explicit ref visibility checking.', "No-GitHub-remote smoke test expects the missing-remote failure message"),
    ('Set a GitHub upstream or add a GitHub remote such as origin before using local commit SHAs here.', "No-GitHub-remote smoke test expects actionable missing-remote recovery guidance"),
    ('git init -q --bare "$REMOTE_REPO"', "No-GitHub-remote smoke test creates a non-GitHub remote fixture"),
    ('git remote add origin "$REMOTE_REPO"', "No-GitHub-remote smoke test attaches a non-GitHub origin fixture"),
    ('UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "origin/feature/no-github-remote"', "No-GitHub-remote smoke test exercises the short remote-tracking ref non-GitHub path"),
    ("points at remote 'origin', but that remote is not GitHub-backed", "No-GitHub-remote smoke test expects the non-GitHub remote-tracking failure message"),
    ('Expected short remote-tracking ref on a non-GitHub remote to fail.', "No-GitHub-remote smoke test explains the short remote-tracking ref fail-closed expectation"),
    ('Short remote-tracking ref non-GitHub case should fail before any preflight steps are planned.', "No-GitHub-remote smoke test guards that short remote-tracking refs fail before planning"),
    ('UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "refs/remotes/origin/feature/no-github-remote"', "No-GitHub-remote smoke test exercises the full remote-tracking ref non-GitHub path"),
    ('Expected full remote-tracking ref on a non-GitHub remote to fail.', "No-GitHub-remote smoke test explains the full remote-tracking ref fail-closed expectation"),
    ('Full remote-tracking ref non-GitHub case should fail before any preflight steps are planned.', "No-GitHub-remote smoke test guards that full remote-tracking refs fail before planning"),
    ('scripts/check_vm_host_readiness.sh', "No-GitHub-remote smoke test guards that failure happens before host-readiness planning appears"),
    ('Expected explicit local SHA case to fail when no GitHub remote exists.', "No-GitHub-remote smoke test explains the explicit-SHA fail-closed expectation"),
    ('git checkout -q --detach', "No-GitHub-remote smoke test forces a detached-HEAD repo state"),
    ('UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh 2>&1', "No-GitHub-remote smoke test exercises the no-arg detached-HEAD path"),
    ('Detached HEAD; pass an explicit GitHub-visible ref.', "No-GitHub-remote smoke test expects the detached-HEAD failure message"),
    ('Expected no-arg detached-HEAD case to fail.', "No-GitHub-remote smoke test explains the detached-HEAD fail-closed expectation"),
    ('Detached-HEAD case should fail before any preflight steps are planned.', "No-GitHub-remote smoke test guards that detached-HEAD failure happens before step planning"),
]

for needle, message in no_github_remote_required:
    if needle not in no_github_remote_smoke_text:
        fail(message)
    ok(message)

forbidden_smoke_needles = [
    "github/fix/openclaw-config-path-and-local-mode",
]

for needle in forbidden_smoke_needles:
    if needle in smoke_text:
        fail(f"Wrapper smoke test must not hard-code stale GitHub-visible refs ({needle})")
    ok(f"Wrapper smoke test does not hard-code stale GitHub-visible refs ({needle})")
print('[PASS] VM verifier preflight wrapper contract looks sane')
