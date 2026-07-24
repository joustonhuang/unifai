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
    ('git show-ref --verify --quiet "refs/heads/$ref"', "Wrapper distinguishes local branch names from explicit refs/SHAs"),
    ('bash scripts/check_github_branch_visibility.sh "$ref"', "Wrapper checks GitHub branch visibility for local branches"),
    ("skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA.", "Wrapper explains why branch visibility is skipped for explicit refs/SHAs"),
    ('python3 scripts/check_github_check_gate.py "$ref"', "Wrapper runs GitHub check gate inspection on the chosen ref"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $ref', "Wrapper points to the VM verifier as the next step"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

smoke_required = [
    ('detect_github_remote()', "Wrapper smoke test derives the GitHub-backed remote dynamically"),
    ('GITHUB_REMOTE="$(detect_github_remote)"', "Wrapper smoke test resolves the GitHub-backed remote before building a visible SHA"),
    ('resolve_visible_remote_ref() {', "Wrapper smoke test provides a helper to pick a GitHub-visible remote ref"),
    ('VISIBLE_REMOTE_REF="$(resolve_visible_remote_ref "$GITHUB_REMOTE")"', "Wrapper smoke test resolves an explicit GitHub-visible remote-tracking ref"),
    ('VISIBLE_SHA="$(git -C "$REPO_ROOT" rev-parse "$VISIBLE_REMOTE_REF")"', "Wrapper smoke test derives the visible SHA from the resolved remote-tracking ref"),
    ('DEFAULT_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER")"', "Wrapper smoke test exercises the no-argument default-branch path"),
    ('Expected current branch to be used when no ref is provided.', "Wrapper smoke test explains the default-branch expectation"),
    ('Expected branch visibility command missing in default no-arg case.', "Wrapper smoke test checks branch visibility in the default no-arg case"),
    ('Expected check-gate command missing in default no-arg case.', "Wrapper smoke test checks the check-gate step in the default no-arg case"),
    ('"$WRAPPER" "$VISIBLE_REMOTE_REF"', "Wrapper smoke test exercises the wrapper with an explicit remote-tracking ref"),
    ('python3 scripts/check_github_check_gate.py $VISIBLE_REMOTE_REF', "Wrapper smoke test keeps the explicit remote-tracking ref intact for the check-gate step"),
    ('"$WRAPPER" -- "$BRANCH"', "Wrapper smoke test exercises the -- separator path"),
    ('Expected branch ref missing when passed after --.', "Wrapper smoke test explains the -- separator branch-ref expectation"),
    ('Expected branch visibility command missing when ref is passed after --.', "Wrapper smoke test checks branch visibility when ref is passed after --"),
    ('Expected check-gate command missing when ref is passed after --.', "Wrapper smoke test checks the check-gate step when ref is passed after --"),
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
    ('scripts/check_vm_host_readiness.sh', "No-GitHub-remote smoke test guards that failure happens before host-readiness planning appears"),
    ('Expected explicit local SHA case to fail when no GitHub remote exists.', "No-GitHub-remote smoke test explains the explicit-SHA fail-closed expectation"),
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
