#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REFRESH_HELPER = REPO_ROOT / "scripts" / "refresh_vm_verifier_checkpoint_state.py"
FRESHNESS_CHECKER = REPO_ROOT / "scripts" / "check_vm_verifier_checkpoint_freshness.py"


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def run_ok(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise AssertionError(
            f"Expected success but command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout + result.stderr


def expect_fail(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"Expected failure but command succeeded: {' '.join(cmd)}")
    return result.stdout + result.stderr


def seed_repo(work: Path) -> None:
    (work / "docs").mkdir(parents=True)
    (work / "scripts").mkdir(parents=True)
    (work / "ci-artifacts" / "bootstrap-preflight").mkdir(parents=True)
    (work / "ci-artifacts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REFRESH_HELPER, work / "scripts" / REFRESH_HELPER.name)
    shutil.copy2(FRESHNESS_CHECKER, work / "scripts" / FRESHNESS_CHECKER.name)
    (work / ".gitignore").write_text("ci-artifacts/\n", encoding="utf-8")
    (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").write_text(
        "Current known boundary on this branch family:\n"
        "- treat the published GitHub-visible ref as the VM-proof boundary and re-check the exact branch/commit state locally before any live verifier run\n"
        "- the local sandbox may carry additional ahead-of-published commits and uncommitted publish-boundary maintenance delta, so confirm with `git status --short --branch` before assuming the current tip is publishable\n"
        "- the latest wrapper hardening keeps explicit GitHub remote-tracking refs such as `refs/remotes/github/fix/openclaw-config-path-and-local-mode` intact through the dry-run preflight path and into `scripts/check_github_check_gate.py`\n"
        "- that same wrapper now normalizes explicit GitHub remote-tracking refs down to a GitHub-visible branch name for the final `scripts/vm/verify_bootstrap_in_vm.sh` handoff, so the operator-facing next step stays runnable\n",
        encoding="utf-8",
    )
    (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").write_text(
        (
            "# Bootstrap VM Verifier Checkpoint — 2026-06-15\n\n"
            "## Branch\n"
            "- Working branch: `fix/openclaw-config-path-and-local-mode`\n"
            "- GitHub-visible branch head: `oldhead`\n"
            "- Latest local head in the stack: `oldsha`\n"
            "- Latest non-doc logic head in the local stack: `oldlogic`\n"
            "- Local branch state at checkpoint: ahead by 0 commits over the GitHub-visible branch head\n\n"
            "## Local commit stack after `oldhead`\n"
            "1. `oldsha` — `old subject`\n\n"
            "## What is now true locally\n"
            "- The current local hardening stack is preserved as clean commits through `oldsha`, rather than as an uncommitted sandbox delta.\n"
            "- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.\n"
            "- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.\n"
            "- Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place.\n"
            "- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.\n"
        ),
        encoding="utf-8",
    )
    (work / "ci-artifacts" / "vm-verifier-checkpoint-latest.md").write_text(
        (
            "# Bootstrap VM Verifier Checkpoint — 2026-06-15\n\n"
            "## Branch\n"
            "- Working branch: `fix/openclaw-config-path-and-local-mode`\n"
            "- GitHub-visible branch head: `oldhead`\n"
            "- Latest local head in the stack: `oldsha`\n"
            "- Latest non-doc logic head in the local stack: `oldlogic`\n"
            "- Local branch state at checkpoint: ahead by 0 commits over the GitHub-visible branch head\n\n"
            "## Local commit stack after `oldhead`\n"
            "1. `oldsha` — `old subject`\n\n"
            "## What is now true locally\n"
            "- The current local hardening stack is preserved as clean commits through `oldsha`, rather than as an uncommitted sandbox delta.\n"
            "- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.\n"
            "- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.\n"
            "- Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place.\n"
            "- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.\n"
        ),
        encoding="utf-8",
    )
    (work / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt").write_text(
        "Commit candidate: placeholder candidate fixture\n"
        "Current local checkpoint: oldsha\n"
        "Current branch state: ahead 0 over fix/openclaw-config-path-and-local-mode\n",
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="unifai-vm-checkpoint-freshness-") as tmp:
        root = Path(tmp)
        remote = root / "remote.git"
        work = root / "work"

        subprocess.check_call(["git", "init", "--bare", str(remote)])
        subprocess.check_call(["git", "clone", str(remote), str(work)])
        run(["git", "config", "user.name", "Little7 Smoke Test"], work)
        run(["git", "config", "user.email", "little7@example.invalid"], work)
        seed_repo(work)
        run(["git", "add", "."], work)
        run(["git", "commit", "-m", "docs: seed checkpoint templates"], work)
        run(["git", "branch", "-M", "fix/openclaw-config-path-and-local-mode"], work)
        run(["git", "push", "-u", "origin", "fix/openclaw-config-path-and-local-mode"], work)

        (work / "logic.txt").write_text("logic\n", encoding="utf-8")
        run(["git", "add", "logic.txt"], work)
        run(["git", "commit", "-m", "tests: add logic commit"], work)

        stale_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "is stale; expected to find:" in stale_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        current_head_short = run(["git", "rev-parse", "--short", "HEAD"], work)
        current_head_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
        fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in fresh_output

        latest_checkpoint = work / "ci-artifacts" / "vm-verifier-checkpoint-latest.md"
        commit_candidate_doc = work / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"
        latest_checkpoint_text = latest_checkpoint.read_text(encoding="utf-8")
        latest_checkpoint.write_text(
            latest_checkpoint_text.replace(
                "- Latest tracked local head in the stack: `",
                "- Latest tracked local head in the stack: `stale-",
                1,
            ),
            encoding="utf-8",
        )
        stale_latest_checkpoint_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Checkpoint latest tracked head is stale; expected to find:" in stale_latest_checkpoint_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        boundary_doc = work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"
        checkpoint_doc = work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"
        checkpoint_text = checkpoint_doc.read_text(encoding="utf-8")
        stale_checkpoint_duplicate_delta = (
            "- The current local sandbox now carries no additional uncommitted publish-boundary maintenance delta beyond the tracked local stack represented here.\n"
        )
        checkpoint_doc.write_text(checkpoint_text + stale_checkpoint_duplicate_delta, encoding="utf-8")
        stale_checkpoint_duplicate_delta_output = expect_fail(
            ["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work
        )
        assert "Checkpoint doc current-delta block is stale; expected exactly one line starting with:" in stale_checkpoint_duplicate_delta_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        checkpoint_text = checkpoint_doc.read_text(encoding="utf-8")
        checkpoint_lines = checkpoint_text.splitlines()
        delta_index = checkpoint_lines.index(
            "- The current local sandbox now carries 2 uncommitted publish-boundary maintenance updates beyond the tracked local stack:"
        )
        duplicated_bullets = checkpoint_lines[delta_index + 1 : delta_index + 3]
        checkpoint_lines[delta_index:delta_index] = duplicated_bullets
        checkpoint_doc.write_text("\n".join(checkpoint_lines) + "\n", encoding="utf-8")
        stale_checkpoint_delta_section_output = expect_fail(
            ["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work
        )
        assert "Checkpoint doc pre-delta bullet drift is stale; unexpected lines before the current-delta block:" in stale_checkpoint_delta_section_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate_doc.read_text(encoding="utf-8")
        commit_candidate_lines = commit_candidate_text.splitlines()
        worktree_start = commit_candidate_lines.index("Working-tree files:") + 1
        worktree_end = commit_candidate_lines.index("", worktree_start)
        replacement_line = "docs/BOOTSTRAP_VM_VERIFICATION.md"
        if commit_candidate_lines[worktree_start] == replacement_line:
            replacement_line = "scripts/not-real-drift.py"
        commit_candidate_lines[worktree_start] = replacement_line
        commit_candidate_doc.write_text("\n".join(commit_candidate_lines) + "\n", encoding="utf-8")
        stale_commit_candidate_worktree_output = expect_fail(
            ["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work
        )
        assert "Commit-candidate working-tree block is stale; expected exact block:" in stale_commit_candidate_worktree_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        boundary_text = boundary_doc.read_text(encoding="utf-8")
        latest_checkpoint_text = latest_checkpoint.read_text(encoding="utf-8")
        latest_checkpoint.write_text(latest_checkpoint_text + "\nextra drift\n", encoding="utf-8")
        stale_latest_checkpoint_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Checkpoint latest handoff artifact diverges from the dated checkpoint doc." in stale_latest_checkpoint_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        boundary_doc.write_text(
            boundary_text + f"\n- the current checked-out branch tip is `{current_head_short}` (`{current_head_subject}`)\n",
            encoding="utf-8",
        )
        unexpected_head_boundary_tip_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "boundary doc checked-out tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_boundary_tip_output

        boundary_doc.write_text(boundary_text, encoding="utf-8")
        checkpoint_text = checkpoint_doc.read_text(encoding="utf-8")
        latest_checkpoint_text = latest_checkpoint.read_text(encoding="utf-8")
        checkpoint_doc.write_text(
            checkpoint_text + f"\n- Current checked-out branch tip: `{current_head_short}` (`{current_head_subject}`)\n",
            encoding="utf-8",
        )
        latest_checkpoint.write_text(
            latest_checkpoint_text + f"\n- Current checked-out branch tip: `{current_head_short}` (`{current_head_subject}`)\n",
            encoding="utf-8",
        )
        unexpected_head_checkpoint_tip_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "checkpoint doc checked-out tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_checkpoint_tip_output

        checkpoint_doc.write_text(checkpoint_text, encoding="utf-8")
        latest_checkpoint.write_text(latest_checkpoint_text, encoding="utf-8")
        commit_candidate = commit_candidate_doc
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "Current branch state: ahead 1 over fix/openclaw-config-path-and-local-mode\n",
                f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\n"
                "Current branch state: ahead 1 over fix/openclaw-config-path-and-local-mode\n",
                1,
            ),
            encoding="utf-8",
        )
        unexpected_head_tip_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "commit-candidate tip line should not be present when the tracked checkpoint is HEAD." in unexpected_head_tip_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- The branch still needs the local checkpoint chain through ",
                "- The branch still needs the stale checkpoint chain through ",
                1,
            ),
            encoding="utf-8",
        )
        stale_head_blocker_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate external blocker is stale; expected to find:" in stale_head_blocker_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make local checkpoint ",
                "- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make stale local checkpoint ",
                1,
            ),
            encoding="utf-8",
        )
        stale_head_move_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate next move is stale; expected to find:" in stale_head_move_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `",
                "- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `stale-",
                1,
            ),
            encoding="utf-8",
        )
        stale_head_public_blocker_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate public blocker note is stale; expected to find:" in stale_head_public_blocker_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        run(["git", "add", "docs/BOOTSTRAP_VM_VERIFICATION.md", "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"], work)
        run(["git", "commit", "-m", "docs: refresh visible verifier boundary state"], work)

        stale_doc_only_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "is stale; expected to find:" in stale_doc_only_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        doc_only_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in doc_only_fresh_output

        doc_only_ahead = run(["git", "rev-list", "--count", "origin/fix/openclaw-config-path-and-local-mode..HEAD"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                f"Current branch state: ahead {doc_only_ahead} over fix/openclaw-config-path-and-local-mode\n",
                "Current branch state: ahead stale over fix/openclaw-config-path-and-local-mode\n",
                1,
            ),
            encoding="utf-8",
        )
        stale_doc_only_branch_state_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate branch state is stale; expected to find:" in stale_doc_only_branch_state_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "Current checked-out branch tip: ",
                "Current checked-out branch tip: stale ",
                1,
            ),
            encoding="utf-8",
        )
        stale_doc_only_tip_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate checked-out tip is stale; expected to find:" in stale_doc_only_tip_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- The branch still needs the current branch tip ",
                "- The branch still needs the stale branch tip ",
                1,
            ),
            encoding="utf-8",
        )
        stale_doc_only_blocker_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate external blocker is stale; expected to find:" in stale_doc_only_blocker_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip ",
                "- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make the stale branch tip ",
                1,
            ),
            encoding="utf-8",
        )
        stale_doc_only_move_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate next move is stale; expected to find:" in stale_doc_only_move_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `",
                "- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `stale-",
                1,
            ),
            encoding="utf-8",
        )
        stale_public_blocker_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate public blocker note is stale; expected to find:" in stale_public_blocker_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        boundary_doc = work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"
        boundary_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in boundary_fresh_output

        run(["git", "push", "origin", "HEAD:fix/openclaw-config-path-and-local-mode"], work)
        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        aligned_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in aligned_fresh_output

        run(["git", "remote", "rename", "origin", "github"], work)
        run(
            ["git", "branch", "--set-upstream-to=github/fix/openclaw-config-path-and-local-mode"],
            work,
        )
        run(["git", "checkout", "-B", "docs-only-tip-needs-publish"], work)
        run(
            ["git", "branch", "--set-upstream-to=github/fix/openclaw-config-path-and-local-mode"],
            work,
        )
        (work / "docs" / "github-remote-freshness.md").write_text("github remote doc-only tip\n", encoding="utf-8")
        run(["git", "add", "docs/github-remote-freshness.md"], work)
        run(["git", "commit", "-m", "docs: add github-remote freshness tip"], work)
        github_remote_tip = run(["git", "rev-parse", "--short", "HEAD"], work)
        github_remote_tip_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        github_remote_unpublished_commit_candidate = commit_candidate.read_text(encoding="utf-8")
        assert f"Current checked-out branch tip: {github_remote_tip} ({github_remote_tip_subject})\n" in github_remote_unpublished_commit_candidate
        assert (
            f"- Run `git push github HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{github_remote_tip}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{current_head_short}` until a non-doc commit supersedes it.\n"
        ) in github_remote_unpublished_commit_candidate
        github_remote_unpublished_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in github_remote_unpublished_fresh_output

        run(["git", "push", "github", "HEAD:fix/openclaw-config-path-and-local-mode"], work)
        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        github_remote_aligned_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in github_remote_aligned_fresh_output

        boundary_text = boundary_doc.read_text(encoding="utf-8")
        boundary_doc.write_text(
            boundary_text + f"\n- the current checked-out branch tip is `{github_remote_tip}` (`{github_remote_tip_subject}`)\n",
            encoding="utf-8",
        )
        aligned_boundary_tip_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "boundary doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible." in aligned_boundary_tip_output

        boundary_doc.write_text(boundary_text, encoding="utf-8")
        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        checkpoint_doc = work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"
        checkpoint_text = checkpoint_doc.read_text(encoding="utf-8")
        latest_checkpoint_text = latest_checkpoint.read_text(encoding="utf-8")
        checkpoint_doc.write_text(
            checkpoint_text + f"\n- Current checked-out branch tip: `{github_remote_tip}` (`{github_remote_tip_subject}`)\n",
            encoding="utf-8",
        )
        latest_checkpoint.write_text(
            latest_checkpoint_text + f"\n- Current checked-out branch tip: `{github_remote_tip}` (`{github_remote_tip_subject}`)\n",
            encoding="utf-8",
        )
        aligned_checkpoint_tip_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "checkpoint doc checked-out tip line should stay out of tracked docs after the doc-only tip becomes visible." in aligned_checkpoint_tip_output

        checkpoint_doc.write_text(checkpoint_text, encoding="utf-8")
        latest_checkpoint.write_text(latest_checkpoint_text, encoding="utf-8")
        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "Current branch state: ahead 0 over fix/openclaw-config-path-and-local-mode\n",
                "Current branch state: ahead stale over fix/openclaw-config-path-and-local-mode\n",
                1,
            ),
            encoding="utf-8",
        )
        aligned_doc_only_branch_state_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate branch state is stale; expected to find:" in aligned_doc_only_branch_state_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "- The exact branch tip `",
                "- The stale exact branch tip `",
                1,
            ),
            encoding="utf-8",
        )
        aligned_doc_only_blocker_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate external blocker is stale; expected to find:" in aligned_doc_only_blocker_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        commit_candidate_text = commit_candidate.read_text(encoding="utf-8")
        commit_candidate.write_text(
            commit_candidate_text.replace(
                "rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `",
                "rerun stale visible-ref work while the tracked publish-boundary checkpoint remains `",
                1,
            ),
            encoding="utf-8",
        )
        aligned_doc_only_move_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Commit-candidate next move is stale; expected to find:" in aligned_doc_only_move_output

    print("[PASS] VM verifier checkpoint freshness smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
