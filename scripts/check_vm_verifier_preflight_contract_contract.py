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
    ('current_branch="$ref"', "VM verifier preflight wrapper contract checker requires detached-HEAD explicit-ref reuse coverage"),
    ('smoke_required = [', "VM verifier preflight wrapper contract checker keeps explicit wrapper smoke requirements"),
    ('DETACHED_WORKTREE_DIR="$(mktemp -d -t unifai-vm-preflight-detached-XXXXXX)"', "VM verifier preflight wrapper contract checker requires detached-worktree smoke coverage"),
    ('git -C "$REPO_ROOT" worktree add --detach "$DETACHED_WORKTREE_DIR" HEAD >/dev/null', "VM verifier preflight wrapper contract checker requires a real detached-HEAD worktree setup"),
    ('DETACHED_VISIBLE_SHA_OUTPUT="$(', "VM verifier preflight wrapper contract checker requires detached-HEAD explicit-SHA smoke output capture"),
    ('Expected detached-HEAD visible-SHA case to skip branch visibility.', "VM verifier preflight wrapper contract checker requires detached-HEAD branch-visibility skip coverage"),
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
