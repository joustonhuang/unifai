#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"
DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def main() -> int:
    current_branch = git("branch", "--show-current")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")
    upstream_short = git("rev-parse", "--short", upstream)
    head_short = git("rev-parse", "--short", "HEAD")
    head_subject = git("show", "-s", "--format=%s", "HEAD")
    ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")

    raw_commits = git("log", "--reverse", "--format=%h\t%s", f"{upstream}..HEAD").splitlines()
    commits = [line.split("\t", 1) for line in raw_commits if line.strip()]
    latest_non_doc = next((sha for sha, subject in reversed(commits) if not subject.startswith("docs:")), head_short)

    status_lines = git("status", "--short").splitlines()
    dirty_paths = [line.split(maxsplit=1)[1] for line in status_lines if len(line.split(maxsplit=1)) == 2]
    commit_lines = "\n".join(
        f"{idx}. `{sha}` — `{subject}`" for idx, (sha, subject) in enumerate(commits, start=1)
    )
    if dirty_paths:
        shown = ", ".join(f"`{path}`" for path in dirty_paths[:5])
        if len(dirty_paths) > 5:
            shown += f", and {len(dirty_paths) - 5} more"
        preservation_line = (
            f"- The current local hardening stack is not fully committed: HEAD is `{head_short}` and the working tree still carries "
            f"{len(dirty_paths)} uncommitted path(s) ({shown})."
        )
        publish_boundary_line = (
            "- The check-gate hardening bundle is no longer only a clean-commit story: the commit stack is preserved, "
            "but the current sandbox also carries additional uncommitted verifier-hardening delta."
        )
        boundary_dirty_line = (
            f"- the local sandbox currently also carries {len(dirty_paths)} uncommitted verifier-hardening path(s) beyond HEAD ({shown})"
        )
    else:
        preservation_line = (
            f"- The current local hardening stack is preserved as clean commits through `{head_short}`, rather than as an uncommitted sandbox delta."
        )
        publish_boundary_line = (
            "- The check-gate hardening bundle is now preserved as a clean local commit instead of only a dirty working tree, "
            "so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens."
        )
        boundary_dirty_line = "- the local sandbox currently carries no additional uncommitted verifier-hardening delta"

    boundary_text = DOC_BOUNDARY.read_text(encoding="utf-8")
    boundary_text = re.sub(
        r"- the local hardening stack is currently ahead of that public ref through `[^`]+` \(`[^`]+`\), \d+ commits ahead in total",
        f"- the local hardening stack is currently ahead of that public ref through `{head_short}` (`{head_subject}`), {ahead_count} commits ahead in total",
        boundary_text,
        count=1,
    )
    if re.search(r"- the local sandbox currently (?:also carries \d+ uncommitted verifier-hardening path\(s\) beyond HEAD \([^\n]+\)|carries no additional uncommitted verifier-hardening delta)", boundary_text):
        boundary_text = re.sub(
            r"- the local sandbox currently (?:also carries \d+ uncommitted verifier-hardening path\(s\) beyond HEAD \([^\n]+\)|carries no additional uncommitted verifier-hardening delta)",
            boundary_dirty_line,
            boundary_text,
            count=1,
        )
    else:
        boundary_text = re.sub(
            r"(- the local hardening stack is currently ahead of that public ref through `[^`]+` \(`[^`]+`\), \d+ commits ahead in total\n)",
            lambda m: m.group(1) + boundary_dirty_line + "\n",
            boundary_text,
            count=1,
        )
    DOC_BOUNDARY.write_text(boundary_text, encoding="utf-8")

    checkpoint_text = DOC_CHECKPOINT.read_text(encoding="utf-8")
    checkpoint_text = re.sub(r"- GitHub-visible branch head: `[^`]+`", f"- GitHub-visible branch head: `{upstream_short}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(r"- Latest local head in the stack: `[^`]+`", f"- Latest local head in the stack: `{head_short}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(r"- Latest non-doc logic head in the local stack: `[^`]+`", f"- Latest non-doc logic head in the local stack: `{latest_non_doc}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(r"- Local branch state at checkpoint: ahead by \d+ commits over the GitHub-visible branch head", f"- Local branch state at checkpoint: ahead by {ahead_count} commits over the GitHub-visible branch head", checkpoint_text, count=1)
    checkpoint_text = re.sub(
        r"(## Local commit stack after `[^`]+`\n)(.*?)(\n## What is now true locally)",
        lambda m: m.group(1) + commit_lines + m.group(3),
        checkpoint_text,
        count=1,
        flags=re.S,
    )
    checkpoint_text = re.sub(
        r"- The check-gate hardening bundle is (?:now preserved as a clean local commit instead of only a dirty working tree, so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens|no longer only a clean-commit story: the commit stack is preserved, but the current sandbox also carries additional uncommitted verifier-hardening delta)\.",
        publish_boundary_line,
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"- The current local hardening stack is (?:preserved as clean commits through `[^`]+`, rather than as an uncommitted sandbox delta|not fully committed: HEAD is `[^`]+` and the working tree still carries \d+ uncommitted path\(s\) \([^\n]+\))\.",
        preservation_line,
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"1\. Make the current local branch tip GitHub-visible \(the latest non-doc logic commit in that tip is `[^`]+`\)\.",
        f"1. Make the current local branch tip GitHub-visible (the latest non-doc logic commit in that tip is `{latest_non_doc}`).",
        checkpoint_text,
        count=1,
    )
    DOC_CHECKPOINT.write_text(checkpoint_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
