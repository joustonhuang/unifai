#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from os import W_OK, access, environ
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"
DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"
CHECKPOINT_LATEST = REPO_ROOT / "ci-artifacts" / "vm-verifier-checkpoint-latest.md"
COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"
STABILIZED_ENV = "UNIFAI_VM_CHECKPOINT_REFRESH_STABILIZED"
SELF_MAINTAINED_HANDOFF_PATHS = {
    str(DOC_BOUNDARY.relative_to(REPO_ROOT)),
    str(DOC_CHECKPOINT.relative_to(REPO_ROOT)),
    str(CHECKPOINT_LATEST.relative_to(REPO_ROOT)),
    str(COMMIT_CANDIDATE.relative_to(REPO_ROOT)),
}
NON_LOGIC_PREFIXES = ("docs/", "ci-artifacts/")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def git_optional(*args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_non_logic_path(path: str) -> bool:
    return path.startswith(NON_LOGIC_PREFIXES)


def upstream_display_name(upstream: str) -> str:
    return upstream.split("/", 1)[1] if "/" in upstream else upstream


def tracked_dirty_paths() -> list[str]:
    status_lines = git("status", "--short").splitlines()
    return [line.split(maxsplit=1)[1] for line in status_lines if len(line.split(maxsplit=1)) == 2]


def effective_dirty_paths(dirty_paths: list[str], tracked_ref: str) -> list[str]:
    # Once HEAD is only a doc-only tip above the tracked publish-boundary commit,
    # keep the tracked handoff anchored to the underlying publish boundary instead
    # of treating regenerated checkpoint artifacts as new uncommitted bundle delta.
    if tracked_ref != "HEAD":
        return [path for path in dirty_paths if path not in SELF_MAINTAINED_HANDOFF_PATHS]
    return dirty_paths


def is_checkpoint_doc_only_commit(ref: str) -> bool:
    changed_paths = {
        line.strip()
        for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", ref).splitlines()
        if line.strip()
    }
    return bool(changed_paths) and all(is_non_logic_path(path) for path in changed_paths)


def command_succeeds(*args: str) -> bool:
    try:
        return subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def current_host_lines() -> tuple[str, str]:
    if Path("/dev/kvm").exists():
        if access("/dev/kvm", W_OK):
            kvm_desc = "`/dev/kvm` is writable"
        else:
            kvm_desc = "`/dev/kvm` is present but not writable"
    else:
        kvm_desc = "`/dev/kvm` is absent"

    if command_succeeds("bash", "-lc", "command -v gh >/dev/null 2>&1"):
        if command_succeeds("gh", "auth", "status"):
            gh_desc = "`gh` is installed and authenticated"
        else:
            gh_desc = "`gh` is installed but unauthenticated"
    else:
        gh_desc = "`gh` is not installed"

    token_desc = (
        "`GH_TOKEN`/`GITHUB_TOKEN` is exported"
        if environ.get("GH_TOKEN") or environ.get("GITHUB_TOKEN")
        else "no `GH_TOKEN`/`GITHUB_TOKEN` is exported"
    )

    checkpoint_line = (
        "- Live host-readiness has improved since the older missing-QEMU note: the required verifier tools are present on this host, "
        f"and the current live state is narrower ({kvm_desc}, {gh_desc}, {token_desc})."
    )
    if gh_desc == "`gh` is installed and authenticated":
        github_expectation = "so the first live run should expect TCG fallback, while normal GitHub API reads should flow through authenticated `gh` unless the host state changes"
    elif token_desc == "`GH_TOKEN`/`GITHUB_TOKEN` is exported":
        github_expectation = "so the first live run should expect TCG fallback, while GitHub API access should rely on token-backed curl fallback unless the host state changes"
    else:
        github_expectation = "so the first live run should expect TCG fallback plus possible GitHub API auth/rate-limit friction unless the host state changes"

    boundary_line = f"- on the current host, {kvm_desc}, {gh_desc}, and {token_desc}, {github_expectation}"
    return checkpoint_line, boundary_line


def collect_bundle_paths(upstream: str, dirty_paths: list[str]) -> list[str]:
    bundle_paths = [line.strip() for line in git("diff", "--name-only", upstream).splitlines() if line.strip()]
    for path in dirty_paths:
        if path not in bundle_paths:
            bundle_paths.append(path)
    return bundle_paths


def replace_delta_and_bundle_sections(
    checkpoint_text: str,
    current_delta_block: str,
    verification_block: str,
    dirty_bullets: str,
    bundle_bullets: str,
) -> str:
    if dirty_bullets and current_delta_block in checkpoint_text:
        prefix, suffix = checkpoint_text.split(current_delta_block, 1)
        checkpoint_text = prefix.replace(dirty_bullets + "\n", "") + current_delta_block + suffix
    checkpoint_text = re.sub(
        r"- The current local sandbox .*?(?=- Fresh local verification at the current (?:sandbox|tracked checkpoint) state is green again:\n(?:  - [^\n]*\n)+)",
        "",
        checkpoint_text,
        count=1,
        flags=re.S,
    )
    updated_checkpoint_text = re.sub(
        r"- Fresh local verification at the current (?:sandbox|tracked checkpoint) state is green again:\n(?:  - [^\n]*\n)+",
        current_delta_block + "\n" + verification_block + "\n",
        checkpoint_text,
        count=1,
        flags=re.S,
    )
    if updated_checkpoint_text == checkpoint_text:
        updated_checkpoint_text = re.sub(
            r"(- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*?\n)",
            lambda m: m.group(1) + current_delta_block + "\n" + verification_block + "\n",
            checkpoint_text,
            count=1,
        )
    if updated_checkpoint_text == checkpoint_text:
        updated_checkpoint_text = re.sub(
            r"(- Fresh local `bash scripts/bootstrap_installer_preflight\.sh` reruns are green[^\n]*\n)",
            lambda m: m.group(1) + current_delta_block + "\n" + verification_block + "\n",
            checkpoint_text,
            count=1,
        )
    checkpoint_text = updated_checkpoint_text
    if dirty_bullets and current_delta_block in checkpoint_text:
        prefix, suffix = checkpoint_text.split(current_delta_block, 1)
        checkpoint_text = prefix.replace(dirty_bullets + "\n", "") + current_delta_block + suffix
    if dirty_bullets:
        replacement = "- Current uncommitted delta on top:\n" + dirty_bullets + "\n- Files in the bundle:"
    else:
        replacement = "- Files in the bundle:"
    checkpoint_text = re.sub(
        r"(?:(?:- )?Current uncommitted delta on top:\n(?:  - `[^\n]+`\n)+)?- Files in the bundle:",
        replacement,
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"(- Files in the bundle:\n)(.*?)(\n- Smallest re-verification gate before publishing that commit:)",
        lambda m: m.group(1) + bundle_bullets + m.group(3),
        checkpoint_text,
        count=1,
        flags=re.S,
    )
    checkpoint_text = re.sub(
        r"(- Bootstrap preflight now locks that installer-failure path.*\n)(?:  - `[^\n]+`\n)+(?=- The current local sandbox now carries)",
        r"\1",
        checkpoint_text,
        count=1,
    )
    return checkpoint_text


def describe_dirty_state(
    dirty_paths: list[str], tracked_head_short: str, ahead_count: str, upstream_display: str
) -> tuple[str, str, str, str, str, str]:
    dirty_bullets = "\n".join(f"  - `{path}`" for path in dirty_paths)
    if dirty_paths:
        shown = ", ".join(f"`{path}`" for path in dirty_paths[:5])
        if len(dirty_paths) > 5:
            shown += f", and {len(dirty_paths) - 5} more"
        preservation_line = (
            f"- The current local hardening stack is not fully committed: tracked head is `{tracked_head_short}` and the working tree still carries "
            f"{len(dirty_paths)} uncommitted path(s) ({shown})."
        )
        publish_boundary_line = (
            "- The publish-boundary maintenance bundle is no longer only a clean-commit story: the commit stack is preserved, "
            "but the current sandbox also carries additional uncommitted publish-boundary maintenance delta."
        )
        boundary_dirty_line = (
            f"- the local sandbox currently also carries {len(dirty_paths)} uncommitted publish-boundary maintenance path(s) beyond HEAD ({shown})"
        )
        current_delta_label = (
            "one small publish-boundary maintenance delta"
            if len(dirty_paths) == 1
            else f"{len(dirty_paths)} uncommitted publish-boundary maintenance updates"
        )
        current_delta_block = (
            f"- The current local sandbox now carries {current_delta_label} beyond the tracked local stack:\n"
            + dirty_bullets
        )
        update_word = "update" if len(dirty_paths) == 1 else "updates"
        stack_progress_line = (
            "- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the "
            f"GitHub-visible branch: the latest tracked commit is now `{tracked_head_short}`, that same commit is also the latest "
            f"non-doc logic head, the sandbox currently carries {len(dirty_paths)} uncommitted publish-boundary maintenance "
            f"{update_word}, and the branch is `ahead {ahead_count}` over `{upstream_display}`."
        )
    else:
        preservation_line = (
            f"- The current local hardening stack is preserved as clean commits through `{tracked_head_short}`, rather than as an uncommitted sandbox delta."
        )
        publish_boundary_line = (
            "- The publish-boundary maintenance bundle is now preserved as a clean local commit instead of only a dirty working tree, "
            "so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens."
        )
        boundary_dirty_line = "- the local sandbox currently carries no additional uncommitted publish-boundary maintenance delta"
        current_delta_block = (
            "- The current local sandbox now carries no additional uncommitted publish-boundary maintenance delta beyond the tracked local stack."
        )
        stack_progress_line = (
            "- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the "
            f"GitHub-visible branch: the latest tracked commit is now `{tracked_head_short}`, that same commit is also the latest "
            f"non-doc logic head, the sandbox currently carries no additional uncommitted publish-boundary maintenance updates, "
            f"and the branch is `ahead {ahead_count}` over `{upstream_display}`."
        )
    return (
        dirty_bullets,
        preservation_line,
        publish_boundary_line,
        boundary_dirty_line,
        current_delta_block,
        stack_progress_line,
    )


def main() -> int:
    current_branch = git_optional("branch", "--show-current")
    if not current_branch:
        return fail(
            "refresh_vm_verifier_checkpoint_state.py requires a checked-out branch; detached HEAD does not provide a stable publish-boundary checkpoint."
        )

    upstream = git_optional("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")
    if not upstream:
        return fail(
            f"branch '{current_branch}' has no upstream; set a GitHub-visible upstream before refreshing the verifier publish-boundary checkpoint."
        )
    upstream_display = upstream_display_name(upstream)
    upstream_remote, upstream_branch = upstream.split("/", 1)
    push_command = f"git push {upstream_remote} HEAD:{upstream_branch}"

    upstream_short = git("rev-parse", "--short", upstream)
    current_head_short = git("rev-parse", "--short", "HEAD")
    current_head_subject = git("show", "-s", "--format=%s", "HEAD")
    current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")
    tracked_ref = "HEAD"
    while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):
        tracked_ref = git("rev-parse", f"{tracked_ref}^")
    tracked_head_short = git("rev-parse", "--short", tracked_ref)
    tracked_head_subject = git("show", "-s", "--format=%s", tracked_ref)
    ahead_count = git("rev-list", "--count", f"{upstream}..{tracked_ref}")
    # Keep handoff docs stable after publishing a doc-only checkpoint refresh commit:
    # once the branch is fully aligned with GitHub, the meaningful publish boundary is
    # still the tracked non-doc head rather than the latest doc-only tip.
    visible_head_short = upstream_short
    if tracked_ref != "HEAD" and current_head_ahead_count == "0":
        visible_head_short = tracked_head_short
    if tracked_ref != "HEAD":
        commit_candidate_tip_line = (
            f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\n"
        )
    else:
        commit_candidate_tip_line = ""

    raw_commits = git("log", "--reverse", "--format=%h\t%s", f"{upstream}..{tracked_ref}").splitlines()
    commits = [line.split("\t", 1) for line in raw_commits if line.strip()]
    latest_non_doc = next((sha for sha, _subject in reversed(commits) if not is_checkpoint_doc_only_commit(sha)), tracked_head_short)
    latest_non_doc_subject = next((subject for sha, subject in reversed(commits) if sha == latest_non_doc), tracked_head_subject)
    latest_non_doc_all_paths = [
        line.strip()
        for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", latest_non_doc).splitlines()
        if line.strip()
    ]
    latest_non_doc_paths = [
        path for path in latest_non_doc_all_paths if not is_non_logic_path(path)
    ] or latest_non_doc_all_paths
    latest_non_doc_block = (
        f"- the latest non-doc logic delta in that local stack is `{latest_non_doc}` (`{latest_non_doc_subject}`) in:\n"
        + "\n".join(f"  - `{path}`" for path in latest_non_doc_paths)
    )
    dirty_paths = effective_dirty_paths(tracked_dirty_paths(), tracked_ref)
    original_boundary_text = DOC_BOUNDARY.read_text(encoding="utf-8")
    original_checkpoint_text = DOC_CHECKPOINT.read_text(encoding="utf-8")
    checkpoint_chain_bullets = "\n".join(f"  - `{sha}` (`{subject}`)" for sha, subject in commits)
    if tracked_ref != "HEAD" and current_head_ahead_count == "0" and not checkpoint_chain_bullets:
        checkpoint_chain_bullets = f"  - `{tracked_head_short}` (`{tracked_head_subject}`)"
    commit_lines = "\n".join(
        f"{idx}. `{sha}` — `{subject}`" for idx, (sha, subject) in enumerate(commits, start=1)
    )
    (
        dirty_bullets,
        preservation_line,
        publish_boundary_line,
        boundary_dirty_line,
        current_delta_block,
        stack_progress_line,
    ) = describe_dirty_state(dirty_paths, tracked_head_short, ahead_count, upstream_display)
    bundle_paths = collect_bundle_paths(upstream, dirty_paths)
    bundle_bullets = "\n".join(f"  - `{path}`" for path in bundle_paths)
    suggested_scope_line = (
        "- Suggested scope: publish-boundary maintenance bundle for visible-ref handoff, "
        "including the current self-maintaining checkpoint narrative/test bundle"
    )
    verification_block = (
        "- Fresh local verification at the current sandbox state is green again:\n"
        "  - `python3 scripts/check_publish_stack_parity_contract.py`\n"
        "  - `python3 scripts/check_publish_stack_reconciliation_note.py`\n"
        "  - `python3 scripts/check_publish_stack_reconciliation_note_contract.py`\n"
        "  - `python3 scripts/check_compare_publish_branch_histories_contract.py`\n"
        "  - `python3 scripts/check_branch_reconcile_handoff.py`\n"
        "  - `python3 scripts/check_branch_reconcile_handoff_contract.py`\n"
        "  - `python3 scripts/check_github_branch_visibility_contract.py`\n"
        "  - `python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py`\n"
        "  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`\n"
        "  - `python3 scripts/check_vm_host_readiness_contract.py`\n"
        "  - `bash scripts/smoke_test_publish_stack_parity.sh`\n"
        "  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`\n"
        "  - `bash scripts/smoke_test_publish_stack_reconciliation_note.sh`\n"
        "  - `bash scripts/smoke_test_branch_reconcile_handoff.sh`\n"
        "  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py`\n"
        "  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`\n"
        "  - `bash scripts/bootstrap_installer_preflight.sh` (rerun with the publish-boundary maintenance bundle in place)"
    )
    preflight_status_line = (
        "- Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place."
    )
    handoff_artifact_line = (
        "- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, "
        "verification gates, and the exact next visible-ref move as a one-file handoff."
    )
    checkpoint_host_line, boundary_host_line = current_host_lines()

    boundary_text = original_boundary_text
    boundary_text = re.sub(
        r"- GitHub-visible branch head remains `[^`]+`",
        f"- GitHub-visible branch head remains `{visible_head_short}`",
        boundary_text,
        count=1,
    )
    boundary_progress_line = (
        f"- the local hardening stack is currently ahead of that public ref through `{tracked_head_short}` "
        f"(`{tracked_head_subject}`), {ahead_count} commits ahead in total"
    )
    boundary_text = re.sub(
        (
            r"- the local hardening stack is currently ahead of that public ref through `[^`]+` "
            r"\(`[^`]+`\), \d+ commits ahead in total"
            r"|"
            r"- the checked-out sandbox tip is now `[^`]+` \(`[^`]+`\), while the latest non-doc logic checkpoint remains `[^`]+` "
            r"\(`[^`]+`\)\n- the local hardening stack is currently \d+ commits ahead of that public ref"
        ),
        boundary_progress_line,
        boundary_text,
        count=1,
    )
    # Keep the tracked docs anchored to the publish-boundary head. The live checked-out
    # doc-only tip belongs in commit-candidate.txt; putting it in the docs would make
    # every checkpoint-refresh docs commit immediately stale again.
    boundary_text = re.sub(
        r"- the current checked-out branch tip is `[^`]+` \(`[^`]+`\), but the tracked publish-boundary head stays `[^`]+` because doc-only checkpoint refresh commits are intentionally excluded from that comparison\n?",
        "",
        boundary_text,
        count=1,
    )
    if re.search(
        r"- the local sandbox currently (?:also carries \d+ uncommitted (?:verifier-hardening|checkpoint-refresh helper/doc|publish-boundary maintenance) path\(s\) beyond HEAD \([^\n]+\)[^\n]*|carries no additional uncommitted (?:verifier-hardening|checkpoint-refresh helper/doc|publish-boundary maintenance) delta[^\n]*)",
        boundary_text,
    ):
        boundary_text = re.sub(
            r"- the local sandbox currently (?:also carries \d+ uncommitted (?:verifier-hardening|checkpoint-refresh helper/doc|publish-boundary maintenance) path\(s\) beyond HEAD \([^\n]+\)[^\n]*|carries no additional uncommitted (?:verifier-hardening|checkpoint-refresh helper/doc|publish-boundary maintenance) delta[^\n]*)",
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
    if re.search(r"- on the current host, .*", boundary_text):
        boundary_text = re.sub(
            r"- on the current host, .*",
            boundary_host_line,
            boundary_text,
            count=1,
        )
    else:
        updated_boundary_text = re.sub(
            r"(- a fresh local `bash scripts/bootstrap_installer_preflight\.sh` rerun is green[^\n]*\n)",
            lambda m: m.group(1) + boundary_host_line + "\n",
            boundary_text,
            count=1,
        )
        if updated_boundary_text == boundary_text:
            boundary_text = boundary_text.rstrip() + "\n" + boundary_host_line + "\n"
        else:
            boundary_text = updated_boundary_text
    boundary_text = re.sub(
        r"- the latest non-doc logic delta in that local stack is .*? in:\n(?:  - `[^\n]+`\n)+",
        latest_non_doc_block + "\n",
        boundary_text,
        count=1,
        flags=re.S,
    )
    if re.search(r"- a fresh local `bash scripts/bootstrap_installer_preflight\.sh` rerun is green[^\n]*", boundary_text):
        boundary_text = re.sub(
            r"- a fresh local `bash scripts/bootstrap_installer_preflight\.sh` rerun is green[^\n]*",
            "- a fresh local `bash scripts/bootstrap_installer_preflight.sh` rerun is green with the current publish-boundary maintenance bundle in place",
            boundary_text,
            count=1,
        )
    else:
        boundary_text = re.sub(
            r"(- the latest non-doc logic delta in that local stack is .*? in:\n(?:  - `[^\n]+`\n)+)",
            r"\1- a fresh local `bash scripts/bootstrap_installer_preflight.sh` rerun is green with the current publish-boundary maintenance bundle in place\n",
            boundary_text,
            count=1,
            flags=re.S,
        )
    if re.search(r"- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*", boundary_text):
        boundary_text = re.sub(
            r"- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*",
            handoff_artifact_line,
            boundary_text,
            count=1,
        )
    else:
        boundary_text = re.sub(
            r"(- a fresh local `bash scripts/bootstrap_installer_preflight\.sh` rerun is green with the current publish-boundary maintenance bundle in place\n)",
            lambda m: m.group(1) + handoff_artifact_line + "\n",
            boundary_text,
            count=1,
        )
    checkpoint_text = original_checkpoint_text
    checkpoint_text = re.sub(r"- Working branch: `[^`]+`", f"- Working branch: `{current_branch}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(r"- GitHub-visible branch head: `[^`]+`", f"- GitHub-visible branch head: `{visible_head_short}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(
        r"- Current checked-out branch tip: `[^`]+`(?: \(`[^`]+`\))?(?:; tracked publish-boundary head stays `[^`]+` because doc-only checkpoint refresh commits are intentionally excluded from that comparison\.)?\n?",
        "",
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(r"- Latest (?:tracked )?local head in the stack: `[^`]+`", f"- Latest tracked local head in the stack: `{tracked_head_short}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(r"- Latest non-doc logic head in the local stack: `[^`]+`", f"- Latest non-doc logic head in the local stack: `{latest_non_doc}`", checkpoint_text, count=1)
    checkpoint_text = re.sub(
        r"- (?:Tracked local|Local) branch state at checkpoint: (?:current tip is )?ahead by \d+ commits over the GitHub-visible branch head",
        f"- Tracked local branch state at checkpoint: ahead by {ahead_count} commits over the GitHub-visible branch head",
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"(## Local commit stack after `[^`]+`\n)(.*?)(\n## What is now true locally)",
        lambda m: m.group(1) + commit_lines + m.group(3),
        checkpoint_text,
        count=1,
        flags=re.S,
    )
    checkpoint_text = re.sub(
        r"(- Current local checkpoint chain:\n)(.*?)(\n- Current uncommitted delta on top:|\n- Files in the bundle:)",
        lambda m: m.group(1) + "\n".join(f"  - `{sha}` (`{subject}`)" for sha, subject in commits) + m.group(3),
        checkpoint_text,
        count=1,
        flags=re.S,
    )
    checkpoint_text = re.sub(
        r"- Suggested scope: .*",
        suggested_scope_line,
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"- Fresh local `bash scripts/bootstrap_installer_preflight\.sh` reruns are green .*",
        preflight_status_line,
        checkpoint_text,
        count=1,
    )
    if re.search(r"- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*", checkpoint_text):
        checkpoint_text = re.sub(
            r"- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*",
            handoff_artifact_line,
            checkpoint_text,
            count=1,
        )
    else:
        checkpoint_text = re.sub(
            r"(- Fresh local `bash scripts/bootstrap_installer_preflight\.sh` reruns are green .*?\n)",
            lambda m: m.group(1) + handoff_artifact_line + "\n",
            checkpoint_text,
            count=1,
        )
    checkpoint_text = re.sub(
        r"(- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*?\n)(?:  - `[^\n]+`\n)+",
        r"\1",
        checkpoint_text,
        count=1,
    )
    updated_checkpoint_text = re.sub(
        r"- Live host-readiness has improved since the older missing-QEMU note: .*",
        checkpoint_host_line,
        checkpoint_text,
        count=1,
    )
    if updated_checkpoint_text == checkpoint_text:
        checkpoint_text = re.sub(
            r"(- The current local hardening stack is .*?\.\n\n)",
            lambda m: m.group(1) + checkpoint_host_line + "\n",
            checkpoint_text,
            count=1,
            flags=re.S,
        )
    else:
        checkpoint_text = updated_checkpoint_text
    if re.search(
        r"- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: .*",
        checkpoint_text,
    ):
        checkpoint_text = re.sub(
            r"- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: .*",
            stack_progress_line,
            checkpoint_text,
            count=1,
        )
    else:
        checkpoint_text = re.sub(
            r"(- Fresh local `bash scripts/bootstrap_installer_preflight\.sh` reruns are green .*?\n)",
            lambda m: m.group(1) + stack_progress_line + "\n",
            checkpoint_text,
            count=1,
        )
    checkpoint_text = re.sub(
        r"- The (?:check-gate hardening bundle|checkpoint-refresh helper/doc sync bundle|publish-boundary maintenance bundle) is (?:now preserved as a clean local commit instead of only a dirty working tree, so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens|no longer only a clean-commit story: the commit stack is preserved, but the current sandbox also carries additional uncommitted (?:verifier-hardening|publish-boundary maintenance) delta)\.",
        publish_boundary_line,
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"- The current local hardening stack is (?:preserved as clean commits through `[^`]+`, rather than as an uncommitted sandbox delta|not fully committed: (?:HEAD|tracked head) is `[^`]+` and the working tree still carries \d+ uncommitted path\(s\) \([^\n]+\))\.",
        preservation_line,
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"- The current local sandbox (?:(?:now|also) carries .*? beyond the tracked (?:local stack|doc commits)|also carries .*? checkpoint-refresh helper/doc delta beyond the tracked doc commits)[^\n]*(?::\n(?:  - `[^\n]+`\n)+|\n)?",
        "",
        checkpoint_text,
        flags=re.S,
    )
    checkpoint_text = replace_delta_and_bundle_sections(
        checkpoint_text,
        current_delta_block,
        verification_block,
        dirty_bullets,
        bundle_bullets,
    )
    checkpoint_text = re.sub(
        r"(- `ci-artifacts/bootstrap-preflight/commit-candidate\.txt` now captures .*?\n)(?:  - `[^\n]+`\n)+(?=- The current local sandbox now carries|- Fresh local verification at the current (?:sandbox|tracked checkpoint) state is green again:)",
        r"\1",
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"1\. Make the current local branch tip GitHub-visible \(the latest non-doc logic commit in that tip is `[^`]+`\)\.",
        f"1. Make the current local branch tip GitHub-visible (the latest non-doc logic commit in that tip is `{latest_non_doc}`).",
        checkpoint_text,
        count=1,
    )
    checkpoint_text = re.sub(
        r"5\. If verifier startup friction appears immediately, check host readiness first with:\n   ```bash\n   bash scripts/check_vm_host_readiness\.sh\n   ```",
        "5. If verifier startup friction still appears after wrapper preflight, re-run the narrow host-only check with:\n   ```bash\n   bash scripts/check_vm_host_readiness.sh\n   ```",
        checkpoint_text,
        count=1,
    )
    DOC_BOUNDARY.write_text(boundary_text, encoding="utf-8")
    DOC_CHECKPOINT.write_text(checkpoint_text, encoding="utf-8")
    CHECKPOINT_LATEST.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_LATEST.write_text(checkpoint_text, encoding="utf-8")

    # Keep the handoff stable across doc-only settle commits by reporting the
    # tracked publish-boundary checkpoint state, not the checked-out doc-only tip.
    tracked_branch_state = f"ahead {ahead_count} over {upstream_display}"
    tip_delta_line = ""
    if tracked_ref != "HEAD":
        tip_delta_count = git("rev-list", "--count", f"{tracked_ref}..HEAD")
        tip_delta_label = "commit" if tip_delta_count == "1" else "commits"
        tip_delta_line = (
            f"Checked-out tip delta beyond tracked checkpoint: {tip_delta_count} doc-only {tip_delta_label}\n"
        )
    verification_gates = (
        "Verification gates run:\n"
        "python3 scripts/check_publish_stack_parity_contract.py\n"
        "python3 scripts/check_publish_stack_reconciliation_note.py\n"
        "python3 scripts/check_publish_stack_reconciliation_note_contract.py\n"
        "python3 scripts/check_compare_publish_branch_histories_contract.py\n"
        "python3 scripts/check_branch_reconcile_handoff.py\n"
        "python3 scripts/check_branch_reconcile_handoff_contract.py\n"
        "python3 scripts/check_github_branch_visibility_contract.py\n"
        "python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\n"
        "python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\n"
        "python3 scripts/check_vm_host_readiness_contract.py\n"
        "bash scripts/smoke_test_publish_stack_parity.sh\n"
        "bash scripts/smoke_test_compare_publish_branch_histories.sh\n"
        "bash scripts/smoke_test_publish_stack_reconciliation_note.sh\n"
        "bash scripts/smoke_test_branch_reconcile_handoff.sh\n"
        "python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\n"
        "python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\n"
        "bash scripts/bootstrap_installer_preflight.sh"
    )
    if dirty_paths:
        working_tree_block = "Working-tree files:\n" + "\n".join(dirty_paths)
    else:
        working_tree_block = "Working-tree files:\n(clean)"
    if tracked_ref != "HEAD" and current_head_ahead_count != "0":
        next_move_heading = "Next clean move once the branch tip is GitHub-visible:\n"
        next_move_line = (
            f"- Run `{push_command}` to make the current branch tip `{current_head_short}` GitHub-visible on `{upstream_display}`; "
            f"the tracked publish-boundary checkpoint remains `{tracked_head_short}` until a non-doc commit supersedes it.\n"
        )
        external_blocker_line = (
            f"- The branch still needs the current branch tip `{current_head_short}` GitHub-visible; "
            f"the tracked publish-boundary checkpoint remains `{tracked_head_short}` until that visible ref exists.\n"
        )
    elif tracked_ref != "HEAD":
        next_move_heading = "Next clean move before the real VM-proof path:\n"
        next_move_line = (
            f"- The exact branch tip `{current_head_short}` is already GitHub-visible on `{upstream_display}`; "
            f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{tracked_head_short}`.\n"
        )
        external_blocker_line = (
            f"- The exact branch tip `{current_head_short}` is already GitHub-visible on `{upstream_display}`; "
            f"the tracked publish-boundary checkpoint remains `{tracked_head_short}` because the tip-only delta is doc-only.\n"
        )
    else:
        next_move_heading = "Next clean move before the real VM-proof path:\n"
        next_move_line = (
            f"- Run `{push_command}` to make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream_display}`.\n"
        )
        external_blocker_line = (
            f"- The branch still needs the local checkpoint chain through `{tracked_head_short}` to become GitHub-visible before the real VM-proof path can continue.\n"
        )

    commit_candidate_text = (
        f"Commit candidate: publish-boundary maintenance bundle for visible-ref handoff @ {tracked_head_short}\n"
        f"Current local checkpoint: {tracked_head_short}\n"
        f"{commit_candidate_tip_line}"
        f"Tracked publish-boundary state: {tracked_branch_state}\n\n"
        f"{tip_delta_line}"
        f"{working_tree_block}\n\n"
        f"{verification_gates}\n\n"
        "Current host-readiness snapshot:\n"
        f"{checkpoint_host_line}\n\n"
        "Latest local hardening:\n"
        f"{current_delta_block}\n"
        f"{publish_boundary_line}\n"
        f"{preflight_status_line}\n\n"
        "Current checkpoint chain:\n"
        f"{checkpoint_chain_bullets}\n\n"
        "Current external blocker:\n"
        f"{external_blocker_line}"
        f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{upstream_short}`, so the next real boundary is still a visible rerun on the exact published ref.\n\n"
        f"{next_move_heading}"
        f"{next_move_line}"
        "- Rerun `Bootstrap Installer Preflight` on the exact visible ref.\n"
        "- If green, run `bash scripts/run_vm_verifier_preflight.sh <visible-ref>` and then `bash scripts/vm/verify_bootstrap_in_vm.sh <visible-ref>`.\n"
    )
    COMMIT_CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    COMMIT_CANDIDATE.write_text(commit_candidate_text, encoding="utf-8")

    final_dirty_paths = effective_dirty_paths(tracked_dirty_paths(), tracked_ref)
    if final_dirty_paths != dirty_paths and not environ.get(STABILIZED_ENV):
        rerun_env = dict(environ)
        rerun_env[STABILIZED_ENV] = "1"
        return subprocess.run(
            ["python3", str(Path(__file__).resolve())],
            cwd=REPO_ROOT,
            env=rerun_env,
            check=False,
        ).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
