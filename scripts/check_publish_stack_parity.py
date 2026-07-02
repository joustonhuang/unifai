#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWED_PATHS = [
    "docs/BOOTSTRAP_VM_VERIFICATION.md",
    "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md",
]


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def changed_paths(base_ref: str, tip_ref: str) -> list[str]:
    result = run_git("diff", "--name-only", f"{base_ref}..{tip_ref}")
    return [line for line in result.stdout.splitlines() if line]


def file_text(ref: str, path: str) -> str | None:
    result = run_git("show", f"{ref}:{path}", check=False)
    if result.returncode == 0:
        return result.stdout
    if "exists on disk, but not in" in result.stderr or "does not exist in" in result.stderr:
        return None
    fail(f"Could not read {path} at {ref}: {result.stderr.strip()}")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check that a cleaned publish stack still matches an expected functional tip, "
            "while allowing explicitly noisy checkpoint/doc paths to differ."
        )
    )
    parser.add_argument("base_ref", help="Shared base ref before the publish stack starts")
    parser.add_argument("candidate_ref", help="Candidate cleaned branch/ref to verify")
    parser.add_argument("expected_ref", help="Expected functional tip to match")
    parser.add_argument(
        "--allow-path",
        action="append",
        default=[],
        help="Path that may differ between candidate and expected refs; repeat as needed",
    )
    parser.add_argument(
        "--no-default-allow-paths",
        action="store_true",
        help="Do not auto-allow the current verifier checkpoint docs",
    )
    args = parser.parse_args()

    default_allowed = [] if args.no_default_allow_paths else DEFAULT_ALLOWED_PATHS
    allowed_paths = set(default_allowed + args.allow_path)

    expected_changed = set(changed_paths(args.base_ref, args.expected_ref))
    candidate_changed = set(changed_paths(args.base_ref, args.candidate_ref))
    interesting_paths = sorted((expected_changed | candidate_changed) - allowed_paths)

    mismatches: list[str] = []
    for path in interesting_paths:
        if file_text(args.candidate_ref, path) != file_text(args.expected_ref, path):
            mismatches.append(path)

    if mismatches:
        print("[FAIL] Candidate publish stack does not match the expected functional tip.")
        print("Compared refs:")
        print(f"  base: {args.base_ref}")
        print(f"  candidate: {args.candidate_ref}")
        print(f"  expected: {args.expected_ref}")
        if allowed_paths:
            print("Allowed differing paths:")
            for path in sorted(allowed_paths):
                print(f"  {path}")
        print("Mismatched functional paths:")
        for path in mismatches:
            print(f"  {path}")
        sys.exit(1)

    print("[PASS] Candidate publish stack matches the expected functional tip.")
    print("Compared refs:")
    print(f"  base: {args.base_ref}")
    print(f"  candidate: {args.candidate_ref}")
    print(f"  expected: {args.expected_ref}")
    if allowed_paths:
        print("Allowed differing paths:")
        for path in sorted(allowed_paths):
            print(f"  {path}")
    print(f"Checked functional paths: {len(interesting_paths)}")


if __name__ == "__main__":
    main()
