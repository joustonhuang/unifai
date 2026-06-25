#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / "scripts" / "refresh_vm_verifier_checkpoint_state.py"


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="unifai-vm-checkpoint-") as tmp:
        root = Path(tmp)
        remote = root / "remote.git"
        work = root / "work"

        subprocess.check_call(["git", "init", "--bare", str(remote)])
        subprocess.check_call(["git", "clone", str(remote), str(work)])
        run(["git", "config", "user.name", "Little7 Smoke Test"], work)
        run(["git", "config", "user.email", "little7@example.invalid"], work)

        (work / "docs").mkdir(parents=True)
        (work / "scripts").mkdir(parents=True)
        shutil.copy2(HELPER, work / "scripts" / HELPER.name)

        (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").write_text(
            "Current known boundary on this branch family:\n"
            "- GitHub-visible branch head remains `oldhead`\n"
            "- the local hardening stack is currently ahead of that public ref through `oldsha` (`old subject`), 0 commits ahead in total\n",
            encoding="utf-8",
        )
        (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").write_text(
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
            "- The check-gate hardening bundle is now preserved as a clean local commit instead of only a dirty working tree, so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens.\n"
            "- The current local hardening stack is preserved as clean commits through `oldsha`, rather than as an uncommitted sandbox delta.\n\n"
            "## Recommended next move when external boundary opens\n"
            "1. Make the current local branch tip GitHub-visible (the latest non-doc logic commit in that tip is `oldlogic`).\n",
            encoding="utf-8",
        )
        run(["git", "add", "."], work)
        run(["git", "commit", "-m", "docs: seed checkpoint templates"], work)
        run(["git", "branch", "-M", "fix/openclaw-config-path-and-local-mode"], work)
        run(["git", "push", "-u", "origin", "fix/openclaw-config-path-and-local-mode"], work)

        (work / "logic.txt").write_text("logic\n", encoding="utf-8")
        run(["git", "add", "logic.txt"], work)
        run(["git", "commit", "-m", "tests: add logic commit"], work)
        logic_sha = run(["git", "rev-parse", "--short", "HEAD"], work)

        (work / "note.txt").write_text("docs\n", encoding="utf-8")
        run(["git", "add", "note.txt"], work)
        run(["git", "commit", "-m", "docs: trailing docs refresh"], work)
        head_sha = run(["git", "rev-parse", "--short", "HEAD"], work)

        (work / "scratch.txt").write_text("dirty\n", encoding="utf-8")
        (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").write_text(
            (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8") + "dirty edit\n",
            encoding="utf-8",
        )

        subprocess.check_call(["python3", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")

        assert f"through `{head_sha}` (`docs: trailing docs refresh`), 2 commits ahead in total" in boundary
        assert "local sandbox currently also carries" in boundary
        assert "uncommitted verifier-hardening path(s) beyond HEAD" in boundary
        assert f"Latest tracked local head in the stack: `{head_sha}`" in checkpoint
        assert f"Latest non-doc logic head in the local stack: `{logic_sha}`" in checkpoint
        assert "Tracked local branch state at checkpoint: ahead by 2 commits over the GitHub-visible branch head" in checkpoint
        assert f"1. `{logic_sha}` — `tests: add logic commit`" in checkpoint
        assert f"2. `{head_sha}` — `docs: trailing docs refresh`" in checkpoint
        assert "no longer only a clean-commit story" in checkpoint
        assert f"tracked head is `{head_sha}`" in checkpoint
        assert "not fully committed" in checkpoint
        assert "uncommitted path(s)" in checkpoint
        assert f"latest non-doc logic commit in that tip is `{logic_sha}`" in checkpoint

        run(["git", "add", "docs/BOOTSTRAP_VM_VERIFICATION.md", "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"], work)
        run(["git", "commit", "-m", "docs: refresh vm verifier checkpoint state"], work)
        subprocess.check_call(["python3", "scripts/refresh_vm_verifier_checkpoint_state.py"], cwd=work)

        refreshed_boundary = (work / "docs" / "BOOTSTRAP_VM_VERIFICATION.md").read_text(encoding="utf-8")
        refreshed_checkpoint = (work / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md").read_text(encoding="utf-8")

        assert f"through `{head_sha}` (`docs: trailing docs refresh`), 2 commits ahead in total" in refreshed_boundary
        assert f"Latest tracked local head in the stack: `{head_sha}`" in refreshed_checkpoint
        assert "Tracked local branch state at checkpoint: ahead by 2 commits over the GitHub-visible branch head" in refreshed_checkpoint
        assert f"2. `{head_sha}` — `docs: trailing docs refresh`" in refreshed_checkpoint

    print("[PASS] VM verifier checkpoint refresh smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
