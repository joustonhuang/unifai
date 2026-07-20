#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REVIEWED_DROP_CANDIDATES_BY_BRANCH_PAIR: dict[tuple[str, str], set[str]] = {
    (
        "fix/openclaw-config-path-and-local-mode",
        "transplant/fix-openclaw-config-path-and-local-mode-clean-stack",
    ): {
        "775606195dd1f9e275a08a2c2a7bf106a7e2519f",
        "f4232c51b9b4f933c4eb1c5b679a0a305dbc6aa6",
        "d8539bb09dcbb186570f85ab0cc23216e5427a4b",
        "aaee8379ded3136f2031e9e7bd4155981d31fbac",
        "18f633fae3367195c103ff49a8f96fe04721cd5d",
        "0b062e3fae0ec3202755a1ed6b78a261d66f6255",
        "4996e4ffe250b1b7ecbbff1d70c0b8f4cb518417",
        "4aa294f103acee4eb8ed0df1ca777c5374eb0b59",
        "d7e71524f926dad3f1febff576848298e319c8c8",
        "7af8398310b9858c741127127e8b3250bbba7d67",
        "9e2f0bf2a63e6adf32de81981b4a2895640ff165",
    },
}
KNOWN_ABSORPTION_MARKERS: dict[str, dict[str, list[str]]] = {
    "scripts: stabilize verifier checkpoint refresh tracking": {
        "scripts/refresh_vm_verifier_checkpoint_state.py": [
            "CHECKPOINT_DOCS = {",
            "def is_checkpoint_doc_only_commit(ref: str) -> bool:",
            'while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):',
        ],
        "scripts/smoke_test_vm_verifier_checkpoint_refresh.py": [
            'run(["git", "commit", "-m", "docs: sync visible verifier boundary state"], work)',
            'subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)',
            'assert f"through `{stable_head}` (`{stable_subject}`), {stable_ahead} commits ahead in total" in stable_boundary',
            'assert f"Latest tracked local head in the stack: `{stable_head}`" in stable_checkpoint',
            'assert f"Tracked local branch state at checkpoint: ahead by {stable_ahead} commits over the GitHub-visible branch head" in stable_checkpoint',
        ],
    },
}


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def commit_subject(commit: str) -> str:
    result = run_git("log", "--format=%s", "-n", "1", commit)
    subject = result.stdout.strip()
    if not subject:
        fail(f"Could not resolve commit subject for {commit}")
    return subject


def commit_paths(commit: str) -> list[str]:
    result = run_git("show", "--format=", "--name-only", commit)
    return [line for line in result.stdout.splitlines() if line]


def commit_patch(commit: str) -> str:
    result = run_git("show", "--format=email", "--binary", commit)
    return result.stdout


def patch_delta_by_path(commit: str) -> dict[str, tuple[list[str], list[str]]]:
    result = run_git("show", "--format=", "--unified=0", "--no-ext-diff", commit)
    deltas: dict[str, tuple[list[str], list[str]]] = {}
    current_path: str | None = None
    for raw_line in result.stdout.splitlines():
        if raw_line.startswith("+++ b/"):
            current_path = raw_line[6:]
            deltas.setdefault(current_path, ([], []))
            continue
        if not current_path or raw_line.startswith(("diff --git ", "--- ", "@@")):
            continue
        if raw_line.startswith("+"):
            deltas[current_path][0].append(raw_line[1:])
            continue
        if raw_line.startswith("-"):
            deltas[current_path][1].append(raw_line[1:])
    return deltas


def commit_is_textually_absorbed_by_ref(commit: str, ref: str) -> bool:
    path_deltas = patch_delta_by_path(commit)
    if not path_deltas:
        return False
    with tempfile.TemporaryDirectory(prefix="unifai-compare-publish-history-") as temp_dir:
        worktree = Path(temp_dir) / "worktree"
        run_git("worktree", "add", "--quiet", "--detach", str(worktree), ref)
        try:
            for path, (added_lines, removed_lines) in path_deltas.items():
                target = worktree / path
                if not target.exists():
                    return False
                text = target.read_text(encoding="utf-8")
                if any(line not in text for line in added_lines):
                    return False
                if any(line in text for line in removed_lines):
                    return False
            return True
        finally:
            run_git("worktree", "remove", "--force", str(worktree))


def commit_matches_known_absorption(commit: str, ref: str) -> bool:
    markers = KNOWN_ABSORPTION_MARKERS.get(commit_subject(commit))
    if not markers:
        return False
    with tempfile.TemporaryDirectory(prefix="unifai-compare-publish-history-") as temp_dir:
        worktree = Path(temp_dir) / "worktree"
        run_git("worktree", "add", "--quiet", "--detach", str(worktree), ref)
        try:
            for rel_path, required_markers in markers.items():
                target = worktree / rel_path
                if not target.exists():
                    return False
                text = target.read_text(encoding="utf-8")
                if any(marker not in text for marker in required_markers):
                    return False
            return True
        finally:
            run_git("worktree", "remove", "--force", str(worktree))


