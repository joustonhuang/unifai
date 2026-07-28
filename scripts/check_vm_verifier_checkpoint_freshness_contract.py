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
    ('COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"', "Freshness checker targets the handoff artifact"),
    ('NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")', "Freshness checker treats docs and ci-artifacts handoff files as non-logic paths"),
    ('def is_non_logic_path(path: str) -> bool:', "Freshness checker centralizes non-logic path classification"),
    ('def is_checkpoint_doc_only_commit(ref: str) -> bool:', "Freshness checker distinguishes doc-only checkpoint commits"),
    ('tracked_ref = "HEAD"', "Freshness checker starts from the checked-out branch tip"),
    ('while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):', "Freshness checker skips doc-only checkpoint commits when finding the tracked publish head"),
    ('current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")', "Freshness checker captures the live checked-out branch ahead count"),
    ('latest_non_doc_paths = [', "Freshness checker captures the latest non-doc path list from the tracked publish head"),
    ('path for path in latest_non_doc_all_paths if not is_non_logic_path(path)', "Freshness checker ignores non-logic handoff paths when validating the latest non-doc path list"),
    ('f"- the latest non-doc logic delta in that local stack is `{tracked_head_short}` (`{tracked_head_subject}`) in:"', "Freshness checker validates the boundary doc latest non-doc heading"),
    ('for path in latest_non_doc_paths:', "Freshness checker validates every latest non-doc path bullet in the boundary doc"),
    ('f"  - `{path}`"', "Freshness checker checks the exact latest non-doc path bullets"),
    ('f"Current branch state: ahead {current_head_ahead_count} over {upstream_display}\\n"', "Freshness checker validates the handoff branch-state line against HEAD"),
    ('f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\\n"', "Freshness checker validates the handoff checked-out tip line for doc-only cases"),
    ('if "the current checked-out branch tip is `" in boundary_text:', "Freshness checker rejects checked-out tip prose leaking back into the boundary doc"),
    ('if "- Current checked-out branch tip: `" in checkpoint_text:', "Freshness checker rejects checked-out tip lines leaking back into the checkpoint doc"),
    ('"boundary doc checked-out tip line should stay out of tracked docs to avoid doc-only self-refresh churn."', "Freshness checker fails closed when the boundary doc tries to track the checked-out tip"),
    ('"checkpoint doc checked-out tip line should stay out of tracked docs to avoid doc-only self-refresh churn."', "Freshness checker fails closed when the checkpoint doc tries to track the checked-out tip"),
    ('f"- The branch still needs the current branch tip `{current_head_short}` GitHub-visible; "', "Freshness checker validates the doc-only handoff blocker line against the checked-out tip"),
    ('f"- Make the current branch tip `{current_head_short}` GitHub-visible on `{upstream_display}`; "', "Freshness checker validates the doc-only next-move line against the checked-out tip"),
    ('"boundary doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible."', "Freshness checker rejects checked-out tip prose leaking into tracked docs after the doc-only tip is already visible"),
    ('"checkpoint doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible."', "Freshness checker rejects checked-out tip lines leaking into tracked docs after the doc-only tip is already visible"),
    ('f"- The exact branch tip `{current_head_short}` is already GitHub-visible on `{upstream_display}`; "', "Freshness checker validates the aligned doc-only visible-ref blocker line"),
    ('f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{tracked_head_short}`.\\n"', "Freshness checker validates the aligned doc-only visible-ref next move"),
    ('"boundary doc checked-out tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed when the boundary doc keeps a checked-out tip line at HEAD"),
    ('"checkpoint doc checked-out tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed when the checkpoint doc keeps a checked-out tip line at HEAD"),
    ('"commit-candidate tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed on an unexpected tip line at HEAD"),
    ('f"- The branch still needs the local checkpoint chain through `{tracked_head_short}` "', "Freshness checker validates the direct-checkpoint blocker line when HEAD is the tracked publish head"),
    ('f"- Make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream_display}`.\\n"', "Freshness checker validates the direct-checkpoint next-move line when HEAD is the tracked publish head"),
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
    ('assert "boundary doc checked-out tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_boundary_tip_output', "Freshness smoke test fails closed when the HEAD boundary doc tracks the checked-out tip"),
    ('assert "checkpoint doc checked-out tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_checkpoint_tip_output', "Freshness smoke test fails closed when the HEAD checkpoint doc tracks the checked-out tip"),
    ('assert "[PASS] VM verifier checkpoint artifacts match current repo state" in aligned_fresh_output', "Freshness smoke test requires the aligned visible-ref case to pass cleanly"),
    ('boundary_text + f"\\n- the current checked-out branch tip is `{current_head_short}` (`{current_head_subject}`)\\n"', "Freshness smoke test injects a checked-out tip leak into the aligned boundary doc"),
    ('assert "boundary doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible." in aligned_boundary_tip_output', "Freshness smoke test fails closed when the aligned boundary doc tracks the checked-out tip"),
    ('checkpoint_text + f"\\n- Current checked-out branch tip: `{current_head_short}` (`{current_head_subject}`)\\n"', "Freshness smoke test injects a checked-out tip leak into the aligned checkpoint doc"),
    ('assert "checkpoint doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible." in aligned_checkpoint_tip_output', "Freshness smoke test fails closed when the aligned checkpoint doc tracks the checked-out tip"),
    ('commit_candidate_text.replace(', "Freshness smoke test mutates the aligned handoff artifact fail-closed"),
    ('"Current branch state: ahead 0 over fix/openclaw-config-path-and-local-mode\\n",', "Freshness smoke test covers stale aligned visible-ref branch-state wording"),
    ('assert "Commit-candidate branch state is stale; expected to find:" in aligned_doc_only_branch_state_output', "Freshness smoke test fails closed on stale aligned visible-ref branch-state text"),
    ('"- The exact branch tip `",', "Freshness smoke test covers stale aligned visible-ref blocker wording"),
    ('"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `",', "Freshness smoke test covers stale aligned visible-ref next-move wording"),
    ('assert "Commit-candidate external blocker is stale; expected to find:" in aligned_doc_only_blocker_output', "Freshness smoke test fails closed on stale aligned visible-ref blocker text"),
    ('assert "Commit-candidate next move is stale; expected to find:" in aligned_doc_only_move_output', "Freshness smoke test fails closed on stale aligned visible-ref next-move text"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint freshness smoke contract looks sane")
