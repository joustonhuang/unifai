#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_github_branch_visibility.sh"
SMOKE = REPO_ROOT / "scripts" / "smoke_test_github_branch_visibility.sh"
NO_REMOTE_SMOKE = REPO_ROOT / "scripts" / "smoke_test_github_branch_visibility_no_github_remote.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")
smoke_text = SMOKE.read_text(encoding="utf-8")
no_remote_smoke_text = NO_REMOTE_SMOKE.read_text(encoding="utf-8")

required = [
    ('Usage: bash scripts/check_github_branch_visibility.sh [branch]', "Branch-visibility helper documents its usage"),
    ('GITHUB_REMOTE   Remote name to force; otherwise auto-detected from upstream/origin', "Branch-visibility helper documents the GITHUB_REMOTE override"),
    ('detect_github_remote() {', "Branch-visibility helper defines GitHub-remote autodetection"),
    ('local_branch_name() {', "Branch-visibility helper centralizes refs/heads normalization for local branch refs"),
    ('printf \'%s\\n\' "${ref#refs/heads/}"', "Branch-visibility helper strips the refs/heads/ prefix before branch handling"),
    ('candidate="${candidate%%/*}"', "Branch-visibility helper derives the upstream remote name before validating it"),
    ('for candidate in origin github; do', "Branch-visibility helper tries common remote names before the full scan"),
    ("git remote -v | awk '$3 == \"(fetch)\" {print $1 \"\\t\" $2}'", "Branch-visibility helper scans fetch remotes for GitHub-backed URLs"),
    ('Could not auto-detect a GitHub-backed remote.', "Branch-visibility helper fails clearly when no GitHub remote exists"),
    ('Set GITHUB_REMOTE=<remote> or add a GitHub remote such as origin.', "Branch-visibility helper explains how to recover when no GitHub remote exists"),
    ('Remote \'$GITHUB_REMOTE\' is not configured.', "Branch-visibility helper fails clearly when the forced remote is missing"),
    ('Add it with: git remote add $GITHUB_REMOTE https://github.com/<owner>/<repo>.git', "Branch-visibility helper explains how to recover when the forced remote is missing"),
    ('Remote \'$GITHUB_REMOTE\' is not GitHub-backed: $remote_url', "Branch-visibility helper rejects non-GitHub remotes"),
    ('Local branch \'$branch\' does not exist.', "Branch-visibility helper rejects nonexistent local branches"),
    ('Remote branch \'$github_branch\' does not exist yet.', "Branch-visibility helper fails clearly when the GitHub-visible branch is missing"),
    ('Push the tracked upstream ref first if this work is meant to be public signal.', "Branch-visibility helper distinguishes tracked-upstream push guidance"),
    ('Push the branch first if this work is meant to be public signal.', "Branch-visibility helper distinguishes untracked-branch push guidance"),
    ('Branch is not tracking the GitHub-visible upstream \'$github_branch\'.', "Branch-visibility helper fails clearly when tracking is wrong"),
    ('Fix with: git branch --set-upstream-to=$github_branch $branch', "Branch-visibility helper explains how to repair upstream tracking"),
    ('Local branch and GitHub branch differ (ahead $ahead, behind $behind).', "Branch-visibility helper reports ahead/behind divergence"),
    ('git push $GITHUB_REMOTE HEAD:${github_branch#"$GITHUB_REMOTE/"}', "Branch-visibility helper gives targeted push guidance for ahead-only divergence"),
    ('Local branch is behind the GitHub-visible head; fast-forward or rebase before verifier work.', "Branch-visibility helper explains behind-only divergence"),
    ('Local and GitHub-visible history diverged; reconcile before verifier work.', "Branch-visibility helper explains symmetric divergence"),
    ('git log --oneline --left-right --cherry-pick $branch...$github_branch', "Branch-visibility helper points to the review diff for divergence"),
    ('[PASS] Local branch matches the GitHub-visible branch head.', "Branch-visibility helper explicitly reports the aligned case"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

smoke_required = [
    ('git branch --set-upstream-to=github/fix/test-visibility transplant/test-visibility >/dev/null', "Branch-visibility smoke test pins a tracked GitHub-visible upstream"),
    ('"$HELPER" "refs/heads/transplant/test-visibility"', "Branch-visibility smoke test exercises the helper with an explicit refs/heads local branch ref"),
    ('Expected helper to normalize explicit refs/heads local branch refs.', "Branch-visibility smoke test explains the explicit refs/heads branch-ref expectation"),
    ('Expected explicit refs/heads local branch ref to stay on the visible-branch path.', "Branch-visibility smoke test keeps explicit refs/heads inputs on the branch-visibility path"),
    ('Expected helper to print the tracked GitHub branch when it differs from the local branch name.', "Branch-visibility smoke test explains the remote-tracking branch expectation"),
    ('Expected ahead-only push guidance to target the tracked GitHub branch after local divergence.', "Branch-visibility smoke test guards targeted push guidance"),
    ('Expected review guidance to reference the tracked GitHub branch after local divergence.', "Branch-visibility smoke test guards tracked-branch review guidance"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

no_remote_required = [
    ('Expected branch-visibility helper to fail when no GitHub remote exists.', "No-remote smoke test explains the fail-closed expectation"),
    ('Could not auto-detect a GitHub-backed remote.', "No-remote smoke test expects the missing-remote failure message"),
    ('Set GITHUB_REMOTE=<remote> or add a GitHub remote such as origin.', "No-remote smoke test expects actionable recovery guidance"),
    ('GitHub branch:', "No-remote smoke test guards that failure happens before any GitHub branch state is reported"),
]

for needle, message in no_remote_required:
    if needle not in no_remote_smoke_text:
        fail(message)
    ok(message)

print('[PASS] GitHub branch-visibility contract looks sane')
