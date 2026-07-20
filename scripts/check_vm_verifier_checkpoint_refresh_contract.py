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
    ('def collect_bundle_paths(upstream: str, dirty_paths: list[str]) -> list[str]:', "Refresh helper centralizes bundle-path collection for both the initial and final dirty-tree snapshots"),
    ('def replace_delta_and_bundle_sections(', "Refresh helper centralizes checkpoint delta/bundle section rewrites across both dirty-tree passes"),
    ('def describe_dirty_state(', "Refresh helper centralizes dirty-tree status wording so docs and handoff output stay aligned"),
    ('def git_optional(*args: str) -> str | None:', "Refresh helper keeps the fail-closed optional git wrapper"),
    ('"refresh_vm_verifier_checkpoint_state.py requires a checked-out branch; detached HEAD does not provide a stable publish-boundary checkpoint."', "Refresh helper explains detached-HEAD checkpoint failures clearly"),
    ('has no upstream; set a GitHub-visible upstream before refreshing the verifier publish-boundary checkpoint.', "Refresh helper explains missing-upstream checkpoint failures clearly"),
    ('def current_host_lines() -> tuple[str, str]:', "Refresh helper keeps the host-readiness line builder"),
    ('except FileNotFoundError:', "Refresh helper treats missing host binaries as a false command result instead of crashing"),
    ('if Path("/dev/kvm").exists():', "Refresh helper still inspects /dev/kvm presence when building the host-readiness snapshot"),
    ('if access("/dev/kvm", W_OK):', "Refresh helper still distinguishes writable vs non-writable /dev/kvm state"),
    ('if command_succeeds("gh", "auth", "status"):', "Refresh helper still captures authenticated vs unauthenticated gh state"),
    ('if environ.get("GH_TOKEN") or environ.get("GITHUB_TOKEN")', "Refresh helper still reports GH_TOKEN/GITHUB_TOKEN export state"),
    ('current_head_short = git("rev-parse", "--short", "HEAD")', "Refresh helper captures the checked-out branch tip separately from the tracked publish head"),
    ('current_head_subject = git("show", "-s", "--format=%s", "HEAD")', "Refresh helper captures the checked-out branch-tip subject"),
    ('current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")', "Refresh helper captures the checked-out branch-tip ahead count separately from the tracked publish head"),
    ('if tracked_ref != "HEAD":', "Refresh helper distinguishes doc-only checkpoint commits sitting on top of the tracked publish head"),
    ('doc-only checkpoint refresh commits are intentionally excluded from that comparison', "Refresh helper explains why a checked-out doc-only tip can differ from the tracked publish head"),
    ('original_boundary_text = DOC_BOUNDARY.read_text(encoding="utf-8")', "Refresh helper snapshots the boundary doc before rewriting it"),
    ('original_checkpoint_text = DOC_CHECKPOINT.read_text(encoding="utf-8")', "Refresh helper snapshots the checkpoint doc before rewriting it"),
    ('git("status", "--short")', "Refresh helper still reads git status to capture dirty working-tree state"),
    ('doc_dirty_paths: list[str] = []', "Refresh helper tracks helper-generated doc edits separately from the initial dirty tree"),
    ('if original_text != updated_text and path not in dirty_paths:', "Refresh helper folds rewritten docs back into the final dirty-tree snapshot"),
    ('dirty_paths = [*dirty_paths, *doc_dirty_paths]', "Refresh helper updates the dirty-tree snapshot after helper-generated doc rewrites"),
    ('bundle_paths = collect_bundle_paths(upstream, dirty_paths)', "Refresh helper re-derives bundle paths from the final dirty-tree snapshot"),
    ('"python3 scripts/check_publish_stack_parity_contract.py\\n"', "Refresh helper keeps the publish-stack parity contract gate in the handoff artifact"),
    ('"python3 scripts/check_compare_publish_branch_histories_contract.py\\n"', "Refresh helper keeps the publish-branch-history contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\\n"', "Refresh helper keeps the checkpoint-freshness contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\\n"', "Refresh helper keeps its own contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_host_readiness_contract.py\\n"', "Refresh helper keeps the host-readiness contract gate in the handoff artifact"),
    ('"bash scripts/smoke_test_publish_stack_parity.sh\\n"', "Refresh helper keeps the publish-stack parity smoke gate in the handoff artifact"),
    ('"bash scripts/smoke_test_compare_publish_branch_histories.sh\\n"', "Refresh helper keeps the publish-branch-history smoke gate in the handoff artifact"),
    ('"python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\\n"', "Refresh helper keeps the checkpoint-freshness smoke gate in the handoff artifact"),
    ('"python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\\n"', "Refresh helper keeps the checkpoint-refresh smoke gate in the handoff artifact"),
    ('"bash scripts/bootstrap_installer_preflight.sh"', "Refresh helper keeps bootstrap preflight as the publish gate"),
    ('"Current host-readiness snapshot:\\n"', "Refresh helper writes the host-readiness snapshot into the handoff artifact"),
    ('f"Commit candidate: publish-boundary maintenance bundle for visible-ref handoff @ {tracked_head_short}\\n"', "Refresh helper labels the handoff artifact with the live checkpoint head"),
    ('f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{upstream_short}`', "Refresh helper keeps the public blocker note tied to the live GitHub-visible head"),
    ('next_move_heading = "Next clean move once the branch tip is GitHub-visible:\\n"', "Refresh helper keeps the branch-tip visible-ref handoff heading for doc-only tip cases"),
    ('next_move_heading = "Next clean move before the real VM-proof path:\\n"', "Refresh helper keeps the direct visible-ref handoff heading when the tracked checkpoint is the current tip"),
    ('f"- Make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream}`.\\n"', "Refresh helper targets the tracked upstream ref for direct visible-ref handoff"),
    ('f"- Make the current branch tip `{current_head_short}` GitHub-visible on `{upstream}`; "', "Refresh helper targets the tracked upstream ref for doc-only tip visible-ref handoff"),
    ('f"{commit_candidate_tip_line}"', "Refresh helper can surface the checked-out branch tip in the handoff artifact when it differs from the tracked publish head"),
    ('current_branch_state = f"ahead {current_head_ahead_count} over {upstream}"', "Refresh helper reports the live checked-out branch distance in the handoff artifact"),
    ('COMMIT_CANDIDATE.write_text(commit_candidate_text, encoding="utf-8")', "Refresh helper writes the commit-candidate handoff artifact"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint refresh contract looks sane")
