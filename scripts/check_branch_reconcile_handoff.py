#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NOTE = REPO_ROOT / "ci-artifacts" / "branch-reconcile-2026-07-10.md"
DEFAULT_OLDER_REF = "fix/openclaw-config-path-and-local-mode"
DEFAULT_CLEANER_REF = "transplant/fix-openclaw-config-path-and-local-mode-clean-stack"
NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def git(*args: str) -> str:
    return run_git(*args).stdout.strip()


def git_optional(*args: str) -> str | None:
    result = run_git(*args, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def ref_exists(ref: str) -> bool:
    return run_git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False).returncode == 0


def resolve_ref(ref: str) -> str:
    candidates = [ref]
    if not ref.startswith("refs/heads/"):
        candidates.append(f"refs/heads/{ref}")
    if not ref.startswith("refs/remotes/"):
        candidates.append(f"refs/remotes/{ref}")
    for candidate in candidates:
        if ref_exists(candidate):
            return candidate
    fail(f"Could not resolve ref '{ref}'. Tried: {', '.join(candidates)}")
    return ref


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def require_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"{label} is stale; expected to find: {needle}")


def require_absent(text: str, needle: str, label: str) -> None:
    if needle in text:
        fail(f"{label} is stale; unexpected legacy text found: {needle}")


def note_relpath(note_path: Path) -> str:
    return str(note_path.resolve().relative_to(REPO_ROOT))


def is_non_logic_path(path: str) -> bool:
    return path.startswith(NON_LOGIC_PREFIXES)


def commit_paths(ref: str) -> list[str]:
    return [
        line.strip()
        for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", ref).splitlines()
        if line.strip()
    ]


def is_handoff_only_commit(ref: str, rel_note_path: str) -> bool:
    changed_paths = commit_paths(ref)
    return bool(changed_paths) and all(path == rel_note_path for path in changed_paths)


def is_checkpoint_doc_only_commit(ref: str) -> bool:
    changed_paths = commit_paths(ref)
    return bool(changed_paths) and all(is_non_logic_path(path) for path in changed_paths)


def latest_non_handoff_ref(rel_note_path: str) -> str:
    ref = "HEAD"
    while is_handoff_only_commit(ref, rel_note_path) or is_checkpoint_doc_only_commit(ref):
        parent = git_optional("rev-parse", f"{ref}^")
        if not parent:
            fail(
                "branch-reconcile handoff checker could not step back past handoff/doc-only bookkeeping HEAD."
            )
        ref = parent
    return ref


def tracked_publish_checkpoint_ref(upstream: str) -> str:
    ref = "HEAD"
    while ref != upstream and is_checkpoint_doc_only_commit(ref):
        ref = git("rev-parse", f"{ref}^")
    return ref


def expected_checkpoint_line(
    tracked_head_short: str, current_head_ahead_count: str, tracked_ref_is_head: bool
) -> str:
    if tracked_ref_is_head:
        if current_head_ahead_count != "0":
            return (
                f"- The current branch tip is already the tracked non-doc publish-boundary checkpoint: `{tracked_head_short}`. "
                "It still needs to become GitHub-visible."
            )
        return (
            f"- The current branch tip is already the tracked non-doc publish-boundary checkpoint: `{tracked_head_short}`, "
            "and it is already GitHub-visible."
        )
    if current_head_ahead_count != "0":
        return (
            f"- The last non-doc tracked publish-boundary checkpoint remains `{tracked_head_short}` "
            "until the current doc-only tip becomes GitHub-visible."
        )
    return (
        f"- The last non-doc tracked publish-boundary checkpoint remains `{tracked_head_short}` "
        "while the exact current doc-only tip is already GitHub-visible."
    )


