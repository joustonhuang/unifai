#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"
DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"
COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"
CHECKPOINT_DOCS = {
    str(DOC_BOUNDARY.relative_to(REPO_ROOT)),
    str(DOC_CHECKPOINT.relative_to(REPO_ROOT)),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def git_optional(*args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def is_checkpoint_doc_only_commit(ref: str) -> bool:
    changed_paths = {
        line.strip()
        for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", ref).splitlines()
        if line.strip()
    }
    return bool(changed_paths) and changed_paths.issubset(CHECKPOINT_DOCS)


def require_contains(text: str, needle: str, label: str) -> int:
    if needle not in text:
        return fail(f"{label} is stale; expected to find: {needle}")
    return 0


def main() -> int:
    current_branch = git_optional("branch", "--show-current")
    if not current_branch:
        return fail("checkpoint freshness check requires a checked-out branch.")

    upstream = git_optional("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")
    if not upstream:
        return fail(f"branch '{current_branch}' has no upstream; cannot verify checkpoint freshness.")

    tracked_ref = "HEAD"
    while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):
        tracked_ref = git("rev-parse", f"{tracked_ref}^")

    tracked_head_short = git("rev-parse", "--short", tracked_ref)
    tracked_head_subject = git("show", "-s", "--format=%s", tracked_ref)
    current_head_short = git("rev-parse", "--short", "HEAD")
    current_head_subject = git("show", "-s", "--format=%s", "HEAD")
    ahead_count = git("rev-list", "--count", f"{upstream}..{tracked_ref}")
    current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")

    boundary_text = DOC_BOUNDARY.read_text(encoding="utf-8")
    checkpoint_text = DOC_CHECKPOINT.read_text(encoding="utf-8")
    commit_candidate_text = COMMIT_CANDIDATE.read_text(encoding="utf-8")

    checks = [
        (
            boundary_text,
            f"through `{tracked_head_short}` (`{tracked_head_subject}`), {ahead_count} commits ahead in total",
            "Boundary doc",
        ),
        (
            checkpoint_text,
            f"Latest tracked local head in the stack: `{tracked_head_short}`",
            "Checkpoint doc tracked head",
        ),
        (
            checkpoint_text,
            f"Tracked local branch state at checkpoint: ahead by {ahead_count} commits over the GitHub-visible branch head",
            "Checkpoint doc ahead count",
        ),
        (
            commit_candidate_text,
            f"Current local checkpoint: {tracked_head_short}\n",
            "Commit-candidate tracked head",
        ),
        (
            commit_candidate_text,
            f"Current branch state: ahead {current_head_ahead_count} over {upstream}\n",
            "Commit-candidate branch state",
        ),
    ]

    for text, needle, label in checks:
        status = require_contains(text, needle, label)
        if status:
            return status

    tip_line = f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\n"
    if tracked_ref != "HEAD":
        status = require_contains(commit_candidate_text, tip_line, "Commit-candidate checked-out tip")
        if status:
            return status
    elif tip_line in commit_candidate_text:
        return fail("commit-candidate tip line should not be present when the tracked checkpoint is HEAD.")

    print("[PASS] VM verifier checkpoint artifacts match current repo state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
