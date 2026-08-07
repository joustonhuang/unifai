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
    ('python3 scripts/check_github_check_gate.py "$effective_ref"', "VM verifier preflight wrapper contract checker requires normalized check-gate coverage"),
    ('github_visible_ref_for_verifier() {', "VM verifier preflight wrapper contract checker requires GitHub-visible verifier-ref normalization coverage"),
    ('is_github_remote_head_alias() {', "VM verifier preflight wrapper contract checker requires symbolic GitHub remote HEAD alias detection coverage"),
    ('reject_symbolic_github_remote_head_ref() {', "VM verifier preflight wrapper contract checker requires symbolic GitHub remote HEAD alias rejection coverage"),
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
    ('python3 scripts/check_github_check_gate.py $VISIBLE_REMOTE_REF', "VM verifier preflight wrapper contract checker requires remote-tracking ref check-gate coverage"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $VISIBLE_VERIFIER_REF', "VM verifier preflight wrapper contract checker requires normalized remote-tracking verifier handoff coverage"),
    ('Expected symbolic remote HEAD alias case to fail fast.', "VM verifier preflight wrapper contract checker requires symbolic remote HEAD alias fail-closed coverage"),
    ('Expected symbolic remote HEAD alias recovery guidance missing.', "VM verifier preflight wrapper contract checker requires symbolic remote HEAD alias recovery guidance coverage"),
    ('Symbolic remote HEAD alias case should fail before the GitHub check-gate step.', "VM verifier preflight wrapper contract checker requires symbolic remote HEAD alias fail-before-planning coverage"),
    ('Expected branch case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires branch-path verifier handoff expectations"),
    ('Expected default no-arg case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires default-path verifier handoff expectations"),
    ('Expected explicit refs/heads case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires refs/heads verifier handoff expectations"),
    ('Expected -- separator case to hand off the GitHub-visible verifier ref.', "VM verifier preflight wrapper contract checker requires -- separator verifier handoff expectations"),
    ('no_github_remote_required = [', "VM verifier preflight wrapper contract checker keeps explicit no-GitHub-remote smoke requirements"),
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