def expected_next_move_line(current_head_ahead_count: str) -> str:
    if current_head_ahead_count != "0":
        return (
            "Use `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` as the canonical local publish baseline. "
            "The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block "
            "should stay focused on the external publish boundary: make the current transplant tip GitHub-visible, rerun "
            "`Bootstrap Installer Preflight` on that exact visible ref, then proceed to VM verifier preflight / proof if it stays green."
        )
    return (
        "Use `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` as the canonical local publish baseline. "
        "The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block "
        "should stay focused on the visible publish boundary: rerun `Bootstrap Installer Preflight` on that exact visible ref, "
        "then proceed to VM verifier preflight / proof if it stays green."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fail closed when the checked-in branch-reconcile handoff note drifts away from the "
            "current local publish-boundary state."
        )
    )
    parser.add_argument(
        "--older-ref",
        default=DEFAULT_OLDER_REF,
        help="Older or noisier branch/ref described by the handoff note",
    )
    parser.add_argument(
        "--cleaner-ref",
        default=DEFAULT_CLEANER_REF,
        help="Cleaner transplant branch/ref described by the handoff note",
    )
    parser.add_argument(
        "--note-path",
        default=str(DEFAULT_NOTE.relative_to(REPO_ROOT)),
        help="Path to the checked-in branch-reconcile note, relative to repo root",
    )
    args = parser.parse_args()

    note_path = (REPO_ROOT / args.note_path).resolve()
    if not note_path.exists():
        fail(f"missing branch-reconcile note: {note_path}")
    rel_note_path = note_relpath(note_path)

    current_branch = git_optional("branch", "--show-current")
    if not current_branch:
        fail("branch-reconcile handoff check requires a checked-out branch.")

    upstream = git_optional("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")
    if not upstream:
        fail(f"branch '{current_branch}' has no upstream; cannot verify branch-reconcile handoff.")

    current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")
    latest_handoff_ref = latest_non_handoff_ref(rel_note_path)
    latest_handoff_short = git("rev-parse", "--short", latest_handoff_ref)
    tracked_checkpoint_ref = tracked_publish_checkpoint_ref(upstream)
    tracked_checkpoint_short = git("rev-parse", "--short", tracked_checkpoint_ref)
    tracked_ref_is_head = tracked_checkpoint_ref == "HEAD"
    resolved_older_ref = resolve_ref(args.older_ref)
    older_count, cleaner_count = git(
        "rev-list",
        "--left-right",
        "--count",
        f"{resolved_older_ref}...{latest_handoff_ref}",
    ).split()

    note_text = note_path.read_text(encoding="utf-8")
    require_contains(
        note_text,
        f"- `{args.cleaner_ref}` is the cleaner publish candidate.",
        "Branch-reconcile note cleaner-branch line",
    )
    require_contains(
        note_text,
        (
            f"- The latest non-handoff branch tip captured by this note is `{latest_handoff_short}`; "
            "later doc-only checkpoint or branch-reconcile-only handoff refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit."
        ),
        "Branch-reconcile note captured tip line",
    )
    require_contains(
        note_text,
        expected_checkpoint_line(
            tracked_checkpoint_short,
            current_head_ahead_count,
            tracked_ref_is_head,
        ),
        "Branch-reconcile note tracked checkpoint line",
    )
    require_contains(
        note_text,
        "- Divergence count from `git rev-list --left-right --count "
        "fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack`:",
        "Branch-reconcile note divergence heading",
    )
    require_contains(
        note_text,
        f"  - `{args.older_ref}`: `{older_count}`",
        "Branch-reconcile note older divergence count",
    )
    require_contains(
        note_text,
        f"  - `{args.cleaner_ref}`: `{cleaner_count}`",
        "Branch-reconcile note cleaner divergence count",
    )
    require_contains(
        note_text,
        expected_next_move_line(current_head_ahead_count),
        "Branch-reconcile note best-next-move guidance",
    )
    require_absent(
        note_text,
        "As of `",
        "Branch-reconcile note legacy appendix",
    )

    print("[PASS] Branch-reconcile handoff note matches current publish-boundary state")


if __name__ == "__main__":
    main()
