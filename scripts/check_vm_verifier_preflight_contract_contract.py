#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_vm_verifier_preflight_contract.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('PREFLIGHT = REPO_ROOT / "scripts" / "run_vm_verifier_preflight.sh"', "VM verifier preflight wrapper contract checker targets run_vm_verifier_preflight.sh"),
    ('SMOKE = REPO_ROOT / "scripts" / "smoke_test_vm_verifier_preflight_wrapper.sh"', "VM verifier preflight wrapper contract checker targets the wrapper smoke test"),
    ('NO_GITHUB_REMOTE_SMOKE = REPO_ROOT / "scripts" / "smoke_test_vm_verifier_preflight_no_github_remote.sh"', "VM verifier preflight wrapper contract checker targets the no-GitHub-remote smoke test"),
    ('Detached HEAD; pass an explicit GitHub-visible ref.', "VM verifier preflight wrapper contract checker requires detached-HEAD fail-closed coverage"),
    ('Unknown option: $1', "VM verifier preflight wrapper contract checker requires unknown-option fail-closed coverage"),
    ('current_branch="$ref"', "VM verifier preflight wrapper contract checker requires detached-HEAD explicit-ref reuse coverage"),
    ('effective_ref="$(local_branch_name "$ref")"', "VM verifier preflight wrapper contract checker requires local branch-ref normalization coverage"),
    ('bash scripts/check_github_branch_visibility.sh "$effective_ref"', "VM verifier preflight wrapper contract checker requires normalized branch-visibility coverage"),
    ('python3 scripts/check_github_check_gate.py "$verifier_ref"', "VM verifier preflight wrapper contract checker requires GitHub-visible verifier-ref check-gate coverage"),
    ('github_visible_ref_for_verifier() {', "VM verifier preflight wrapper contract checker requires GitHub-visible verifier-ref normalization coverage"),
    ('is_github_remote_head_alias() {', "VM verifier preflight wrapper contract checker requires symbolic GitHub remote HEAD alias detection coverage"),
    ('reject_symbolic_github_remote_head_ref() {', "VM verifier preflight wrapper contract checker requires symbolic GitHub remote HEAD alias rejection coverage"),
    ('explicit_remote_ref_remote() {', "VM verifier preflight wrapper contract checker requires explicit remote-tracking ref classification coverage"),
    ('reject_non_github_remote_tracking_ref() {', "VM verifier preflight wrapper contract checker requires explicit non-GitHub remote-tracking ref rejection coverage"),
    ('reject_stale_visible_ref_for_current_branch() {', "VM verifier preflight wrapper contract checker requires stale-visible-ref fail-closed coverage"),
    ('if git show-ref --verify --quiet "refs/heads/$ref"; then', "VM verifier preflight wrapper contract checker requires local-branch verifier handoff coverage"),
    ('upstream_ref="$(git rev-parse --abbrev-ref "$ref@{upstream}" 2>/dev/null)"', "VM verifier preflight wrapper contract checker requires upstream-aware verifier handoff coverage"),
    ('Wrapper can hand off the tracked GitHub-visible branch name to the verifier', "VM verifier preflight wrapper contract checker requires tracked GitHub branch-name handoff coverage"),
    ('verifier_ref="$(github_visible_ref_for_verifier "$effective_ref")"', "VM verifier preflight wrapper contract checker requires explicit verifier-ref derivation coverage"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $verifier_ref', "VM verifier preflight wrapper contract checker requires explicit next-step handoff coverage"),
    ('smoke_required = [', "VM verifier preflight wrapper contract checker keeps explicit wrapper smoke requirements"),
    ('DETACHED_WORKTREE_DIR="$(mktemp -d -t unifai-vm-preflight-detached-XXXXXX)"', "VM verifier preflight wrapper contract checker requires detached-worktree smoke coverage"),
    ('git -C "$REPO_ROOT" worktree add --detach "$DETACHED_WORKTREE_DIR" HEAD >/dev/null', "VM verifier preflight wrapper contract checker requires a real detached-HEAD worktree setup"),
    ('resolve_visible_remote_ref() {', "VM verifier preflight wrapper contract checker requires a helper that resolves a GitHub-visible remote ref"),
    ('VISIBLE_REMOTE_REF="$(resolve_visible_remote_ref "$GITHUB_REMOTE")"', "VM verifier preflight wrapper contract checker requires explicit visible remote-ref resolution coverage"),
    ('BRANCH_VERIFIER_REF="$BRANCH"', "VM verifier preflight wrapper contract checker requires branch-path verifier handoff coverage"),
    ('VISIBLE_SHA="$(git -C "$REPO_ROOT" rev-parse "$VISIBLE_REMOTE_REF")"', "VM verifier preflight wrapper contract checker requires explicit visible-SHA derivation coverage"),
    ('DETACHED_VISIBLE_SHA_OUTPUT="$(', "VM verifier preflight wrapper contract checker requires detached-HEAD explicit-SHA smoke output capture"),
    ('Expected detached-HEAD visible-SHA case to skip branch visibility.', "VM verifier preflight wrapper contract checker requires detached-HEAD branch-visibility skip coverage"),
    ('"$WRAPPER" "$VISIBLE_REMOTE_REF"', "VM verifier preflight wrapper contract checker requires explicit remote-tracking ref smoke coverage"),
    ('python3 scripts/check_github_check_gate.py $VISIBLE_VERIFIER_REF', "VM verifier preflight wrapper contract checker requires remote-tracking ref check-gate coverage"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $VISIBLE_VERIFIER_REF', "VM verifier preflight wrapper contract checker requires normalized remote-tracking verifier handoff coverage"),
    ("resolves to the current GitHub-visible head for '$current_branch', but local branch '$current_branch' is ahead by $ahead commit(s).", "VM verifier preflight wrapper contract checker requires stale explicit visible-ref failure guidance"),
    ("Push/reconcile the local tip first, or rerun against the exact published SHA only after the local checkpoint-handoff stack matches that GitHub-visible ref.", "VM verifier preflight wrapper contract checker requires stale explicit visible-ref recovery guidance"),
    ('Expected symbolic remote HEAD alias case to fail fast.', "VM verifier preflight wrapper contract checker requires symbolic remote HEAD alias fail-closed coverage"),
    ('Expected symbolic remote HEAD alias recovery guidance missing.', "VM verifier preflight wrapper contract checker requires symbolic remote HEAD alias recovery guidance coverage"),
    ('Symbolic remote HEAD alias case should fail before the GitHub check-gate step.', "VM verifier preflight wrapper contract checker requires symbolic remote HEAD alias fail-before-planning coverage"),
    ('"$WRAPPER" "$GITHUB_REMOTE/HEAD"', "VM verifier preflight wrapper contract checker requires short-form symbolic remote HEAD alias smoke coverage"),
    ('Expected short-form symbolic remote HEAD alias case to fail fast.', "VM verifier preflight wrapper contract checker requires short-form symbolic remote HEAD alias fail-closed coverage"),
    ('Expected short-form symbolic remote HEAD alias failure message missing.', "VM verifier preflight wrapper contract checker requires short-form symbolic remote HEAD alias failure-message coverage"),
    ('Expected short-form symbolic remote HEAD alias recovery guidance missing.', "VM verifier preflight wrapper contract checker requires short-form symbolic remote HEAD alias recovery-guidance coverage"),
    ('Short-form symbolic remote HEAD alias case should fail before the GitHub check-gate step.', "VM verifier preflight wrapper contract checker requires short-form symbolic remote HEAD alias fail-before-planning coverage"),
    ('STALE_FIXTURE_DIR="$(mktemp -d -t unifai-vm-preflight-stale-XXXXXX)"', "VM verifier preflight wrapper contract checker requires stale-visible-ref fixture coverage"),
    ('git -C "$STALE_FIXTURE_DIR" remote add origin https://github.com/example/unifai.git', "VM verifier preflight wrapper contract checker requires stale-visible-ref fake GitHub remote coverage"),
    ('git -C "$STALE_FIXTURE_DIR" update-ref refs/remotes/origin/main "$(git -C "$STALE_FIXTURE_DIR" rev-parse HEAD)"', "VM verifier preflight wrapper contract checker requires stale-visible-ref remote-tracking seed coverage"),
    ('STALE_VISIBLE_SHA="$(git -C "$STALE_FIXTURE_DIR" rev-parse refs/remotes/origin/main)"', "VM verifier preflight wrapper contract checker requires stale-visible-ref SHA derivation coverage"),
    ('Expected stale visible SHA case to fail when the local branch is ahead of the published GitHub-visible head.', "VM verifier preflight wrapper contract checker requires stale-visible-ref fail-closed expectations"),
    ('Expected stale visible SHA failure message missing.', "VM verifier preflight wrapper contract checker requires stale-visible-ref failure message coverage"),
    ('Expected stale visible SHA recovery guidance missing.', "VM verifier preflight wrapper contract checker requires stale-visible-ref recovery guidance coverage"),
    ('Stale visible SHA case should fail before any preflight steps are planned.', "VM verifier preflight wrapper contract checker requires stale-visible-ref pre-planning fail-closed coverage"),
    ("points at remote 'origin', but that remote is not GitHub-backed", "VM verifier preflight wrapper contract checker requires non-GitHub remote-tracking failure coverage"),
    ('Expected short remote-tracking ref on a non-GitHub remote to fail.', "VM verifier preflight wrapper contract checker requires short non-GitHub remote-tracking fail-closed coverage"),
    ('Expected full remote-tracking ref on a non-GitHub remote to fail.', "VM verifier preflight wrapper contract checker requires full non-GitHub remote-tracking fail-closed coverage"),
    ('Expected branch case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires branch-path verifier handoff expectations"),
    ('Expected default no-arg case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires default-path verifier handoff expectations"),
    ('Expected explicit refs/heads case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires refs/heads verifier handoff expectations"),
    ('Expected -- separator case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires -- separator verifier handoff expectations"),
    ('no_github_remote_required = [', "VM verifier preflight wrapper contract checker keeps explicit no-GitHub-remote smoke requirements"),
    ('git init -q --bare "$REMOTE_REPO"', "VM verifier preflight wrapper contract checker requires a non-GitHub remote fixture in the no-GitHub-remote smoke test"),
    ('UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "origin/feature/no-github-remote"', "VM verifier preflight wrapper contract checker requires short remote-tracking ref non-GitHub smoke coverage"),
    ('UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "refs/remotes/origin/feature/no-github-remote"', "VM verifier preflight wrapper contract checker requires full remote-tracking ref non-GitHub smoke coverage"),
    ('git checkout -q --detach', "VM verifier preflight wrapper contract checker requires detached-HEAD coverage in the no-GitHub-remote smoke test"),
    ('Detached-HEAD case should fail before any preflight steps are planned.', "VM verifier preflight wrapper contract checker requires fail-before-planning detached-HEAD coverage"),
    ('for needle, message in smoke_required:', "VM verifier preflight wrapper contract checker validates wrapper smoke requirements"),
    ('for needle, message in no_github_remote_required:', "VM verifier preflight wrapper contract checker validates no-GitHub-remote smoke requirements"),
    ('for needle in forbidden_smoke_needles:', "VM verifier preflight wrapper contract checker keeps stale-ref guard coverage"),
    ("github/fix/openclaw-config-path-and-local-mode", "VM verifier preflight wrapper contract checker guards against hard-coded stale GitHub-visible refs"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] VM verifier preflight wrapper contract checker contract looks sane')
