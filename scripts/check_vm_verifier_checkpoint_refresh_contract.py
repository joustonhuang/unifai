#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "refresh_vm_verifier_checkpoint_state.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"', "Refresh helper targets the boundary doc"),
    ('DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Refresh helper targets the checkpoint doc"),
    ('COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"', "Refresh helper targets the commit-candidate handoff artifact"),
    ('def git_optional(*args: str) -> str | None:', "Refresh helper keeps the fail-closed optional git wrapper"),
    ('"refresh_vm_verifier_checkpoint_state.py requires a checked-out branch; detached HEAD does not provide a stable publish-boundary checkpoint."', "Refresh helper explains detached-HEAD checkpoint failures clearly"),
    ('has no upstream; set a GitHub-visible upstream before refreshing the verifier publish-boundary checkpoint.', "Refresh helper explains missing-upstream checkpoint failures clearly"),
    ('def current_host_lines() -> tuple[str, str]:', "Refresh helper keeps the host-readiness line builder"),
    ('except FileNotFoundError:', "Refresh helper treats missing host binaries as a false command result instead of crashing"),
    ('if Path("/dev/kvm").exists():', "Refresh helper still inspects /dev/kvm presence when building the host-readiness snapshot"),
    ('if access("/dev/kvm", W_OK):', "Refresh helper still distinguishes writable vs non-writable /dev/kvm state"),
    ('if command_succeeds("gh", "auth", "status"):', "Refresh helper still captures authenticated vs unauthenticated gh state"),
    ('if environ.get("GH_TOKEN") or environ.get("GITHUB_TOKEN")', "Refresh helper still reports GH_TOKEN/GITHUB_TOKEN export state"),
    ('git("status", "--short")', "Refresh helper still reads git status to capture dirty working-tree state"),
    ('git("diff", "--name-only", upstream)', "Refresh helper still derives bundle paths from the upstream diff"),
    ('"python3 scripts/check_publish_stack_parity_contract.py\\n"', "Refresh helper keeps the publish-stack parity contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_host_readiness_contract.py\\n"', "Refresh helper keeps the host-readiness contract gate in the handoff artifact"),
    ('"python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\\n"', "Refresh helper keeps the checkpoint-refresh smoke gate in the handoff artifact"),
    ('"bash scripts/bootstrap_installer_preflight.sh"', "Refresh helper keeps bootstrap preflight as the publish gate"),
    ('"Current host-readiness snapshot:\\n"', "Refresh helper writes the host-readiness snapshot into the handoff artifact"),
    ('f"Commit candidate: checkpoint-refresh helper/doc sync for publish-boundary state @ {tracked_head_short}\\n"', "Refresh helper labels the handoff artifact with the live checkpoint head"),
    ('f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{upstream_short}`', "Refresh helper keeps the public blocker note tied to the live GitHub-visible head"),
    ('"Next clean move once the branch tip is GitHub-visible:\\n"', "Refresh helper keeps the visible-ref handoff section"),
    ('COMMIT_CANDIDATE.write_text(commit_candidate_text, encoding="utf-8")', "Refresh helper writes the commit-candidate handoff artifact"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint refresh contract looks sane")
