#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_branch_reconcile_handoff.py"
SMOKE = REPO_ROOT / "scripts" / "smoke_test_branch_reconcile_handoff.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")
smoke_text = SMOKE.read_text(encoding="utf-8")

required = [
    ('DEFAULT_NOTE = REPO_ROOT / "ci-artifacts" / "branch-reconcile-2026-07-10.md"', "Branch-reconcile checker targets the checked-in handoff note"),
    ('DEFAULT_OLDER_REF = "fix/openclaw-config-path-and-local-mode"', "Branch-reconcile checker defaults to the legacy older branch"),
    ('DEFAULT_CLEANER_REF = "transplant/fix-openclaw-config-path-and-local-mode-clean-stack"', "Branch-reconcile checker defaults to the cleaner transplant branch"),
    ('NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")', "Branch-reconcile checker reuses the non-logic publish-boundary classification"),
    ('def note_relpath(note_path: Path) -> str:', "Branch-reconcile checker can normalize the note path relative to repo root"),
    ('def ref_exists(ref: str) -> bool:', "Branch-reconcile checker can verify candidate refs before divergence math"),
    ('def resolve_ref(ref: str) -> str:', "Branch-reconcile checker can normalize branch names to concrete refs"),
    ('f"refs/heads/{ref}"', "Branch-reconcile checker falls back to explicit local branch refs"),
    ('f"refs/remotes/{ref}"', "Branch-reconcile checker falls back to explicit remote-tracking refs"),
    ('def is_handoff_only_commit(ref: str, rel_note_path: str) -> bool:', "Branch-reconcile checker can classify note-only bookkeeping commits"),
    ('all(path == rel_note_path for path in changed_paths)', "Branch-reconcile checker treats note-only commits as handoff bookkeeping"),
    ('def latest_non_handoff_ref(rel_note_path: str) -> str:', "Branch-reconcile checker walks back past handoff-only HEAD commits"),
    ('while is_handoff_only_commit(ref, rel_note_path):', "Branch-reconcile checker ignores handoff-only refresh commits when finding the captured tip"),
    ('def is_checkpoint_doc_only_commit(ref: str) -> bool:', "Branch-reconcile checker can classify doc-only publish-boundary commits"),
    ('while ref != upstream and is_checkpoint_doc_only_commit(ref):', "Branch-reconcile checker walks back past doc-only publish-boundary commits to the tracked checkpoint"),
    ('def expected_checkpoint_line(tracked_head_short: str, current_head_ahead_count: str) -> str:', "Branch-reconcile checker derives visibility-aware tracked-checkpoint wording"),
    ('until the current doc-only tip becomes GitHub-visible.', "Branch-reconcile checker validates the unpublished doc-only-tip blocker wording"),
    ('while the exact current doc-only tip is already GitHub-visible.', "Branch-reconcile checker validates the aligned doc-only-tip wording"),
    ('def expected_next_move_line(current_head_ahead_count: str) -> str:', "Branch-reconcile checker derives visibility-aware next-move guidance"),
    ('"should stay focused on the external publish boundary: make the current transplant tip GitHub-visible, rerun "', "Branch-reconcile checker validates the unpublished next move"),
    ('"should stay focused on the visible publish boundary: rerun `Bootstrap Installer Preflight` on that exact visible ref, "', "Branch-reconcile checker validates the aligned visible-ref next move"),
    ('git("rev-list", "--count", f"{upstream}..HEAD")', "Branch-reconcile checker captures current branch visibility state from upstream divergence"),
    ('resolved_older_ref = resolve_ref(args.older_ref)', "Branch-reconcile checker resolves the older ref before divergence math"),
    ('f"{resolved_older_ref}...{latest_handoff_ref}"', "Branch-reconcile checker anchors divergence counts to the latest non-handoff tip"),
    ('f"- The latest non-handoff branch tip captured by this note is `{latest_handoff_short}`; "', "Branch-reconcile checker validates the captured non-handoff tip line"),
    ('"[PASS] Branch-reconcile handoff note matches current publish-boundary state"', "Branch-reconcile checker emits a passing verdict"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

smoke_required = [
    ('python3 scripts/check_branch_reconcile_handoff.py', "Branch-reconcile smoke test exercises the checker on a synthetic publish-boundary repo"),
    ('docs: refresh branch reconcile publish handoff', "Branch-reconcile smoke test creates a handoff-only bookkeeping commit at HEAD"),
    ('The latest non-handoff branch tip captured by this note is', "Branch-reconcile smoke test writes a synthetic handoff note with a captured non-handoff tip"),
    ('Expected branch-reconcile checker to reject a note that captures the bookkeeping HEAD tip.', "Branch-reconcile smoke test fail-closes on self-stale captured-tip wording"),
    ('Expected branch-reconcile checker to reject stale divergence counts.', "Branch-reconcile smoke test fail-closes on stale divergence counts"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

print("[PASS] Branch-reconcile handoff contract looks sane")
