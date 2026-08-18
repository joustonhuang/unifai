#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_publish_stack_reconciliation_note.py"
SMOKE = REPO_ROOT / "scripts" / "smoke_test_publish_stack_reconciliation_note.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")
smoke_text = SMOKE.read_text(encoding="utf-8")

required = [
    ('DEFAULT_NOTE = REPO_ROOT / "ci-artifacts" / "publish-stack-reconciliation-next-step.txt"', "Publish-note checker targets the checked-in reconciliation note"),
    ('DEFAULT_OLDER_REF = "fix/openclaw-config-path-and-local-mode"', "Publish-note checker defaults to the legacy older branch"),
    ('DEFAULT_CLEANER_REF = "transplant/fix-openclaw-config-path-and-local-mode-clean-stack"', "Publish-note checker defaults to the cleaner transplant branch"),
    ('COMPARE_HELPER = REPO_ROOT / "scripts" / "compare_publish_branch_histories.py"', "Publish-note checker loads the publish-branch-history helper"),
    ('GENERATED_PREFIX = "Generated: "', "Publish-note checker anchors note freshness to the checked-in timestamp"),
    ('def load_compare_helper():', "Publish-note checker can import the publish-branch-history helper directly"),
    ('importlib.util.spec_from_file_location("compare_publish_branch_histories", COMPARE_HELPER)', "Publish-note checker loads the helper module from disk"),
    ('def parse_generated_at(note_text: str) -> str:', "Publish-note checker can read the checked-in generated-at timestamp"),
    ('if line.startswith(GENERATED_PREFIX):', "Publish-note checker finds the generated-at line by prefix"),
    ('Publish-stack reconciliation note is missing its generated-at line.', "Publish-note checker fails closed on a missing timestamp"),
    ('def refresh_command(older_ref: str, cleaner_ref: str, generated_at: str) -> str:', "Publish-note checker can print an exact refresh command"),
    ('--write-reconciliation-note', "Publish-note checker refresh guidance uses tracked-note write mode"),
    ('--generated-at', "Publish-note checker preserves the existing timestamp while checking freshness"),
    ('resolved_older_ref = compare_publish_branch_histories.resolve_ref(args.older_ref)', "Publish-note checker resolves the older ref through the helper"),
    ('resolved_cleaner_ref = compare_publish_branch_histories.resolve_ref(args.cleaner_ref)', "Publish-note checker resolves the cleaner ref through the helper"),
    ('compare_publish_branch_histories.divergence_counts(', "Publish-note checker recomputes live divergence counts"),
    ('compare_publish_branch_histories.cherry(', "Publish-note checker recomputes live cherry summaries"),
    ('expected_note = compare_publish_branch_histories.build_reconciliation_note(', "Publish-note checker rebuilds the tracked note from the helper source of truth"),
    ('if note_text != expected_note:', "Publish-note checker compares the checked-in note against the regenerated note"),
    ('difflib.unified_diff(', "Publish-note checker shows a unified-diff preview on drift"),
    ('Publish-stack reconciliation note is stale. Refresh it with:', "Publish-note checker fails closed with explicit refresh guidance"),
    ('[PASS] Publish-stack reconciliation note matches current branch-comparison state', "Publish-note checker emits a passing verdict"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

smoke_required = [
    ('python3 scripts/compare_publish_branch_histories.py --write-reconciliation-note --generated-at', "Publish-note smoke test generates a tracked reconciliation note with a deterministic timestamp"),
    ('python3 scripts/check_publish_stack_reconciliation_note.py --older-ref fix/older --cleaner-ref transplant/cleaner', "Publish-note smoke test exercises the checker against synthetic refs"),
    ('docs: cleaner bookkeeping', "Publish-note smoke test creates a live cleaner-only drift after the note snapshot"),
    ('Expected publish-note checker to fail once the cleaner branch drifts past the tracked note.', "Publish-note smoke test fail-closes on live branch drift"),
    ('docs: settle publish reconciliation note', "Publish-note smoke test creates a reconciliation-note-only settle commit after refresh"),
    ('Expected publish-note checker to ignore a cleaner-only note settle commit.', "Publish-note smoke test proves reconciliation-note-only bookkeeping does not invalidate the note"),
    ('Publish-stack reconciliation note matches current branch-comparison state', "Publish-note smoke test covers the passing path"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

print("[PASS] Publish-stack reconciliation note contract looks sane")
