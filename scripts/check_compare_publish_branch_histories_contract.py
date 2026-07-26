#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "scripts" / "compare_publish_branch_histories.py"

EXPECTATIONS = [
    ('REVIEWED_DROP_CANDIDATES_BY_BRANCH_PAIR: dict[tuple[str, str], set[str]] = {', "Branch-history helper tracks reviewed older commits that are already ready to drop for known branch pairs"),
    ('KNOWN_ABSORPTION_MARKERS: dict[str, dict[str, list[str]]] = {', "Branch-history helper carries known absorbed-commit markers for generalized coverage cases"),
    ('"scripts: stabilize verifier checkpoint refresh tracking"', "Branch-history helper recognizes the older checkpoint-refresh tracking commit as a known absorption case"),
    ('def ref_exists(ref: str) -> bool:', "Branch-history helper can verify candidate refs before comparing histories"),
    ('def resolve_ref(ref: str) -> str:', "Branch-history helper can normalize branch names to concrete local or remote-tracking refs"),
    ('"--verify", "--quiet", f"{ref}^{{commit}}"', "Branch-history helper resolves refs through commit verification rather than trusting ambiguous short names"),
    ('f"refs/heads/{ref}"', "Branch-history helper falls back to explicit local branch refs"),
    ('f"refs/remotes/{ref}"', "Branch-history helper falls back to explicit remote-tracking refs"),
    ('Could not resolve ref', "Branch-history helper fails closed when neither local nor remote-tracking refs exist"),
    ('def cherry(from_ref: str, to_ref: str)', "Branch-history helper defines a git cherry reader"),
    ('run_git("cherry", from_ref, to_ref)', "Branch-history helper shells out to git cherry"),
    ('def commit_paths(commit: str)', "Branch-history helper defines a changed-path reader"),
    ('run_git("show", "--format=", "--name-only", commit)', "Branch-history helper reads touched paths for each commit"),
    ('def commit_patch(commit: str) -> str:', "Branch-history helper can read a full commit patch for absorption checks"),
    ('run_git("show", "--format=email", "--binary", commit)', "Branch-history helper reads binary-safe email patches"),
    ('def patch_delta_by_path(commit: str) -> dict[str, tuple[list[str], list[str]]]:', "Branch-history helper can extract per-file added and removed lines"),
    ('run_git("show", "--format=", "--unified=0", "--no-ext-diff", commit)', "Branch-history helper reads zero-context diffs for textual absorption checks"),
    ('def is_doc_only(paths: list[str]) -> bool:', "Branch-history helper classifies doc-only commits"),
    ('all(path.startswith("docs/") for path in paths)', "Branch-history helper treats docs/ paths as doc-only churn"),
    ('def is_code_only(paths: list[str]) -> bool:', "Branch-history helper classifies code-only commits"),
    ('not has_doc_paths(paths)', "Branch-history helper recognizes code-only paths without docs/ churn"),
    ('def commit_is_absorbed_by_ref(commit: str, ref: str) -> bool:', "Branch-history helper detects code-only commits already absorbed on the cleaner ref"),
    ('def commit_is_textually_absorbed_by_ref(commit: str, ref: str) -> bool:', "Branch-history helper falls back to textual absorption when reverse apply is too strict"),
    ('def commit_matches_known_absorption(commit: str, ref: str) -> bool:', "Branch-history helper can recognize known absorbed commits whose coverage was later generalized"),
    ('run_git("worktree", "add", "--quiet", "--detach", str(worktree), ref)', "Branch-history helper stages absorption checks in a throwaway detached worktree"),
    ('["git", "apply", "--check", "--reverse"]', "Branch-history helper uses reverse patch application to detect absorbed commits"),
    ('return commit_is_textually_absorbed_by_ref(commit, ref)', "Branch-history helper falls back to textual absorption after reverse-apply failures"),
    ('or commit_matches_known_absorption(commit, ref)', "Branch-history helper also recognizes known absorbed commits after textual fallback"),
    ('def divergence_counts(left_ref: str, right_ref: str)', "Branch-history helper defines divergence counting"),
    ('run_git("rev-list", "--left-right", "--count", f"{left_ref}...{right_ref}")', "Branch-history helper reads left-right divergence counts"),
    ('Patch-equivalent commits already represented on', "Branch-history helper reports patch-equivalent duplicates"),
    ('True branch-only commits on', "Branch-history helper reports truly unique commits"),
    ('print(f"    paths: {\', \'.join(paths)}")', "Branch-history helper prints touched paths under each listed commit"),
    ('def print_commit_list(title: str, commits: list[str], include_paths: bool = False) -> None:', "Branch-history helper can print explicit commit buckets"),
    ('def canonical_branch_pair_key(ref: str) -> str:', "Branch-history helper can canonicalize branch-pair refs before lookup"),
    ('def reviewed_drop_candidates(older_ref: str, cleaner_ref: str) -> set[str]:', "Branch-history helper can load reviewed drop candidates for a branch pair"),
    ('canonical_branch_pair_key(older_ref)', "Branch-history helper normalizes older branch-pair refs before reviewed-drop lookup"),
    ('canonical_branch_pair_key(cleaner_ref)', "Branch-history helper normalizes cleaner branch-pair refs before reviewed-drop lookup"),
    ('if include_paths:', "Branch-history helper can optionally show touched paths inside explicit buckets"),
    ('Code-only older commits already absorbed on', "Branch-history helper prints absorbed older code-only commits explicitly"),
    ('Replay-safe code-only older commits still unique to', "Branch-history helper prints replay-safe older code-only commits explicitly"),
    ('Older mixed docs+code commits requiring manual review:', "Branch-history helper prints mixed older commits explicitly"),
    ('Older doc/checkpoint-only commits requiring manual review or drop:', "Branch-history helper prints doc-only older commits explicitly"),
    ('Older commits already reviewed and ready to drop:', "Branch-history helper prints previously reviewed older commits explicitly"),
    ('unresolved_older = [', "Branch-history helper tracks unresolved older-only commits separately from already-absorbed churn"),
    ('Suggested next step:', "Branch-history helper prints a reconciliation next-step section"),
    ('git cherry-pick', "Branch-history helper prints an exact cherry-pick command"),
    ('review code-only older commits and cherry-pick only the ones worth keeping onto', "Branch-history helper prefers code-only replay guidance"),
    ('already absorbed on', "Branch-history helper reports code-only commits already absorbed by the cleaner ref"),
    ('older mixed docs+code commit(s) remain for manual review before replay', "Branch-history helper leaves mixed docs+code commits for manual review"),
    ('older-only doc/checkpoint commit(s) remain for manual review or drop', "Branch-history helper leaves doc-only churn for conscious review"),
    ('remaining older-only history is doc/checkpoint churn only; treat it as intentional drop noise unless you need it for archaeology', "Branch-history helper can declare the doc-only terminal reconciliation state explicitly"),
    ('older branch still has {len(unresolved_older)} older-only commit(s) to review/drop consciously', "Branch-history helper reports only unresolved older-only commits in the final summary"),
    ('# no older-only commits remain', "Branch-history helper can clear the final older-only summary once only absorbed churn remains"),
    ('parser.add_argument("older_ref"', "Branch-history helper accepts an older branch ref"),
    ('parser.add_argument("cleaner_ref"', "Branch-history helper accepts a cleaner branch ref"),
    ('resolved_older_ref = resolve_ref(args.older_ref)', "Branch-history helper normalizes the older ref before git history math"),
    ('resolved_cleaner_ref = resolve_ref(args.cleaner_ref)', "Branch-history helper normalizes the cleaner ref before git history math"),
    ('divergence_counts(resolved_older_ref, resolved_cleaner_ref)', "Branch-history helper computes divergence counts on normalized refs"),
    ('cherry(resolved_older_ref, resolved_cleaner_ref)', "Branch-history helper computes cleaner-vs-older cherry data on normalized refs"),
    ('cherry(resolved_cleaner_ref, resolved_older_ref)', "Branch-history helper computes older-vs-cleaner cherry data on normalized refs"),
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


text = TARGET.read_text()

for needle, message in EXPECTATIONS:
    if needle not in text:
        fail(message)
    print(f"[PASS] {message}")

print("[PASS] Compare publish branch histories contract looks sane")