def cherry(from_ref: str, to_ref: str) -> list[tuple[str, str, str, list[str]]]:
    result = run_git("cherry", from_ref, to_ref)
    rows: list[tuple[str, str, str, list[str]]] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        marker, commit = line.split(maxsplit=1)
        rows.append((marker, commit, commit_subject(commit), commit_paths(commit)))
    return rows


def divergence_counts(left_ref: str, right_ref: str) -> tuple[int, int]:
    result = run_git("rev-list", "--left-right", "--count", f"{left_ref}...{right_ref}")
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        fail(f"Unexpected rev-list count output: {result.stdout.strip()}")
    return int(parts[0]), int(parts[1])


def print_section(title: str, rows: list[tuple[str, str, str, list[str]]], marker: str) -> None:
    print(title)
    filtered = [row for row in rows if row[0] == marker]
    if not filtered:
        print("  (none)")
        return
    for _, commit, subject, paths in filtered:
        print(f"  {commit} {subject}")
        if paths:
            print(f"    paths: {', '.join(paths)}")


def print_commit_list(title: str, commits: list[str], include_paths: bool = False) -> None:
    print(title)
    if not commits:
        print("  (none)")
        return
    for commit in commits:
        print(f"  {commit} {commit_subject(commit)}")
        if include_paths:
            paths = commit_paths(commit)
            if paths:
                print(f"    paths: {', '.join(paths)}")


def commits_with_marker(rows: list[tuple[str, str, str, list[str]]], marker: str) -> list[str]:
    return [commit for row_marker, commit, _, _ in rows if row_marker == marker]


def reviewed_drop_candidates(older_ref: str, cleaner_ref: str) -> set[str]:
    return REVIEWED_DROP_CANDIDATES_BY_BRANCH_PAIR.get((older_ref, cleaner_ref), set())


def is_doc_only(paths: list[str]) -> bool:
    return bool(paths) and all(path.startswith("docs/") for path in paths)


def has_doc_paths(paths: list[str]) -> bool:
    return any(path.startswith("docs/") for path in paths)


def is_code_only(paths: list[str]) -> bool:
    return bool(paths) and not has_doc_paths(paths)


def commit_is_absorbed_by_ref(commit: str, ref: str) -> bool:
    patch = commit_patch(commit)
    with tempfile.TemporaryDirectory(prefix="unifai-compare-publish-history-") as temp_dir:
        worktree = Path(temp_dir) / "worktree"
        run_git("worktree", "add", "--quiet", "--detach", str(worktree), ref)
        try:
            result = subprocess.run(
                ["git", "apply", "--check", "--reverse"],
                cwd=worktree,
                input=patch,
                text=True,
                capture_output=True,
            )
            if result.returncode == 0:
                return True
        finally:
            run_git("worktree", "remove", "--force", str(worktree))
    return commit_is_textually_absorbed_by_ref(commit, ref) or commit_matches_known_absorption(commit, ref)


