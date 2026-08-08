#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
from os import W_OK, access, environ
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / "scripts" / "refresh_vm_verifier_checkpoint_state.py"
FRESHNESS_CHECKER = REPO_ROOT / "scripts" / "check_vm_verifier_checkpoint_freshness.py"


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def extract_bundle_section(text: str) -> str:
    return text.split("- Files in the bundle:\n", 1)[1].split("- Smallest re-verification gate before publishing that commit:", 1)[0]


def read_commit_candidate(work: Path) -> str:
    return (work / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt").read_text(encoding="utf-8")


def read_latest_checkpoint(work: Path) -> str:
    return (work / "ci-artifacts" / "vm-verifier-checkpoint-latest.md").read_text(encoding="utf-8")


def expect_fail(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"Expected failure but command succeeded: {' '.join(cmd)}")
    return result.stdout + result.stderr


def run_ok(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise AssertionError(
            f"Expected success but command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout + result.stderr


def current_host_lines() -> tuple[str, str]:
    if Path("/dev/kvm").exists():
        if access("/dev/kvm", W_OK):
            kvm_desc = "`/dev/kvm` is writable"
        else:
            kvm_desc = "`/dev/kvm` is present but not writable"
    else:
        kvm_desc = "`/dev/kvm` is absent"

    if shutil.which("gh"):
        gh_ok = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True).returncode == 0
        gh_desc = "`gh` is installed and authenticated" if gh_ok else "`gh` is installed but unauthenticated"
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


def main() -> int:
    expected_checkpoint_host_line, expected_boundary_host_line = current_host_lines()
    with tempfile.TemporaryDirectory(prefix="unifai-vm-checkpoint-") as tmp:
        root = Path(tmp)
        remote = root / "remote.git"
        work = root / "work"
        detached = root / "detached"
        no_upstream = root / "no-upstream"

        subprocess.check_call(["git", "init", "--bare", str(remote)])
        subprocess.check_call(["git", "clone", str(remote), str(work)])
        run(["git", "config", "user.name", "Little7 Smoke Test"], work)
        run(["git", "config", "user.email", "little7@example.invalid"], work)

        (work / "docs").mkdir(parents=True)
        (work / "scripts").mkdir(parents=True)
        (work / "ci-artifacts" / "bootstrap-preflight").mkdir(parents=True)
        shutil.copy2(HELPER, work / "scripts" / HELPER.name)
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
                "- The publish-boundary maintenance bundle is now preserved as a clean local commit instead of only a dirty working tree, so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens.\n"
                "- The current local hardening stack is preserved as clean commits through `oldsha`, rather than as an uncommitted sandbox delta.\n\n"
                "- Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place.\n"
                "- The current local sandbox also carries one more small checkpoint-refresh helper/doc delta beyond the tracked doc commits:\n"
                "  - `placeholder/helper.py`\n"
                "  - `placeholder/smoke.sh`\n"
                "- Fresh local verification at the current sandbox state is green again:\n"
                "  - `python3 old_refresh_smoke.py`\n\n"
                "## Recommended next move when external boundary opens\n"
                "1. Make the current local branch tip GitHub-visible (the latest non-doc logic commit in that tip is `oldlogic`).\n"
                "## Clean commit candidate\n"
                "- Suggested scope: placeholder scope line\n"
                "- Current local checkpoint chain:\n"
                "  - `oldsha` (`old subject`)\n"
                "- Current uncommitted delta on top:\n"
                "  - `placeholder/file.txt`\n"
                "- Files in the bundle:\n"
                "  - `docs/BOOTSTRAP_VM_VERIFICATION.md`\n"
                "- Smallest re-verification gate before publishing that commit:\n"
                "  ```bash\n"
                "  bash scripts/bootstrap_installer_preflight.sh\n"
                "  ```\n"
            ),
            encoding="utf-8",
        )
        (work / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt").write_text(
            "Commit candidate: placeholder candidate fixture\n"
            "Current local checkpoint: oldsha\n"
            "Current branch state: ahead 0 over fix/openclaw-config-path-and-local-mode\n",
            encoding="utf-8",
        )
        run(["git", "add", "."], work)
        run(["git", "commit", "-m", "docs: seed checkpoint templates"], work)
        run(["git", "branch", "-M", "fix/openclaw-config-path-and-local-mode"], work)
        run(["git", "push", "-u", "origin", "fix/openclaw-config-path-and-local-mode"], work)

        shutil.copytree(work, detached)
        shutil.copytree(work, no_upstream)
        detached_head = run(["git", "rev-parse", "HEAD"], detached)
        run(["git", "checkout", "--detach", detached_head], detached)
        run(["git", "branch", "--unset-upstream"], no_upstream)

        detached_output = expect_fail(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], detached)
        assert "requires a checked-out branch; detached HEAD does not provide a stable publish-boundary checkpoint" in detached_output

        no_upstream_output = expect_fail(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], no_upstream)
        assert "has no upstream; set a GitHub-visible upstream before refreshing the verifier publish-boundary checkpoint" in no_upstream_output

        (work / "logic.txt").write_text("logic\n", encoding="utf-8")
        (work / "docs" / "logic-sidecar.md").write_text("doc companion\n", encoding="utf-8")
        run(["git", "add", "logic.txt", "docs/logic-sidecar.md"], work)
        run(["git", "commit", "-m", "tests: add logic commit"], work)
        logic_sha = run(["git", "rev-parse", "--short", "HEAD"], work)

        (work / "note.txt").write_text("docs\n", encoding="utf-8")
        run(["git", "add", "note.txt"], work)
        run(["git", "commit", "-m", "docs: trailing docs refresh"], work)
        docs_head_sha = run(["git", "rev-parse", "--short", "HEAD"], work)

        (work / "ci-artifacts" / "branch-reconcile-2026-07-10.md").write_text("handoff only\n", encoding="utf-8")
        run(["git", "add", "-f", "ci-artifacts/branch-reconcile-2026-07-10.md"], work)
        run(["git", "commit", "-m", "docs: refresh branch reconcile publish handoff"], work)
        head_sha = run(["git", "rev-parse", "--short", "HEAD"], work)

        (work / "scratch.txt").write_text("dirty\n", encoding="utf-8")
        (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").write_text(
            (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8") + "dirty edit\n",
            encoding="utf-8",
        )

        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")
        latest_checkpoint = read_latest_checkpoint(work)
        commit_candidate = read_commit_candidate(work)
        bundle_section = extract_bundle_section(checkpoint)
        remote_ref = "origin/fix/openclaw-config-path-and-local-mode"
        remote_sha = run(["git", "rev-parse", "--short", remote_ref], work)

        assert f"GitHub-visible branch head remains `{remote_sha}`" in boundary
        assert f"through `{docs_head_sha}` (`docs: trailing docs refresh`), 2 commits ahead in total" in boundary
        assert "local sandbox currently also carries" in boundary
        assert "uncommitted publish-boundary maintenance path(s) beyond HEAD" in boundary
        assert f"latest non-doc logic delta in that local stack is `{docs_head_sha}` (`docs: trailing docs refresh`) in:" in boundary
        assert "  - `note.txt`\n" in boundary
        assert "  - `logic.txt`\n" not in boundary
        assert "  - `ci-artifacts/branch-reconcile-2026-07-10.md`\n" not in boundary
        assert "  - `docs/logic-sidecar.md`\n" not in boundary
        assert "- a fresh local `bash scripts/bootstrap_installer_preflight.sh` rerun is green with the current publish-boundary maintenance bundle in place\n" in boundary
        assert "- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.\n" in boundary
        assert "that helper hardening" not in boundary
        assert expected_boundary_host_line in boundary
        assert "- Working branch: `fix/openclaw-config-path-and-local-mode`" in checkpoint
        assert f"Latest tracked local head in the stack: `{docs_head_sha}`" in checkpoint
        assert f"Latest non-doc logic head in the local stack: `{docs_head_sha}`" in checkpoint
        assert "Tracked local branch state at checkpoint: ahead by 2 commits over the GitHub-visible branch head" in checkpoint
        assert f"1. `{logic_sha}` — `tests: add logic commit`" in checkpoint
        assert f"2. `{docs_head_sha}` — `docs: trailing docs refresh`" in checkpoint
        assert f"3. `{head_sha}` — `docs: refresh branch reconcile publish handoff`" not in checkpoint
        assert "publish-boundary maintenance bundle is no longer only a clean-commit story" in checkpoint
        assert f"tracked head is `{docs_head_sha}`" in checkpoint
        assert "not fully committed" in checkpoint
        assert "uncommitted path(s)" in checkpoint
        assert f"latest non-doc logic commit in that tip is `{docs_head_sha}`" in checkpoint
        assert "publish-boundary maintenance bundle for visible-ref handoff" in checkpoint
        assert "Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place." in checkpoint
        assert "`ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff." in checkpoint
        assert expected_checkpoint_host_line in checkpoint
        assert "the sandbox currently carries 1 uncommitted publish-boundary maintenance update, and the branch is `ahead 2` over `fix/openclaw-config-path-and-local-mode`." in checkpoint
        assert "remote-detection hardening bundle" not in checkpoint
        assert "- The current local sandbox now carries one small publish-boundary maintenance delta beyond the tracked local stack:\n" in checkpoint
        assert "- The current local sandbox now carries no additional uncommitted publish-boundary maintenance delta beyond the tracked local stack represented here.\n" not in checkpoint
        assert "  - `scratch.txt`\n" in checkpoint
        assert "`placeholder/helper.py`" not in checkpoint
        assert "  - `python3 scripts/check_publish_stack_parity_contract.py`\n" in checkpoint
        assert "  - `python3 scripts/check_compare_publish_branch_histories_contract.py`\n" in checkpoint
        assert "  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`\n" in checkpoint
        assert "  - `python3 scripts/check_vm_host_readiness_contract.py`\n" in checkpoint
        assert "  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`\n" in checkpoint
        assert "  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`\n" in checkpoint
        assert "old_refresh_smoke.py" not in checkpoint
        assert "- Current local checkpoint chain:\n" in checkpoint
        assert f"  - `{logic_sha}` (`tests: add logic commit`)\n" in checkpoint
        assert f"  - `{docs_head_sha}` (`docs: trailing docs refresh`)\n" in checkpoint
        assert f"  - `{head_sha}` (`docs: refresh branch reconcile publish handoff`)\n" not in checkpoint
        assert "`oldsha` (`old subject`)" not in checkpoint
        assert "placeholder scope line" not in checkpoint
        assert "Current uncommitted delta on top:\n  - `scratch.txt`\n" in checkpoint
        assert "`placeholder/file.txt`" not in checkpoint
        assert "  - `logic.txt`\n" in bundle_section
        assert "  - `note.txt`\n" in bundle_section
        assert "  - `scratch.txt`\n" in bundle_section
        assert "`placeholder/file.txt`" not in bundle_section
        assert "\n- - Files in the bundle:" not in checkpoint
        assert f"Commit candidate: publish-boundary maintenance bundle for visible-ref handoff @ {docs_head_sha}\n" in commit_candidate
        assert latest_checkpoint == checkpoint
        assert f"Current local checkpoint: {docs_head_sha}\n" in commit_candidate
        assert f"Current checked-out branch tip: {head_sha} (docs: refresh branch reconcile publish handoff)\n" in commit_candidate
        assert "Current branch state: ahead 3 over fix/openclaw-config-path-and-local-mode\n" in commit_candidate
        assert "Checked-out tip delta beyond tracked checkpoint: 1 doc-only commit\n" in commit_candidate
        assert "Working-tree files:\nscratch.txt\n" in commit_candidate
        assert "Verification gates run:\npython3 scripts/check_publish_stack_parity_contract.py\npython3 scripts/check_compare_publish_branch_histories_contract.py\npython3 scripts/check_github_branch_visibility_contract.py\npython3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\npython3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\npython3 scripts/check_vm_host_readiness_contract.py\nbash scripts/smoke_test_publish_stack_parity.sh\nbash scripts/smoke_test_compare_publish_branch_histories.sh\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\nbash scripts/bootstrap_installer_preflight.sh\n" in commit_candidate
        assert "Current host-readiness snapshot:\n" in commit_candidate
        assert expected_checkpoint_host_line in commit_candidate
        assert "- The current local sandbox now carries one small publish-boundary maintenance delta beyond the tracked local stack:\n" in commit_candidate
        assert "- The publish-boundary maintenance bundle is no longer only a clean-commit story: the commit stack is preserved, but the current sandbox also carries additional uncommitted publish-boundary maintenance delta.\n" in commit_candidate
        assert "check-gate hardening bundle" not in commit_candidate
        assert f"- The branch still needs the current branch tip `{head_sha}` GitHub-visible; the tracked publish-boundary checkpoint remains `{docs_head_sha}` until that visible ref exists.\n" in commit_candidate
        assert f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{remote_sha}`, so the next real boundary is still a visible rerun on the exact published ref.\n" in commit_candidate
        assert "Next clean move once the branch tip is GitHub-visible:\n" in commit_candidate
        assert "GitHub auth / a visible ref" not in commit_candidate
        assert (
            f"- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{head_sha}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{docs_head_sha}` until a non-doc commit supersedes it.\n"
        ) in commit_candidate

        run(["git", "add", "docs/BOOTSTRAP_VM_VERIFICATION.md", "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"], work)
        run(["git", "commit", "-m", "docs: refresh vm verifier checkpoint state"], work)
        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        refreshed_boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        refreshed_checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")
        refreshed_latest_checkpoint = read_latest_checkpoint(work)
        refreshed_commit_candidate = read_commit_candidate(work)
        refreshed_tip = run(["git", "rev-parse", "--short", "HEAD"], work)
        refreshed_tip_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
        refreshed_delta_section = refreshed_checkpoint.split("Current uncommitted delta on top:\n", 1)[1].split("- Files in the bundle:", 1)[0]
        refreshed_bundle_section = extract_bundle_section(refreshed_checkpoint)

        assert f"GitHub-visible branch head remains `{remote_sha}`" in refreshed_boundary
        assert f"through `{docs_head_sha}` (`docs: trailing docs refresh`), 2 commits ahead in total" in refreshed_boundary
        assert f"latest non-doc logic delta in that local stack is `{docs_head_sha}` (`docs: trailing docs refresh`) in:" in refreshed_boundary
        assert "  - `note.txt`\n" in refreshed_boundary
        assert "  - `logic.txt`\n" not in refreshed_boundary
        assert "  - `ci-artifacts/branch-reconcile-2026-07-10.md`\n" not in refreshed_boundary
        assert "uncommitted publish-boundary maintenance path(s) beyond HEAD" in refreshed_boundary
        assert "- a fresh local `bash scripts/bootstrap_installer_preflight.sh` rerun is green with the current publish-boundary maintenance bundle in place\n" in refreshed_boundary
        assert "- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.\n" in refreshed_boundary
        assert "that helper hardening" not in refreshed_boundary
        assert expected_boundary_host_line in refreshed_boundary
        assert "- Working branch: `fix/openclaw-config-path-and-local-mode`" in refreshed_checkpoint
        assert f"Latest tracked local head in the stack: `{docs_head_sha}`" in refreshed_checkpoint
        assert "Tracked local branch state at checkpoint: ahead by 2 commits over the GitHub-visible branch head" in refreshed_checkpoint
        assert f"2. `{docs_head_sha}` — `docs: trailing docs refresh`" in refreshed_checkpoint
        assert f"3. `{head_sha}` — `docs: refresh branch reconcile publish handoff`" not in refreshed_checkpoint
        assert "publish-boundary maintenance bundle for visible-ref handoff" in refreshed_checkpoint
        assert "Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place." in refreshed_checkpoint
        assert "`ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff." in refreshed_checkpoint
        assert expected_checkpoint_host_line in refreshed_checkpoint
        assert "  - `python3 scripts/check_github_branch_visibility_contract.py`\n" in refreshed_checkpoint
        assert "the sandbox currently carries 1 uncommitted publish-boundary maintenance update, and the branch is `ahead 2` over `fix/openclaw-config-path-and-local-mode`." in refreshed_checkpoint
        assert "- The current local sandbox now carries one small publish-boundary maintenance delta beyond the tracked local stack:\n" in refreshed_checkpoint
        assert "- The current local sandbox now carries no additional uncommitted publish-boundary maintenance delta beyond the tracked local stack represented here.\n" not in refreshed_checkpoint
        assert f"  - `{logic_sha}` (`tests: add logic commit`)\n" in refreshed_checkpoint
        assert f"  - `{docs_head_sha}` (`docs: trailing docs refresh`)\n" in refreshed_checkpoint
        assert f"  - `{head_sha}` (`docs: refresh branch reconcile publish handoff`)\n" not in refreshed_checkpoint
        assert "Current uncommitted delta on top:\n  - `scratch.txt`\n" in refreshed_checkpoint
        assert refreshed_delta_section == "  - `scratch.txt`\n"
        assert "`ci-artifacts/bootstrap-preflight/commit-candidate.txt`" not in refreshed_delta_section
        assert "  - `logic.txt`\n" in refreshed_bundle_section
        assert "  - `note.txt`\n" in refreshed_bundle_section
        assert "  - `scratch.txt`\n" in refreshed_bundle_section
        assert "\n- - Files in the bundle:" not in refreshed_checkpoint
        assert refreshed_latest_checkpoint == refreshed_checkpoint
        assert f"Current local checkpoint: {docs_head_sha}\n" in refreshed_commit_candidate
        assert "Checked-out tip delta beyond tracked checkpoint: 2 doc-only commits\n" in refreshed_commit_candidate
        assert "Working-tree files:\nscratch.txt\n" in refreshed_commit_candidate
        assert "ci-artifacts/bootstrap-preflight/commit-candidate.txt" not in refreshed_commit_candidate.split("Working-tree files:\n", 1)[1].split("\n\n", 1)[0]
        assert "Current host-readiness snapshot:\n" in refreshed_commit_candidate
        assert "Verification gates run:\npython3 scripts/check_publish_stack_parity_contract.py\npython3 scripts/check_compare_publish_branch_histories_contract.py\npython3 scripts/check_github_branch_visibility_contract.py\npython3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\npython3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\npython3 scripts/check_vm_host_readiness_contract.py\nbash scripts/smoke_test_publish_stack_parity.sh\nbash scripts/smoke_test_compare_publish_branch_histories.sh\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\nbash scripts/bootstrap_installer_preflight.sh\n" in refreshed_commit_candidate
        assert expected_checkpoint_host_line in refreshed_commit_candidate
        assert "- The publish-boundary maintenance bundle is no longer only a clean-commit story: the commit stack is preserved, but the current sandbox also carries additional uncommitted publish-boundary maintenance delta.\n" in refreshed_commit_candidate
        assert (
            f"- The branch still needs the current branch tip `{refreshed_tip}` GitHub-visible; "
            f"the tracked publish-boundary checkpoint remains `{docs_head_sha}` until that visible ref exists.\n"
        ) in refreshed_commit_candidate
        assert f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{remote_sha}`, so the next real boundary is still a visible rerun on the exact published ref.\n" in refreshed_commit_candidate
        assert "Next clean move once the branch tip is GitHub-visible:\n" in refreshed_commit_candidate
        assert (
            f"- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{refreshed_tip}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{docs_head_sha}` until a non-doc commit supersedes it.\n"
        ) in refreshed_commit_candidate
        assert "GitHub auth / a visible ref" not in refreshed_commit_candidate
        assert f"Current checked-out branch tip: {refreshed_tip} ({refreshed_tip_subject})\n" in refreshed_commit_candidate

        run(["git", "add", "docs/BOOTSTRAP_VM_VERIFICATION.md", "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"], work)
        run(["git", "commit", "-m", "docs: sync visible verifier boundary state"], work)
        run(["git", "add", "scratch.txt"], work)
        run(["git", "commit", "-m", "docs: clear dirty scratch state"], work)
        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        stable_boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        stable_checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")
        stable_latest_checkpoint = read_latest_checkpoint(work)
        stable_commit_candidate = read_commit_candidate(work)
        stable_head = run(["git", "rev-parse", "--short", "HEAD"], work)
        stable_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
        stable_ahead = run(["git", "rev-list", "--count", f"{remote_ref}..HEAD"], work)
        stable_bundle_section = extract_bundle_section(stable_checkpoint)

        assert f"through `{stable_head}` (`{stable_subject}`), {stable_ahead} commits ahead in total" in stable_boundary
        assert f"latest non-doc logic delta in that local stack is `{stable_head}` (`{stable_subject}`) in:" in stable_boundary
        assert "  - `scratch.txt`\n" in stable_boundary
        assert "  - `logic.txt`\n" not in stable_boundary
        assert "uncommitted publish-boundary maintenance path(s) beyond HEAD" in stable_boundary
        assert "- a fresh local `bash scripts/bootstrap_installer_preflight.sh` rerun is green with the current publish-boundary maintenance bundle in place\n" in stable_boundary
        assert "- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.\n" in stable_boundary
        assert "that helper hardening" not in stable_boundary
        assert expected_boundary_host_line in stable_boundary
        assert "- Working branch: `fix/openclaw-config-path-and-local-mode`" in stable_checkpoint
        assert f"Latest tracked local head in the stack: `{stable_head}`" in stable_checkpoint
        assert f"Tracked local branch state at checkpoint: ahead by {stable_ahead} commits over the GitHub-visible branch head" in stable_checkpoint
        assert f"`{stable_head}` — `{stable_subject}`" in stable_checkpoint
        assert "publish-boundary maintenance bundle for visible-ref handoff" in stable_checkpoint
        assert "Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place." in stable_checkpoint
        assert "`ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff." in stable_checkpoint
        assert expected_checkpoint_host_line in stable_checkpoint
        assert f"the sandbox currently carries 2 uncommitted publish-boundary maintenance updates, and the branch is `ahead {stable_ahead}` over `fix/openclaw-config-path-and-local-mode`." in stable_checkpoint
        assert "- The current local sandbox now carries " in stable_checkpoint
        assert "publish-boundary maintenance " in stable_checkpoint
        assert "beyond the tracked local stack:\n" in stable_checkpoint
        assert "- The current local sandbox now carries no additional uncommitted publish-boundary maintenance delta beyond the tracked local stack represented here.\n" not in stable_checkpoint
        assert f"  - `{logic_sha}` (`tests: add logic commit`)\n" in stable_checkpoint
        assert f"  - `{stable_head}` (`{stable_subject}`)\n" in stable_checkpoint
        assert "Current uncommitted delta on top:\n  - `docs/BOOTSTRAP_VM_VERIFICATION.md`\n  - `docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md`\n" in stable_checkpoint
        assert "  - `logic.txt`\n" in stable_bundle_section
        assert "  - `note.txt`\n" in stable_bundle_section
        assert "  - `scratch.txt`\n" in stable_bundle_section
        assert "\n- - Files in the bundle:" not in stable_checkpoint
        assert stable_latest_checkpoint == stable_checkpoint
        assert f"Current local checkpoint: {stable_head}\n" in stable_commit_candidate
        assert "Current checked-out branch tip:" not in stable_commit_candidate
        assert f"Current branch state: ahead {stable_ahead} over fix/openclaw-config-path-and-local-mode\n" in stable_commit_candidate
        assert "Checked-out tip delta beyond tracked checkpoint:" not in stable_commit_candidate
        assert "Working-tree files:\ndocs/BOOTSTRAP_VM_VERIFICATION.md\ndocs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md\n" in stable_commit_candidate
        assert "Current host-readiness snapshot:\n" in stable_commit_candidate
        assert "Verification gates run:\npython3 scripts/check_publish_stack_parity_contract.py\npython3 scripts/check_compare_publish_branch_histories_contract.py\npython3 scripts/check_github_branch_visibility_contract.py\npython3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\npython3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\npython3 scripts/check_vm_host_readiness_contract.py\nbash scripts/smoke_test_publish_stack_parity.sh\nbash scripts/smoke_test_compare_publish_branch_histories.sh\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\nbash scripts/bootstrap_installer_preflight.sh\n" in stable_commit_candidate
        assert expected_checkpoint_host_line in stable_commit_candidate
        assert "- The publish-boundary maintenance bundle is no longer only a clean-commit story: the commit stack is preserved, but the current sandbox also carries additional uncommitted publish-boundary maintenance delta.\n" in stable_commit_candidate
        assert f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on `{remote_sha}`, so the next real boundary is still a visible rerun on the exact published ref.\n" in stable_commit_candidate
        assert "Next clean move before the real VM-proof path:\n" in stable_commit_candidate
        assert "GitHub auth / a visible ref" not in stable_commit_candidate
        assert "`ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff." in stable_checkpoint

        run(["git", "add", "docs/BOOTSTRAP_VM_VERIFICATION.md", "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"], work)
        run(["git", "commit", "-m", "docs: refresh visible verifier boundary state"], work)
        doc_only_tip = run(["git", "rev-parse", "--short", "HEAD"], work)
        doc_only_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        doc_only_boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        doc_only_checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")
        doc_only_latest_checkpoint = read_latest_checkpoint(work)
        doc_only_commit_candidate = read_commit_candidate(work)
        doc_only_ahead = run(["git", "rev-list", "--count", f"{remote_ref}..HEAD"], work)

        assert f"through `{stable_head}` (`{stable_subject}`), {stable_ahead} commits ahead in total" in doc_only_boundary
        assert "- Working branch: `fix/openclaw-config-path-and-local-mode`" in doc_only_checkpoint
        assert f"Latest tracked local head in the stack: `{stable_head}`" in doc_only_checkpoint
        assert f"Tracked local branch state at checkpoint: ahead by {stable_ahead} commits over the GitHub-visible branch head" in doc_only_checkpoint
        assert "the current checked-out branch tip is" not in doc_only_boundary
        assert "- Current checked-out branch tip:" not in doc_only_checkpoint
        assert doc_only_latest_checkpoint == doc_only_checkpoint
        assert f"Current local checkpoint: {stable_head}\n" in doc_only_commit_candidate
        assert f"Current checked-out branch tip: {doc_only_tip} ({doc_only_subject})\n" in doc_only_commit_candidate
        assert f"Current branch state: ahead {doc_only_ahead} over fix/openclaw-config-path-and-local-mode\n" in doc_only_commit_candidate
        assert "Checked-out tip delta beyond tracked checkpoint: 1 doc-only commit\n" in doc_only_commit_candidate
        assert "Working-tree files:\n(clean)\n" in doc_only_commit_candidate
        assert "Verification gates run:\npython3 scripts/check_publish_stack_parity_contract.py\npython3 scripts/check_compare_publish_branch_histories_contract.py\npython3 scripts/check_github_branch_visibility_contract.py\npython3 scripts/check_vm_verifier_checkpoint_freshness_contract.py\npython3 scripts/check_vm_verifier_checkpoint_refresh_contract.py\npython3 scripts/check_vm_host_readiness_contract.py\nbash scripts/smoke_test_publish_stack_parity.sh\nbash scripts/smoke_test_compare_publish_branch_histories.sh\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py\npython3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py\nbash scripts/bootstrap_installer_preflight.sh\n" in doc_only_commit_candidate
        assert (
            f"- The branch still needs the current branch tip `{doc_only_tip}` GitHub-visible; "
            f"the tracked publish-boundary checkpoint remains `{stable_head}` until that visible ref exists.\n"
        ) in doc_only_commit_candidate
        assert (
            f"- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{doc_only_tip}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{stable_head}` until a non-doc commit supersedes it.\n"
        ) in doc_only_commit_candidate

        run(["git", "add", "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"], work)
        run(["git", "commit", "-m", "docs: settle verifier checkpoint handoff"], work)
        second_doc_only_tip = run(["git", "rev-parse", "--short", "HEAD"], work)
        second_doc_only_subject = run(["git", "show", "-s", "--format=%s", "HEAD"], work)
        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        second_doc_only_boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        second_doc_only_checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")
        second_doc_only_latest_checkpoint = read_latest_checkpoint(work)
        second_doc_only_commit_candidate = read_commit_candidate(work)
        second_doc_only_ahead = run(["git", "rev-list", "--count", f"{remote_ref}..HEAD"], work)

        assert f"through `{stable_head}` (`{stable_subject}`), {stable_ahead} commits ahead in total" in second_doc_only_boundary
        assert f"Latest tracked local head in the stack: `{stable_head}`" in second_doc_only_checkpoint
        assert f"Tracked local branch state at checkpoint: ahead by {stable_ahead} commits over the GitHub-visible branch head" in second_doc_only_checkpoint
        assert "the current checked-out branch tip is" not in second_doc_only_boundary
        assert "- Current checked-out branch tip:" not in second_doc_only_checkpoint
        assert second_doc_only_latest_checkpoint == second_doc_only_checkpoint
        assert f"Current local checkpoint: {stable_head}\n" in second_doc_only_commit_candidate
        assert f"Current checked-out branch tip: {second_doc_only_tip} ({second_doc_only_subject})\n" in second_doc_only_commit_candidate
        assert f"Current branch state: ahead {second_doc_only_ahead} over fix/openclaw-config-path-and-local-mode\n" in second_doc_only_commit_candidate
        assert "Checked-out tip delta beyond tracked checkpoint: 2 doc-only commits\n" in second_doc_only_commit_candidate
        assert "Working-tree files:\n(clean)\n" in second_doc_only_commit_candidate
        assert (
            f"- The branch still needs the current branch tip `{second_doc_only_tip}` GitHub-visible; "
            f"the tracked publish-boundary checkpoint remains `{stable_head}` until that visible ref exists.\n"
        ) in second_doc_only_commit_candidate
        assert (
            f"- Run `git push origin HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{second_doc_only_tip}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{stable_head}` until a non-doc commit supersedes it.\n"
        ) in second_doc_only_commit_candidate

        run(["git", "push", "origin", "HEAD:fix/openclaw-config-path-and-local-mode"], work)
        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        aligned_boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        aligned_checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")
        aligned_latest_checkpoint = read_latest_checkpoint(work)
        aligned_commit_candidate = read_commit_candidate(work)
        aligned_status = run(["git", "status", "--short"], work)

        assert "docs/BOOTSTRAP_VM_VERIFICATION.md" in aligned_status
        assert "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md" in aligned_status
        assert f"GitHub-visible branch head remains `{stable_head}`" in aligned_boundary
        assert f"GitHub-visible branch head: `{stable_head}`" in aligned_checkpoint
        assert f"Latest tracked local head in the stack: `{stable_head}`" in aligned_checkpoint
        assert aligned_latest_checkpoint == aligned_checkpoint
        assert f"Current local checkpoint: {stable_head}\n" in aligned_commit_candidate
        assert f"Current checked-out branch tip: {second_doc_only_tip} ({second_doc_only_subject})\n" in aligned_commit_candidate
        assert "Current branch state: ahead 0 over fix/openclaw-config-path-and-local-mode\n" in aligned_commit_candidate
        assert "Checked-out tip delta beyond tracked checkpoint: 2 doc-only commits\n" in aligned_commit_candidate
        assert "Working-tree files:\n(clean)\n" in aligned_commit_candidate
        assert f"  - `{stable_head}` (`{stable_subject}`)\n" in aligned_commit_candidate
        assert (
            f"- The exact branch tip `{second_doc_only_tip}` is already GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{stable_head}` because the tip-only delta is doc-only.\n"
        ) in aligned_commit_candidate
        assert (
            f"- The exact branch tip `{second_doc_only_tip}` is already GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"rerun `Bootstrap Installer Preflight` on that visible ref while the tracked publish-boundary checkpoint remains `{stable_head}`.\n"
        ) in aligned_commit_candidate
        assert "Next clean move before the real VM-proof path:\n" in aligned_commit_candidate

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
        (work / "docs" / "github-remote-checkpoint.md").write_text("github remote doc-only tip\n", encoding="utf-8")
        run(["git", "add", "docs/github-remote-checkpoint.md"], work)
        run(["git", "commit", "-m", "docs: add github-remote doc-only tip"], work)
        github_remote_tip = run(["git", "rev-parse", "--short", "HEAD"], work)
        subprocess.check_call(["python3", "-B", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        github_remote_commit_candidate = read_commit_candidate(work)
        assert (
            f"- Run `git push github HEAD:fix/openclaw-config-path-and-local-mode` to make the current branch tip `{github_remote_tip}` GitHub-visible on `fix/openclaw-config-path-and-local-mode`; "
            f"the tracked publish-boundary checkpoint remains `{stable_head}` until a non-doc commit supersedes it.\n"
        ) in github_remote_commit_candidate

        spec = importlib.util.spec_from_file_location("refresh_vm_verifier_checkpoint_state_no_gh", work / "scripts" / HELPER.name)
        if spec is None or spec.loader is None:
            raise AssertionError("Could not load checkpoint refresh helper for no-gh smoke validation")
        helper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper_module)

        original_run = helper_module.subprocess.run

        def fake_run(args: list[str] | tuple[str, ...], *rest: object, **kwargs: object):
            if args and args[0] == "gh":
                raise FileNotFoundError("gh")
            return original_run(args, *rest, **kwargs)

        helper_module.subprocess.run = fake_run
        try:
            assert helper_module.command_succeeds("gh", "auth", "status") is False
        finally:
            helper_module.subprocess.run = original_run

    print("[PASS] VM verifier checkpoint refresh smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
