#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = REPO_ROOT / "scripts" / "run_vm_verifier_preflight.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = PREFLIGHT.read_text(encoding="utf-8")

required = [
    ("bash scripts/bootstrap_installer_preflight.sh", "Wrapper runs bootstrap installer preflight first"),
    ('git show-ref --verify --quiet "refs/heads/$ref"', "Wrapper distinguishes local branch names from explicit refs/SHAs"),
    ('bash scripts/check_github_branch_visibility.sh "$ref"', "Wrapper checks GitHub branch visibility for local branches"),
    ("skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA.", "Wrapper explains why branch visibility is skipped for explicit refs/SHAs"),
    ('python3 scripts/check_github_check_gate.py "$ref"', "Wrapper runs GitHub check gate inspection on the chosen ref"),
    ('Next: bash scripts/vm/verify_bootstrap_in_vm.sh $ref', "Wrapper points to the VM verifier as the next step"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] VM verifier preflight wrapper contract looks sane')
