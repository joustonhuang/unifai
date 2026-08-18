#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_vm_verifier_checkpoint_freshness.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")
smoke_text = (REPO_ROOT / "scripts" / "smoke_test_vm_verifier_checkpoint_freshness.py").read_text(encoding="utf-8")

required = [
    ('DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"', "Freshness checker targets the boundary doc"),
    ('DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Freshness checker targets the checkpoint doc"),
    ('CHECKPOINT_LATEST = REPO_ROOT / "ci-artifacts" / "vm-verifier-checkpoint-latest.md"', "Freshness checker targets the stable latest-checkpoint handoff artifact"),
    ('COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"', "Freshness checker targets the handoff artifact"),
    ('SELF_MAINTAINED_HANDOFF_PATHS = {', "Freshness checker groups regenerated checkpoint artifacts into one self-maintained handoff set"),
    ('str(CHECKPOINT_LATEST.relative_to(REPO_ROOT))', "Freshness checker treats the latest-checkpoint artifact as self-maintained handoff state"),
    ('str(COMMIT_CANDIDATE.relative_to(REPO_ROOT))', "Freshness checker treats the commit-candidate artifact as self-maintained handoff state"),
    ('NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")', "Freshness checker treats docs and ci-artifacts handoff files as non-logic paths"),
    ('def is_non_logic_path(path: str) -> bool:', "Freshness checker centralizes non-logic path classification"),
    ('def is_checkpoint_doc_only_commit(ref: str) -> bool:', "Freshness checker distinguishes doc-only checkpoint commits"),
    ('tracked_ref = "HEAD"', "Freshness checker starts from the checked-out branch tip"),
    ('while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):', "Freshness checker skips doc-only checkpoint commits when finding the tracked publish head"),
    ('current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")', "Freshness checker captures the live checked-out branch ahead count"),
    ('visible_head_short = upstream_short', "Freshness checker derives the default visible head from the upstream tip"),
    ('if tracked_ref != "HEAD" and current_head_ahead_count == "0":', "Freshness checker can keep the visible head anchored to the tracked non-doc checkpoint after a visible doc-only tip"),
    ('latest_non_doc_paths = [', "Freshness checker captures the latest non-doc path list from the tracked publish head"),
    ('path for path in latest_non_doc_all_paths if not is_non_logic_path(path)', "Freshness checker ignores non-logic handoff paths when validating the latest non-doc path list"),
    ('def require_exact_line(text: str, needle: str, label: str) -> int:', "Freshness checker can require exact line matches when substring checks are too weak"),
    ('def require_exact_block(text: str, needle: str, label: str) -> int:', "Freshness checker can require exact block matches for multi-line handoff sections"),
    ('def require_unique_line_prefix(text: str, prefix: str, label: str) -> int:', "Freshness checker can fail closed when a supposedly unique handoff line appears multiple times"),
    ('def dirty_bundle_lines(dirty_paths: list[str]) -> tuple[str, str]:', "Freshness checker derives visibility-aware dirty-bundle summaries from the live worktree"),
    ('def current_delta_block(dirty_paths: list[str]) -> str:', "Freshness checker derives the expected checkpoint current-delta block from the live worktree"),
    ('_, checkpoint_dirty_line = dirty_bundle_lines(dirty_paths)', "Freshness checker computes the live checkpoint dirty-bundle summary line"),
    ('checkpoint_delta_block = current_delta_block(dirty_paths)', "Freshness checker computes the live checkpoint current-delta block"),
    ('working_tree_block = (', "Freshness checker derives the live handoff working-tree block from the effective dirty path set"),
    ('return [path for path in dirty_paths if path not in SELF_MAINTAINED_HANDOFF_PATHS]', "Freshness checker strips regenerated handoff artifacts out of doc-only dirty-state comparisons"),
    ('require_unique_line_prefix(', "Freshness checker requires the checkpoint current-delta line to stay unique"),
    ('"Checkpoint doc current-delta block"', "Freshness checker validates the checkpoint current-delta block exactly"),
    ('"Commit-candidate working-tree block"', "Freshness checker validates the handoff working-tree block exactly"),
    ('"Checkpoint doc dirty bundle summary"', "Freshness checker validates the checkpoint doc dirty-bundle summary"),
    ('for path in dirty_paths:', "Freshness checker validates every live dirty path in the checkpoint doc bundle section"),
    ('"Checkpoint doc dirty bundle paths"', "Freshness checker fail-closes when any live dirty bundle path is missing from the checkpoint doc"),
    ('checkpoint_latest_text = CHECKPOINT_LATEST.read_text(encoding="utf-8")', "Freshness checker reads the stable latest-checkpoint handoff artifact"),
    ('"- treat the published GitHub-visible ref as the VM-proof boundary and re-check the exact branch/commit state locally before any live verifier run"', "Freshness checker validates the boundary doc VM-proof boundary guidance"),
    ('"- the local sandbox may carry additional ahead-of-published commits and uncommitted publish-boundary maintenance delta, so confirm with `git status --short --branch` before assuming the current tip is publishable"', "Freshness checker validates the boundary doc dirty-state guidance"),
    ('"- that same wrapper now normalizes explicit GitHub remote-tracking refs down to a GitHub-visible branch name for the final `scripts/vm/verify_bootstrap_in_vm.sh` handoff, so the operator-facing next step stays runnable"', "Freshness checker validates the boundary doc verifier handoff guidance"),
    ('"Checkpoint doc visible head"', "Freshness checker validates the dated checkpoint doc GitHub-visible head"),
    ('"Checkpoint latest visible head"', "Freshness checker validates the stable latest-checkpoint GitHub-visible head"),
    ('"Checkpoint latest tracked head"', "Freshness checker validates the stable latest-checkpoint tracked head"),
    ('"Checkpoint latest ahead count"', "Freshness checker validates the stable latest-checkpoint ahead count"),
    ('if checkpoint_latest_text != checkpoint_text:', "Freshness checker fail-closes when the stable latest-checkpoint artifact diverges from the dated checkpoint doc"),
    ('"Checkpoint latest handoff artifact diverges from the dated checkpoint doc."', "Freshness checker emits a clear mismatch failure for latest-checkpoint drift"),
    ('f"Tracked publish-boundary state: ahead {ahead_count} over {upstream_display}\\n"', "Freshness checker validates the handoff branch-state line against HEAD"),
    ('f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\\n"', "Freshness checker validates the handoff checked-out tip line for doc-only cases"),
    ('if "the current checked-out branch tip is `" in boundary_text:', "Freshness checker rejects checked-out tip prose leaking back into the boundary doc"),
    ('if "- Current checked-out branch tip: `" in checkpoint_text:', "Freshness checker rejects checked-out tip lines leaking back into the checkpoint doc"),
    ('"boundary doc checked-out tip line should stay out of tracked docs to avoid doc-only self-refresh churn."', "Freshness checker fails closed when the boundary doc tries to track the checked-out tip"),
    ('"checkpoint doc checked-out tip line should stay out of tracked docs to avoid doc-only self-refresh churn."', "Freshness checker fails closed when the checkpoint doc tries to track the checked-out tip"),
    ('f"- The branch still needs the current branch tip `{current_head_short}` GitHub-visible; "', "Freshness checker validates the doc-only handoff blocker line against the checked-out tip"),
    ('push_command = f"git push {upstream_remote} HEAD:{upstream_branch}"', "Freshness checker derives the exact push command for visible-ref handoff validation"),
    ('f"- Run `{push_command}` to make the current branch tip `{current_head_short}` GitHub-visible on `{upstream_display}`; "', "Freshness checker validates the doc-only next-move line against the checked-out tip"),
    ('"boundary doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible."', "Freshness checker rejects checked-out tip prose leaking into tracked docs after the doc-only tip is already visible"),
    ('"checkpoint doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible."', "Freshness checker rejects checked-out tip lines leaking into tracked docs after the doc-only tip is already visible"),
    ('f"- The current checked-out doc-only tip is already GitHub-visible on `{upstream_display}`; "', "Freshness checker validates the aligned doc-only visible-ref blocker line"),
    ('f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{tracked_head_short}`.\\n"', "Freshness checker validates the aligned doc-only visible-ref next move"),
    ('"boundary doc checked-out tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed when the boundary doc keeps a checked-out tip line at HEAD"),
    ('"checkpoint doc checked-out tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed when the checkpoint doc keeps a checked-out tip line at HEAD"),
    ('"commit-candidate tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed on an unexpected tip line at HEAD"),
    ('f"- The branch still needs the local checkpoint chain through `{tracked_head_short}` "', "Freshness checker validates the direct-checkpoint blocker line when HEAD is the tracked publish head"),
    ('f"- Run `{push_command}` to make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream_display}`.\\n"', "Freshness checker validates the direct-checkpoint next-move line when HEAD is the tracked publish head"),
    ('f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on "',
     "Freshness checker validates the public blocker note against the live GitHub-visible head"),
    ('"[PASS] VM verifier checkpoint artifacts match current repo state"', "Freshness checker emits a passing verdict"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint freshness contract looks sane")

smoke_required = [
    ('run(["git", "push", "origin", "HEAD:fix/openclaw-config-path-and-local-mode"], work)', "Freshness smoke test exercises the already-visible doc-only tip handoff"),
    ('latest_checkpoint = work / "ci-artifacts" / "vm-verifier-checkpoint-latest.md"', "Freshness smoke test edits the stable latest-checkpoint handoff artifact explicitly"),
    ('assert "Checkpoint doc current-delta block is stale; expected exactly one line starting with:" in stale_checkpoint_duplicate_delta_output', "Freshness smoke test fails closed when the checkpoint doc carries contradictory current-delta lines"),
    ('assert "Commit-candidate working-tree block is stale; expected exact block:" in stale_commit_candidate_worktree_output', "Freshness smoke test fails closed when the handoff working-tree block drifts"),
    ('assert "Checkpoint latest handoff artifact diverges from the dated checkpoint doc." in stale_latest_checkpoint_output', "Freshness smoke test fails closed when the stable latest-checkpoint handoff artifact drifts"),
    ('assert "Checkpoint doc visible head is stale; expected to find:" in stale_visible_head_output', "Freshness smoke test fails closed when the dated checkpoint doc records the wrong GitHub-visible head"),
    ('assert "Checkpoint latest visible head is stale; expected to find:" in stale_latest_visible_head_output', "Freshness smoke test fails closed when the stable latest-checkpoint artifact records the wrong GitHub-visible head"),
    ('assert "boundary doc checked-out tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_boundary_tip_output', "Freshness smoke test fails closed when the HEAD boundary doc tracks the checked-out tip"),
    ('assert "checkpoint doc checked-out tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_checkpoint_tip_output', "Freshness smoke test fails closed when the HEAD checkpoint doc tracks the checked-out tip"),
    ('assert "[PASS] VM verifier checkpoint artifacts match current repo state" in aligned_fresh_output', "Freshness smoke test requires the aligned visible-ref case to pass cleanly"),
    ('boundary_text + f"\\n- the current checked-out branch tip is `{current_head_short}` (`{current_head_subject}`)\\n"', "Freshness smoke test injects a checked-out tip leak into the aligned boundary doc"),
    ('assert "boundary doc checked-out tip line should stay out of tracked docs after a clean doc-only tip becomes visible." in aligned_boundary_tip_output', "Freshness smoke test fails closed when the aligned boundary doc tracks the checked-out tip"),
    ('checkpoint_text + f"\\n- Current checked-out branch tip: `{current_head_short}` (`{current_head_subject}`)\\n"', "Freshness smoke test injects a checked-out tip leak into the aligned checkpoint doc"),
    ('assert "checkpoint doc checked-out tip line should stay out of tracked docs after a clean doc-only tip becomes visible." in aligned_checkpoint_tip_output', "Freshness smoke test fails closed when the aligned checkpoint doc tracks the checked-out tip"),
    ('commit_candidate_text.replace(', "Freshness smoke test mutates the aligned handoff artifact fail-closed"),
    ('"Tracked publish-boundary state: ahead 0 over fix/openclaw-config-path-and-local-mode\\n",', "Freshness smoke test covers stale aligned visible-ref branch-state wording"),
    ('assert "Commit-candidate branch state is stale; expected to find:" in aligned_doc_only_branch_state_output', "Freshness smoke test fails closed on stale aligned visible-ref branch-state text"),
    ('"- The current checked-out doc-only tip is already GitHub-visible",', "Freshness smoke test covers stale aligned visible-ref blocker wording"),
    ('"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `",', "Freshness smoke test covers stale aligned visible-ref next-move wording"),
    ('assert "Commit-candidate external blocker is stale; expected to find:" in aligned_doc_only_blocker_output', "Freshness smoke test fails closed on stale aligned visible-ref blocker text"),
    ('assert "Commit-candidate next move is stale; expected to find:" in aligned_doc_only_move_output', "Freshness smoke test fails closed on stale aligned visible-ref next-move text"),
    ('run(["git", "remote", "rename", "origin", "github"], work)', "Freshness smoke test renames the upstream remote to exercise dynamic push-command generation"),
    ('"--set-upstream-to=github/fix/openclaw-config-path-and-local-mode"', "Freshness smoke test points the branch at the renamed GitHub remote"),
    ('f"- Run `git push github HEAD:fix/openclaw-config-path-and-local-mode` to make the current checked-out tip GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "', "Freshness smoke test pins the stable unpublished doc-only next move against the renamed GitHub remote"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint freshness smoke contract looks sane")
