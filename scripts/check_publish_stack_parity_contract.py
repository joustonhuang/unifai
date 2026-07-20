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
    ('from collections import Counter', "Publish stack parity checker imports Counter for per-path delta accounting"),
    ('DEFAULT_ALLOWED_PATHS = [', "Publish stack parity checker defines default allowed noisy paths"),
    ('"docs/BOOTSTRAP_VM_VERIFICATION.md"', "Publish stack parity checker allows the boundary doc by default"),
    ('"docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Publish stack parity checker allows the checkpoint doc by default"),
    ('def changed_paths(base_ref: str, tip_ref: str) -> list[str]:', "Publish stack parity checker defines changed-path collection"),
    ('run_git("diff", "--name-only", f"{base_ref}..{tip_ref}")', "Publish stack parity checker diffs refs by changed path"),
    ('def file_text(ref: str, path: str) -> str | None:', "Publish stack parity checker defines per-ref file loading"),
    ('result = run_git("show", f"{ref}:{path}", check=False)', "Publish stack parity checker reads candidate and expected file contents through git show"),
    ('if "exists on disk, but not in" in result.stderr or "does not exist in" in result.stderr:', "Publish stack parity checker treats missing paths as absent content instead of crashing"),
    ('def path_delta(base_ref: str, tip_ref: str, path: str) -> tuple[Counter[str], Counter[str]]:', "Publish stack parity checker can read per-path diff deltas from the shared base"),
    ('run_git(\n        "diff",', "Publish stack parity checker shells out to git diff for per-path delta inspection"),
    ('def path_matches_expected_delta(', "Publish stack parity checker defines a delta-absorption matcher"),
    ('return not (expected_removed - candidate_removed or expected_added - candidate_added)', "Publish stack parity checker accepts cleaner files that absorb the expected delta even if they add extra local helper coverage"),
    ('"--allow-path"', "Publish stack parity checker supports explicit extra allowed paths"),
    ('"--no-default-allow-paths"', "Publish stack parity checker can disable the default noisy doc allowlist"),
    ('interesting_paths = sorted(expected_changed - allowed_paths)', "Publish stack parity checker compares only the expected branch\\'s non-allowed changed paths"),
    ('candidate_only_paths = sorted((candidate_changed - expected_changed) - allowed_paths)', "Publish stack parity checker tracks cleaner-only additions separately from expected parity paths"),
    ('if not path_matches_expected_delta(', "Publish stack parity checker fails only when the cleaner branch does not preserve the expected functional delta"),
    ('"Ignored candidate-only paths:"', "Publish stack parity checker reports cleaner-only additions without failing parity"),
    ('"[FAIL] Candidate publish stack does not match the expected functional tip."', "Publish stack parity checker emits a fail-closed mismatch verdict"),
    ('"Mismatched functional paths:"', "Publish stack parity checker prints mismatched functional paths"),
    ('"[PASS] Candidate publish stack matches the expected functional tip."', "Publish stack parity checker emits a passing parity verdict"),
    ('print(f"Checked expected functional paths: {len(interesting_paths)}")', "Publish stack parity checker reports how many expected functional paths were checked"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] Publish stack parity contract looks sane")
