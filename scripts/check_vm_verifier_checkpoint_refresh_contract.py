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
smoke_text = (REPO_ROOT / "scripts" / "smoke_test_vm_verifier_checkpoint_refresh.py").read_text(encoding="utf-8")

required = [
    ('DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"', "Refresh helper targets the boundary doc"),
    ('DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Refresh helper targets the checkpoint doc"),
    ('CHECKPOINT_LATEST = REPO_ROOT / "ci-artifacts" / "vm-verifier-checkpoint-latest.md"', "Refresh helper targets the stable latest-checkpoint handoff artifact"),
    ('COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"', "Refresh helper targets the commit-candidate handoff artifact"),
    ('NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")', "Refresh helper treats docs and ci-artifacts handoff files as non-logic paths"),
    ('def is_non_logic_path(path: str) -> bool:', "Refresh helper centralizes non-logic path classification"),
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
    ('while normal GitHub API reads should flow through authenticated `gh` unless the host state changes', "Refresh helper narrows the host-readiness warning when gh auth already covers normal API reads"),
    ('while GitHub API access should rely on token-backed curl fallback unless the host state changes', "Refresh helper can still describe the token-backed curl fallback case"),
    ('current_head_short = git("rev-parse", "--short", "HEAD")', "Refresh helper captures the checked-out branch tip separately from the tracked publish head"),
    ('current_head_subject = git("show", "-s", "--format=%s", "HEAD")', "Refresh helper captures the checked-out branch-tip subject"),
    ('current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")', "Refresh helper captures the checked-out branch-tip ahead count separately from the tracked publish head"),
    ('if tracked_ref != "HEAD":', "Refresh helper distinguishes doc-only checkpoint commits sitting on top of the tracked publish head"),
    ('doc-only checkpoint refresh commits are intentionally excluded from that comparison', "Refresh helper explains why a checked-out doc-only tip can differ from the tracked publish head"),
    ('The live checked-out', "Refresh helper documents why checked-out tip state belongs only in the handoff artifact"),
    ('boundary_text = re.sub(', "Refresh helper rewrites tracked docs through explicit regex replacements"),
    ('r"- the current checked-out branch tip is `[^`]+` \\(`[^`]+`\\), but the tracked publish-boundary head stays `[^`]+` because doc-only checkpoint refresh commits are intentionally excluded from that comparison\\n?",', "Refresh helper strips checked-out tip prose back out of the boundary doc"),
    ('r"- Current checked-out branch tip: `[^`]+`(?: \\(`[^`]+`\\))?(?:; tracked publish-boundary head stays `[^`]+` because doc-only checkpoint refresh commits are intentionally excluded from that comparison\\.)?\\n?",', "Refresh helper strips checked-out tip lines back out of the checkpoint doc"),
    ('next((sha for sha, _subject in reversed(commits) if not is_checkpoint_doc_only_commit(sha)), tracked_head_short)', "Refresh helper derives the latest non-doc logic head from changed paths instead of commit-subject prefixes"),
    ('latest_non_doc_all_paths = [', "Refresh helper records the full path list for the latest non-doc commit before narrowing it"),
    ('path for path in latest_non_doc_all_paths if not is_non_logic_path(path)', "Refresh helper drops non-logic handoff paths from the non-doc delta file list when mixed commits touch both docs and scripts"),
    ('] or latest_non_doc_all_paths', "Refresh helper falls back to the full path list if filtering would leave the non-doc delta section empty"),
    ('original_boundary_text = DOC_BOUNDARY.read_text(encoding="utf-8")', "Refresh helper snapshots the boundary doc before rewriting it"),
    ('original_checkpoint_text = DOC_CHECKPOINT.read_text(encoding="utf-8")', "Refresh helper snapshots the checkpoint doc before rewriting it"),
    ('git("status", "--short")', "Refresh helper still reads git status to capture dirty working-tree state"),
    ('bundle_paths = collect_bundle_paths(upstream, dirty_paths)', "Refresh helper derives bundle paths from the real worktree dirty snapshot"),
    ('CHECKPOINT_LATEST.write_text(checkpoint_text, encoding="utf-8")', "Refresh helper refreshes the stable latest-checkpoint handoff artifact alongside the dated checkpoint doc"),
    ('"python3 scripts/check_publish_stack_parity_contract.py\\n"', "Refresh helper keeps the publish-stack parity contract gate in the handoff artifact"),
    ('"python3 scripts/check_publish_stack_reconciliation_note.py\\n"', "Refresh helper keeps the publish-stack reconciliation note freshness gate in the handoff artifact"),
    ('"python3 scripts/check_publish_stack_reconciliation_note_contract.py\\n"', "Refresh helper keeps the publish-stack reconciliation note contract gate in the handoff artifact"),
    ('"python3 scripts/check_compare_publish_branch_histories_contract.py\\n"', "Refresh helper keeps the publish-branch-history contract gate in the handoff artifact"),
    ('"python3 scripts/check_branch_reconcile_handoff.py\\n"', "Refresh helper keeps the branch-reconcile handoff freshness gate in the handoff artifact"),
    ('"python3 scripts/check_branch_reconcile_handoff_contract.py\\n"', "Refresh helper keeps the branch-reconcile handoff contract gate in the handoff artifact"),
    ('"  - `python3 scripts/check_github_branch_visibility_contract.py`\\n"', "Refresh helper keeps the branch-visibility contract gate in the generated checkpoint verification block"),
    ('"python3 scripts/check_github_branch_visibility_contract.py\\n"', "Refresh helper keeps the branch-visibility contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\\n"', "Refresh helper keeps the checkpoint-freshness contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\\n"', "Refresh helper keeps its own contract gate in the handoff artifact"),
    ('"python3 scripts/check_vm_host_readiness_contract.py\\n"', "Refresh helper keeps the host-readiness contract gate in the handoff artifact"),
    ('"bash scripts/smoke_test_publish_stack_parity.sh\\n"', "Refresh helper keeps the publish-stack parity smoke gate in the handoff artifact"),
    ('"bash scripts/smoke_test_compare_publish_branch_histories.sh\\n"', "Refresh helper keeps the publish-branch-history smoke gate in the handoff artifact"),
    ('"bash scripts/smoke_test_publish_stack_reconciliation_note.sh\\n"', "Refresh helper keeps the publish-stack reconciliation note smoke gate in the handoff artifact"),
    ('"bash scripts/smoke_test_branch_reconcile_handoff.sh\\n"', "Refresh helper keeps the branch-reconcile handoff smoke gate in the handoff artifact"),
    ('"python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\\n"', "Refresh helper keeps the checkpoint-freshness smoke gate in the handoff artifact"),
    ('"python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\\n"', "Refresh helper keeps the checkpoint-refresh smoke gate in the handoff artifact"),
    ('"bash scripts/bootstrap_installer_preflight.sh"', "Refresh helper keeps bootstrap preflight as the publish gate"),
    ('"Current host-readiness snapshot:\\n"', "Refresh helper writes the host-readiness snapshot into the handoff artifact"),
    ('f"Commit candidate: publish-boundary maintenance bundle for visible-ref handoff @ {tracked_head_short}\\n"', "Refresh helper labels the handoff artifact with the live checkpoint head"),
    ('f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{upstream_short}`', "Refresh helper keeps the public blocker note tied to the live GitHub-visible head"),
    ('next_move_heading = "Next clean move once the branch tip is GitHub-visible:\\n"', "Refresh helper keeps the branch-tip visible-ref handoff heading for doc-only tip cases"),
    ('next_move_heading = "Next clean move before the real VM-proof path:\\n"', "Refresh helper keeps the direct visible-ref handoff heading when the tracked checkpoint is the current tip"),
    ('push_command = f"git push {upstream_remote} HEAD:{upstream_branch}"', "Refresh helper derives the exact push command for the visible-ref handoff"),
    ('f"- Run `{push_command}` to make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream_display}`.\\n"', "Refresh helper targets the tracked upstream ref for direct visible-ref handoff"),
    ('f"- Run `{push_command}` to make the current branch tip `{current_head_short}` GitHub-visible on `{upstream_display}`; "', "Refresh helper targets the tracked upstream ref for doc-only tip visible-ref handoff"),
    ('f"- The exact branch tip `{current_head_short}` is already GitHub-visible on `{upstream_display}`; "', "Refresh helper reports when a doc-only checked-out tip is already GitHub-visible"),
    ('f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{tracked_head_short}`.\\n"', "Refresh helper points the aligned doc-only visible-ref case back at the visible preflight rerun"),
    ('f"{commit_candidate_tip_line}"', "Refresh helper can surface the checked-out branch tip in the handoff artifact when it differs from the tracked publish head"),
    ('tracked_branch_state = f"ahead {ahead_count} over {upstream_display}"', "Refresh helper reports the tracked publish-boundary distance in the handoff artifact"),
    ('COMMIT_CANDIDATE.write_text(commit_candidate_text, encoding="utf-8")', "Refresh helper writes the commit-candidate handoff artifact"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint refresh contract looks sane")

smoke_required = [
    ('assert f"Current checked-out branch tip: {head_sha} (docs: refresh branch reconcile publish handoff)\\n" in commit_candidate', "Refresh smoke test pins the initial doc-only checked-out tip line"),
    ('assert "Current checked-out branch tip:" not in stable_commit_candidate', "Refresh smoke test forbids a checked-out tip line when the tracked checkpoint is HEAD"),
    ('run(["git", "commit", "-m", "docs: settle verifier checkpoint handoff"], work)', "Refresh smoke test exercises a second unpublished doc-only checkpoint commit"),
    ('assert "Checked-out tip delta beyond tracked checkpoint: 2 doc-only commits\\n" in second_doc_only_commit_candidate', "Refresh smoke test pins the handoff tip-delta count after two unpublished doc-only checkpoint commits"),
    ('f"- The branch still needs the current branch tip `{second_doc_only_tip}` GitHub-visible; "', "Refresh smoke test pins the blocker wording for the second unpublished doc-only checkpoint tip"),
    ('run(["git", "push", "origin", "HEAD:fix/openclaw-config-path-and-local-mode"], work)', "Refresh smoke test exercises the already-visible doc-only tip handoff"),
    ('assert "Tracked publish-boundary state: ahead 0 over fix/openclaw-config-path-and-local-mode\\n" in aligned_commit_candidate', "Refresh smoke test pins the aligned visible-ref tracked-state line"),
    ('assert "Working-tree files:\\n(clean)\\n" in aligned_commit_candidate', "Refresh smoke test pins the aligned visible-ref clean handoff shape"),
    ('f"- The exact branch tip `{second_doc_only_tip}` is already GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "', "Refresh smoke test pins the aligned visible-ref blocker wording"),
    ('f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{stable_head}`.\\n"', "Refresh smoke test pins the aligned visible-ref next move"),
    ('assert "Next clean move before the real VM-proof path:\\n" in aligned_commit_candidate', "Refresh smoke test keeps the aligned case on the visible-ref rerun path"),
    ('run(["git", "remote", "rename", "origin", "github"], work)', "Refresh smoke test renames the upstream remote to exercise dynamic push-command generation"),
    ('"--set-upstream-to=github/fix/openclaw-config-path-and-local-mode"', "Refresh smoke test points the branch at the renamed GitHub remote"),
    ('f"- Run `git push github HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{github_remote_tip}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "', "Refresh smoke test pins the unpublished doc-only next move against the renamed GitHub remote"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint refresh smoke contract looks sane")
