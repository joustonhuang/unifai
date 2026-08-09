#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import importlib.util
import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NOTE = REPO_ROOT / "ci-artifacts" / "publish-stack-reconciliation-next-step.txt"
DEFAULT_OLDER_REF = "fix/openclaw-config-path-and-local-mode"
DEFAULT_CLEANER_REF = "transplant/fix-openclaw-config-path-and-local-mode-clean-stack"
COMPARE_HELPER = REPO_ROOT / "scripts" / "compare_publish_branch_histories.py"
GENERATED_PREFIX = "Generated: "


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def load_compare_helper():
    spec = importlib.util.spec_from_file_location("compare_publish_branch_histories", COMPARE_HELPER)
    if spec is None or spec.loader is None:
        fail(f"Could not load publish-branch-history helper from {COMPARE_HELPER}")
    compare_publish_branch_histories = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compare_publish_branch_histories)
    return compare_publish_branch_histories


def parse_generated_at(note_text: str) -> str:
    for line in note_text.splitlines():
        if line.startswith(GENERATED_PREFIX):
            return line[len(GENERATED_PREFIX) :]
    fail("Publish-stack reconciliation note is missing its generated-at line.")
    return ""


def refresh_command(older_ref: str, cleaner_ref: str, generated_at: str) -> str:
    return (
        "python3 scripts/compare_publish_branch_histories.py "
        f"{older_ref} {cleaner_ref} --write-reconciliation-note "
        f"--generated-at {shlex.quote(generated_at)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fail closed when the checked-in publish-stack reconciliation note drifts away from "
            "the current local branch-comparison state."
        )
    )
    parser.add_argument(
        "--older-ref",
        default=DEFAULT_OLDER_REF,
        help="Older or noisier branch/ref summarized by the reconciliation note",
    )
    parser.add_argument(
        "--cleaner-ref",
        default=DEFAULT_CLEANER_REF,
        help="Cleaner baseline branch/ref summarized by the reconciliation note",
    )
    parser.add_argument(
        "--note-path",
        default=str(DEFAULT_NOTE.relative_to(REPO_ROOT)),
        help="Path to the checked-in reconciliation note, relative to repo root",
    )
    args = parser.parse_args()

    note_path = (REPO_ROOT / args.note_path).resolve()
    if not note_path.exists():
        fail(f"missing publish-stack reconciliation note: {note_path}")

    note_text = note_path.read_text(encoding="utf-8")
    generated_at = parse_generated_at(note_text)

    compare_publish_branch_histories = load_compare_helper()
    resolved_older_ref = compare_publish_branch_histories.resolve_ref(args.older_ref)
    resolved_cleaner_ref = compare_publish_branch_histories.resolve_ref(args.cleaner_ref)
    left_count, right_count = compare_publish_branch_histories.divergence_counts(
        resolved_older_ref,
        resolved_cleaner_ref,
    )
    cleaner_vs_older = compare_publish_branch_histories.cherry(
        resolved_older_ref,
        resolved_cleaner_ref,
    )
    older_vs_cleaner = compare_publish_branch_histories.cherry(
        resolved_cleaner_ref,
        resolved_older_ref,
    )
    expected_note = compare_publish_branch_histories.build_reconciliation_note(
        args.older_ref,
        args.cleaner_ref,
        left_count,
        right_count,
        older_vs_cleaner,
        cleaner_vs_older,
        generated_at=generated_at,
    )
    if note_text != expected_note:
        preview = "".join(
            difflib.unified_diff(
                expected_note.splitlines(keepends=True),
                note_text.splitlines(keepends=True),
                fromfile="expected",
                tofile="actual",
                n=2,
            )
        )
        preview_lines = "\n".join(preview.splitlines()[:20]) if preview else "(no diff preview available)"
        fail(
            "Publish-stack reconciliation note is stale. Refresh it with: "
            f"{refresh_command(args.older_ref, args.cleaner_ref, generated_at)}\n"
            f"{preview_lines}"
        )

    print("[PASS] Publish-stack reconciliation note matches current branch-comparison state")


if __name__ == "__main__":
    main()
