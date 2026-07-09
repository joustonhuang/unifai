#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_publish_stack_parity.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('DEFAULT_ALLOWED_PATHS = [', "Publish stack parity checker defines default allowed noisy paths"),
    ('"docs/BOOTSTRAP_VM_VERIFICATION.md"', "Publish stack parity checker allows the boundary doc by default"),
    ('"docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Publish stack parity checker allows the checkpoint doc by default"),
    ('def changed_paths(base_ref: str, tip_ref: str) -> list[str]:', "Publish stack parity checker defines changed-path collection"),
    ('run_git("diff", "--name-only", f"{base_ref}..{tip_ref}")', "Publish stack parity checker diffs refs by changed path"),
    ('def file_text(ref: str, path: str) -> str | None:', "Publish stack parity checker defines per-ref file loading"),
    ('result = run_git("show", f"{ref}:{path}", check=False)', "Publish stack parity checker reads candidate and expected file contents through git show"),
    ('if "exists on disk, but not in" in result.stderr or "does not exist in" in result.stderr:', "Publish stack parity checker treats missing paths as absent content instead of crashing"),
    ('"--allow-path"', "Publish stack parity checker supports explicit extra allowed paths"),
    ('"--no-default-allow-paths"', "Publish stack parity checker can disable the default noisy doc allowlist"),
    ('interesting_paths = sorted((expected_changed | candidate_changed) - allowed_paths)', "Publish stack parity checker compares only non-allowed changed paths"),
    ('if file_text(args.candidate_ref, path) != file_text(args.expected_ref, path):', "Publish stack parity checker fails on functional content mismatches"),
    ('"[FAIL] Candidate publish stack does not match the expected functional tip."', "Publish stack parity checker emits a fail-closed mismatch verdict"),
    ('"Mismatched functional paths:"', "Publish stack parity checker prints mismatched functional paths"),
    ('"[PASS] Candidate publish stack matches the expected functional tip."', "Publish stack parity checker emits a passing parity verdict"),
    ('print(f"Checked functional paths: {len(interesting_paths)}")', "Publish stack parity checker reports how many functional paths were checked"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] Publish stack parity contract looks sane")
