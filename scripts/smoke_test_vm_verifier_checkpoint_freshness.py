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
    shutil.copy2(REFRESH_HELPER, work / "scripts" / REFRESH_HELPER.name)
    shutil.copy2(FRESHNESS_CHECKER, work / "scripts" / FRESHNESS_CHECKER.name)
    (work / ".gitignore").write_text("ci-artifacts/\n", encoding="utf-8")
    (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").write_text(
        "Current known boundary on this branch family:\n"
        "- GitHub-visible branch head remains `oldhead`\n"
        "- the local hardening stack is currently ahead of that public ref through `oldsha` (`old subject`), 0 commits ahead in total\n"
        "- the latest non-doc logic delta in that local stack is the placeholder publish-boundary bundle in:\n"
        "  - `old/path.py`\n",
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
        fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in fresh_output

        commit_candidate = work / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"
        current_head_short = run(["git", "rev-parse", "--short", "HEAD"], work)
        current_head_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
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
                "- Make local checkpoint ",
                "- Make stale local checkpoint ",
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
        assert "Commit-candidate branch state is stale; expected to find:" in stale_doc_only_output

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
                "- Make the current branch tip ",
                "- Make the stale branch tip ",
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
        boundary_text = boundary_doc.read_text(encoding="utf-8")
        boundary_doc.write_text(
            boundary_text.replace(
                f"- the latest non-doc logic delta in that local stack is `{run(['git', 'rev-parse', '--short', 'HEAD^'], work)}` (`tests: add logic commit`) in:\n",
                "- the latest non-doc logic delta in that local stack is `wrongsha` (`wrong subject`) in:\n",
                1,
            ),
            encoding="utf-8",
        )
        stale_boundary_head_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Boundary doc latest non-doc head is stale; expected to find:" in stale_boundary_head_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        boundary_text = boundary_doc.read_text(encoding="utf-8")
        boundary_doc.write_text(
            boundary_text.replace(
                "- `logic.txt`\n",
                "- `wrong-path.txt`\n",
                1,
            ),
            encoding="utf-8",
        )
        stale_boundary_output = expect_fail(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "Boundary doc latest non-doc paths is stale; expected to find:" in stale_boundary_output

        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        boundary_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in boundary_fresh_output

        run(["git", "push", "origin", "HEAD:fix/openclaw-config-path-and-local-mode"], work)
        run_ok(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], work)
        aligned_fresh_output = run_ok(["python3", "-B", "scripts/check_vm_verifier_checkpoint_freshness.py"], work)
        assert "[PASS] VM verifier checkpoint artifacts match current repo state" in aligned_fresh_output

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