def print_reconciliation_next_step(
    older_ref: str,
    cleaner_ref: str,
    older_vs_cleaner: list[tuple[str, str, str, list[str]]],
    cleaner_vs_older: list[tuple[str, str, str, list[str]]],
) -> None:
    already_reviewed = reviewed_drop_candidates(older_ref, cleaner_ref)
    older_unique_rows = [
        row for row in older_vs_cleaner if row[0] == "+" and row[1] not in already_reviewed
    ]
    older_unique = [commit for _, commit, _, _ in older_unique_rows]
    cleaner_unique = commits_with_marker(cleaner_vs_older, "+")
    older_duplicates = commits_with_marker(older_vs_cleaner, "-")
    cleaner_duplicates = commits_with_marker(cleaner_vs_older, "-")
    absorbed_candidates = [
        commit
        for _, commit, _, paths in older_unique_rows
        if is_code_only(paths) and commit_is_absorbed_by_ref(commit, cleaner_ref)
    ]
    unresolved_older = [
        commit for commit in older_unique if commit not in absorbed_candidates
    ]
    replay_candidates = [
        commit
        for _, commit, _, paths in older_unique_rows
        if is_code_only(paths) and commit not in absorbed_candidates
    ]
    doc_only_older = [
        commit for _, commit, _, paths in older_unique_rows if is_doc_only(paths)
    ]
    mixed_older = [
        commit
        for _, commit, _, paths in older_unique_rows
        if paths and not is_doc_only(paths) and not is_code_only(paths)
    ]

    print("Suggested next step:")
    print(f"  git checkout {cleaner_ref}")
    if replay_candidates:
        print(
            f"  # review code-only older commits and cherry-pick only the ones worth keeping onto {cleaner_ref}"
        )
        # `git cherry cleaner older` already reports older-only commits in replay-safe order.
        print(f"  git cherry-pick {' '.join(replay_candidates)}")
    else:
        print(f"  # no code-only older commits remain to replay from {older_ref}")
    if older_duplicates or cleaner_duplicates:
        print("  # patch-equivalent duplicates are already accounted for and do not need replay")
    if absorbed_candidates:
        print(
            f"  # {len(absorbed_candidates)} code-only older commit(s) are already absorbed on {cleaner_ref} and can stay out of replay"
        )
    if cleaner_unique:
        print(
            f"  # {cleaner_ref} still has {len(cleaner_unique)} cleaner-only commit(s); keep it as the baseline during reconciliation"
        )
    if mixed_older:
        print(
            f"  # {len(mixed_older)} older mixed docs+code commit(s) remain for manual review before replay"
        )
    if doc_only_older:
        print(
            f"  # {len(doc_only_older)} older-only doc/checkpoint commit(s) remain for manual review or drop"
        )
    if unresolved_older and not replay_candidates and not mixed_older and doc_only_older:
        print(
            "  # remaining older-only history is doc/checkpoint churn only; treat it as intentional drop noise unless you need it for archaeology"
        )
    if unresolved_older:
        print(
            f"  # older branch still has {len(unresolved_older)} older-only commit(s) to review/drop consciously"
        )
    else:
        print("  # no older-only commits remain")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two local publish branches and separate patch-equivalent duplicate commits "
            "from truly branch-only history."
        )
    )
    parser.add_argument("older_ref", help="Older or noisier local branch/ref")
    parser.add_argument("cleaner_ref", help="Cleaner candidate branch/ref")
    args = parser.parse_args()

    left_count, right_count = divergence_counts(args.older_ref, args.cleaner_ref)
    cleaner_vs_older = cherry(args.older_ref, args.cleaner_ref)
    older_vs_cleaner = cherry(args.cleaner_ref, args.older_ref)

    print("[INFO] Publish branch history comparison")
    print(f"  older:   {args.older_ref}")
    print(f"  cleaner: {args.cleaner_ref}")
    print("Divergence counts (git rev-list --left-right --count):")
    print(f"  {args.older_ref}: {left_count}")
    print(f"  {args.cleaner_ref}: {right_count}")

    print_section(
        f"Patch-equivalent commits already represented on {args.cleaner_ref}:",
        older_vs_cleaner,
        "-",
    )
    print_section(
        f"True branch-only commits on {args.older_ref}:",
        older_vs_cleaner,
        "+",
    )
    print_section(
        f"Patch-equivalent commits already represented on {args.older_ref}:",
        cleaner_vs_older,
        "-",
    )
    print_section(
        f"True branch-only commits on {args.cleaner_ref}:",
        cleaner_vs_older,
        "+",
    )
    older_unique_rows = [row for row in older_vs_cleaner if row[0] == "+"]
    reviewed_drop_commits = [
        commit for _, commit, _, _ in older_unique_rows if commit in reviewed_drop_candidates(args.older_ref, args.cleaner_ref)
    ]
    older_unique_rows = [
        row for row in older_unique_rows if row[1] not in reviewed_drop_candidates(args.older_ref, args.cleaner_ref)
    ]
    absorbed_candidates = [
        commit
        for _, commit, _, paths in older_unique_rows
        if is_code_only(paths) and commit_is_absorbed_by_ref(commit, args.cleaner_ref)
    ]
    replay_candidates = [
        commit
        for _, commit, _, paths in older_unique_rows
        if is_code_only(paths) and commit not in absorbed_candidates
    ]
    mixed_older = [
        commit
        for _, commit, _, paths in older_unique_rows
        if paths and not is_doc_only(paths) and not is_code_only(paths)
    ]
    doc_only_older = [
        commit for _, commit, _, paths in older_unique_rows if is_doc_only(paths)
    ]
    print_commit_list(
        f"Code-only older commits already absorbed on {args.cleaner_ref}:",
        absorbed_candidates,
        include_paths=True,
    )
    print_commit_list(
        f"Replay-safe code-only older commits still unique to {args.older_ref}:",
        replay_candidates,
        include_paths=True,
    )
    print_commit_list(
        f"Older mixed docs+code commits requiring manual review:",
        mixed_older,
        include_paths=True,
    )
    print_commit_list(
        f"Older doc/checkpoint-only commits requiring manual review or drop:",
        doc_only_older,
        include_paths=True,
    )
    print_commit_list(
        f"Older commits already reviewed and ready to drop:",
        reviewed_drop_commits,
        include_paths=True,
    )
    print_reconciliation_next_step(
        args.older_ref,
        args.cleaner_ref,
        older_vs_cleaner,
        cleaner_vs_older,
    )


if __name__ == "__main__":
    main()
