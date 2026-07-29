#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"
DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"
CHECKPOINT_LATEST = REPO_ROOT / "ci-artifacts" / "vm-verifier-checkpoint-latest.md"
COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"
CHECKPOINT_DOCS = {
    str(DOC_BOUNDARY.relative_to(REPO_ROOT)),
    str(DOC_CHECKPOINT.relative_to(REPO_ROOT)),
}
NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")


def is_non_logic_path(path: str) -> bool:
    return path.startswith(NON_LOGIC_PREFIXES)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def git_optional(*args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def upstream_display_name(upstream: str) -> str:
    return upstream.split("/", 1)[1] if "/" in upstream else upstream


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def is_checkpoint_doc_only_commit(ref: str) -> bool:
    changed_paths = {
        line.strip()
        for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", ref).splitlines()
        if line.strip()
    }
    return bool(changed_paths) and all(is_non_logic_path(path) for path in changed_paths)


def require_contains(text: str, needle: str, label: str) -> int:
    if needle not in text:
        return fail(f"{label} is stale; expected to find: {needle}")
    return 0


def effective_dirty_paths(dirty_paths: list[str], tracked_ref: str) -> list[str]:
    if tracked_ref != "HEAD":
        return [path for path in dirty_paths if path not in CHECKPOINT_DOCS]
    return dirty_paths


def dirty_bundle_lines(dirty_paths: list[str]) -> tuple[str, str]:
    if dirty_paths:
        shown = ", ".join(f"`{path}`" for path in dirty_paths[:5])
        if len(dirty_paths) > 5:
            shown += f", and {len(dirty_paths) - 5} more"
        update_word = "update" if len(dirty_paths) == 1 else "updates"
        boundary_line = (
            f"- the local sandbox currently also carries {len(dirty_paths)} uncommitted "
            f"publish-boundary maintenance path(s) beyond HEAD ({shown})"
        )
        checkpoint_line = (
            "- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the "
            f"GitHub-visible branch: the latest tracked commit is now `{{tracked_head_short}}`, that same commit is also the latest "
            f"non-doc logic head, the sandbox currently carries {len(dirty_paths)} uncommitted publish-boundary maintenance "
            f"{update_word}, and the branch is `ahead {{ahead_count}}` over `{{upstream_display}}`."
        )
        return boundary_line, checkpoint_line
    return (
        "- the local sandbox currently carries no additional uncommitted publish-boundary maintenance delta",
        "- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the "
        "GitHub-visible branch: the latest tracked commit is now `{tracked_head_short}`, that same commit is also the latest "
        "non-doc logic head, the sandbox currently carries no additional uncommitted publish-boundary maintenance updates, "
        "and the branch is `ahead {ahead_count}` over `{upstream_display}`.",
    )


def main() -> int:
    current_branch = git_optional("branch", "--show-current")
    if not current_branch:
        return fail("checkpoint freshness check requires a checked-out branch.")

    upstream = git_optional("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")
    if not upstream:
        return fail(f"branch '{current_branch}' has no upstream; cannot verify checkpoint freshness.")
    upstream_display = upstream_display_name(upstream)

    tracked_ref = "HEAD"
    while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):
        tracked_ref = git("rev-parse", f"{tracked_ref}^")

    tracked_head_short = git("rev-parse", "--short", tracked_ref)
    tracked_head_subject = git("show", "-s", "--format=%s", tracked_ref)
    current_head_short = git("rev-parse", "--short", "HEAD")
    current_head_subject = git("show", "-s", "--format=%s", "HEAD")
    ahead_count = git("rev-list", "--count", f"{upstream}..{tracked_ref}")
    current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")
    upstream_short = git("rev-parse", "--short", upstream)
    latest_non_doc_all_paths = [
        line.strip()
        for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", tracked_ref).splitlines()
        if line.strip()
    ]
    latest_non_doc_paths = [
        path for path in latest_non_doc_all_paths if not is_non_logic_path(path)
    ] or latest_non_doc_all_paths
    status_lines = git("status", "--short").splitlines()
    dirty_paths = effective_dirty_paths(
        [line.split(maxsplit=1)[1] for line in status_lines if len(line.split(maxsplit=1)) == 2],
        tracked_ref,
    )
    boundary_dirty_line, checkpoint_dirty_line = dirty_bundle_lines(dirty_paths)

    boundary_text = DOC_BOUNDARY.read_text(encoding="utf-8")
    checkpoint_text = DOC_CHECKPOINT.read_text(encoding="utf-8")
    checkpoint_latest_text = CHECKPOINT_LATEST.read_text(encoding="utf-8")
    commit_candidate_text = COMMIT_CANDIDATE.read_text(encoding="utf-8")

    checks = [
        (
            boundary_text,
            f"through `{tracked_head_short}` (`{tracked_head_subject}`), {ahead_count} commits ahead in total",
            "Boundary doc",
        ),
        (
            boundary_text,
            f"- the latest non-doc logic delta in that local stack is `{tracked_head_short}` (`{tracked_head_subject}`) in:",
            "Boundary doc latest non-doc head",
        ),
        (
            boundary_text,
            boundary_dirty_line,
            "Boundary doc dirty bundle summary",
        ),
        (
            checkpoint_text,
            f"Latest tracked local head in the stack: `{tracked_head_short}`",
            "Checkpoint doc tracked head",
        ),
        (
            checkpoint_latest_text,
            f"Latest tracked local head in the stack: `{tracked_head_short}`",
            "Checkpoint latest tracked head",
        ),
        (
            checkpoint_text,
            f"Tracked local branch state at checkpoint: ahead by {ahead_count} commits over the GitHub-visible branch head",
            "Checkpoint doc ahead count",
        ),
        (
            checkpoint_text,
            checkpoint_dirty_line.format(
                tracked_head_short=tracked_head_short,
                ahead_count=ahead_count,
                upstream_display=upstream_display,
            ),
            "Checkpoint doc dirty bundle summary",
        ),
        (
            checkpoint_latest_text,
            f"Tracked local branch state at checkpoint: ahead by {ahead_count} commits over the GitHub-visible branch head",
            "Checkpoint latest ahead count",
        ),
        (
            commit_candidate_text,
            f"Current local checkpoint: {tracked_head_short}\n",
            "Commit-candidate tracked head",
        ),
        (
            commit_candidate_text,
            f"Current branch state: ahead {current_head_ahead_count} over {upstream_display}\n",
            "Commit-candidate branch state",
        ),
    ]

    for text, needle, label in checks:
        status = require_contains(text, needle, label)
        if status:
            return status

    if checkpoint_latest_text != checkpoint_text:
        return fail("Checkpoint latest handoff artifact diverges from the dated checkpoint doc.")

    for path in latest_non_doc_paths:
        status = require_contains(boundary_text, f"  - `{path}`", "Boundary doc latest non-doc paths")
        if status:
            return status

    if "Current uncommitted delta on top:\n" in checkpoint_text:
        for path in dirty_paths:
            status = require_contains(checkpoint_text, f"  - `{path}`", "Checkpoint doc dirty bundle paths")
            if status:
                return status

    tip_line = f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\n"
    if tracked_ref != "HEAD" and current_head_ahead_count != "0":
        if "the current checked-out branch tip is `" in boundary_text:
            return fail("boundary doc checked-out tip line should stay out of tracked docs to avoid doc-only self-refresh churn.")
        if "- Current checked-out branch tip: `" in checkpoint_text:
            return fail("checkpoint doc checked-out tip line should stay out of tracked docs to avoid doc-only self-refresh churn.")
        status = require_contains(commit_candidate_text, tip_line, "Commit-candidate checked-out tip")
        if status:
            return status
        status = require_contains(
            commit_candidate_text,
            (
                f"- The branch still needs the current branch tip `{current_head_short}` GitHub-visible; "
                f"the tracked publish-boundary checkpoint remains `{tracked_head_short}` until that visible ref exists.\n"
            ),
            "Commit-candidate external blocker",
        )
        if status:
            return status
        status = require_contains(
            commit_candidate_text,
            (
                f"- Make the current branch tip `{current_head_short}` GitHub-visible on `{upstream_display}`; "
                f"the tracked publish-boundary checkpoint remains `{tracked_head_short}` until a non-doc commit supersedes it.\n"
            ),
            "Commit-candidate next move",
        )
        if status:
            return status
    elif tracked_ref != "HEAD":
        if "the current checked-out branch tip is `" in boundary_text:
            return fail("boundary doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible.")
        if "- Current checked-out branch tip: `" in checkpoint_text:
            return fail("checkpoint doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible.")
        status = require_contains(commit_candidate_text, tip_line, "Commit-candidate checked-out tip")
        if status:
            return status
        status = require_contains(
            commit_candidate_text,
            (
                f"- The exact branch tip `{current_head_short}` is already GitHub-visible on `{upstream_display}`; "
                f"the tracked publish-boundary checkpoint remains `{tracked_head_short}` because the tip-only delta is doc-only.\n"
            ),
            "Commit-candidate external blocker",
        )
        if status:
            return status
        status = require_contains(
            commit_candidate_text,
            (
                f"- The exact branch tip `{current_head_short}` is already GitHub-visible on `{upstream_display}`; "
                f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{tracked_head_short}`.\n"
            ),
            "Commit-candidate next move",
        )
        if status:
            return status
    else:
        if "the current checked-out branch tip is `" in boundary_text:
            return fail("boundary doc checked-out tip line should not be present when the tracked checkpoint is HEAD.")
        if "- Current checked-out branch tip: `" in checkpoint_text:
            return fail("checkpoint doc checked-out tip line should not be present when the tracked checkpoint is HEAD.")
        if tip_line in commit_candidate_text:
            return fail("commit-candidate tip line should not be present when the tracked checkpoint is HEAD.")
        status = require_contains(
            commit_candidate_text,
            (
                f"- The branch still needs the local checkpoint chain through `{tracked_head_short}` "
                "to become GitHub-visible before the real VM-proof path can continue.\n"
            ),
            "Commit-candidate external blocker",
        )
        if status:
            return status
        status = require_contains(
            commit_candidate_text,
            f"- Make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream_display}`.\n",
            "Commit-candidate next move",
        )
        if status:
            return status

    status = require_contains(
        commit_candidate_text,
        (
            f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on "
            f"`{upstream_short}`, so the next real boundary is still a visible rerun on the exact published ref.\n"
        ),
        "Commit-candidate public blocker note",
    )
    if status:
        return status

    print("[PASS] VM verifier checkpoint artifacts match current repo state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
