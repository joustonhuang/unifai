#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"
DEFAULT_ALLOWED_PATHS = [
    "docs/BOOTSTRAP_VM_VERIFICATION.md",
    "docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md",
    "ci-artifacts/bootstrap-preflight/commit-candidate.txt",
    "ci-artifacts/vm-verifier-checkpoint-latest.md",
    "ci-artifacts/branch-reconcile-2026-07-10.md",
    "ci-artifacts/publish-stack-reconciliation-next-step.txt",
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


def git_output(*args: str) -> str | None:
    result = run_git(*args, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


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


def path_delta(base_ref: str, tip_ref: str, path: str) -> tuple[Counter[str], Counter[str]]:
    result = run_git(
        "diff",
        "--no-ext-diff",
        "--unified=0",
        f"{base_ref}..{tip_ref}",
        "--",
        path,
    )
    added: Counter[str] = Counter()
    removed: Counter[str] = Counter()
    for line in result.stdout.splitlines():
        if line.startswith(("diff --git", "index ", "--- ", "+++ ", "@@")):
            continue
        if line.startswith("+"):
            added[line[1:]] += 1
        elif line.startswith("-"):
            removed[line[1:]] += 1
    return removed, added


def path_matches_expected_delta(
    base_ref: str,
    candidate_ref: str,
    expected_ref: str,
    path: str,
) -> bool:
    expected_text = file_text(expected_ref, path)
    candidate_text = file_text(candidate_ref, path)
    if candidate_text == expected_text:
        return True
    if expected_text is None or candidate_text is None:
        return False
    if "\0" in expected_text or "\0" in candidate_text:
        return False

    expected_removed, expected_added = path_delta(base_ref, expected_ref, path)
    candidate_removed, candidate_added = path_delta(base_ref, candidate_ref, path)
    return not (expected_removed - candidate_removed or expected_added - candidate_added)


def infer_current_handoff_refs() -> tuple[str, str, str]:
    if not COMMIT_CANDIDATE.exists():
        fail(f"Could not infer refs: missing handoff artifact {COMMIT_CANDIDATE}.")

    commit_candidate_text = COMMIT_CANDIDATE.read_text(encoding="utf-8")
    checkpoint_match = re.search(r"^Current local checkpoint:\s+(\S+)$", commit_candidate_text, re.M)
    if not checkpoint_match:
        fail("Could not infer refs: commit-candidate handoff is missing the local checkpoint line.")
    candidate_ref = checkpoint_match.group(1)

    current_branch = git_output("branch", "--show-current")
    if not current_branch:
        fail(
            "Could not infer refs: detached HEAD does not provide a stable expected ref; "
            "pass explicit refs instead."
        )

    base_ref = git_output("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")
    if not base_ref:
        fail(
            f"Could not infer refs: branch '{current_branch}' has no upstream; "
            "pass explicit refs instead."
        )

    expected_ref = "HEAD"
    return base_ref, candidate_ref, expected_ref


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check that a cleaned publish stack still matches an expected functional tip, "
            "while allowing explicitly noisy checkpoint/doc paths to differ."
        )
    )
    parser.add_argument(
        "base_ref",
        nargs="?",
        help="Shared base ref before the publish stack starts",
    )
    parser.add_argument(
        "candidate_ref",
        nargs="?",
        help="Candidate cleaned branch/ref to verify",
    )
    parser.add_argument(
        "expected_ref",
        nargs="?",
        help="Expected functional tip to match",
    )
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

    provided_refs = [args.base_ref, args.candidate_ref, args.expected_ref]
    if any(ref is None for ref in provided_refs):
        if any(ref is not None for ref in provided_refs):
            parser.error("pass either all three refs or none to infer the current publish-boundary handoff")
        args.base_ref, args.candidate_ref, args.expected_ref = infer_current_handoff_refs()
        print("[INFO] Inferred refs from current publish-boundary handoff:")
        print(f"  base: {args.base_ref}")
        print(f"  candidate: {args.candidate_ref}")
        print(f"  expected: {args.expected_ref}")

    default_allowed = [] if args.no_default_allow_paths else DEFAULT_ALLOWED_PATHS
    allowed_paths = set(default_allowed + args.allow_path)

    expected_changed = set(changed_paths(args.base_ref, args.expected_ref))
    candidate_changed = set(changed_paths(args.base_ref, args.candidate_ref))
    interesting_paths = sorted(expected_changed - allowed_paths)
    candidate_only_paths = sorted((candidate_changed - expected_changed) - allowed_paths)

    mismatches: list[str] = []
    for path in interesting_paths:
        if not path_matches_expected_delta(
            args.base_ref,
            args.candidate_ref,
            args.expected_ref,
            path,
        ):
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
        if candidate_only_paths:
            print("Ignored candidate-only paths:")
            for path in candidate_only_paths:
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
    if candidate_only_paths:
        print("Ignored candidate-only paths:")
        for path in candidate_only_paths:
            print(f"  {path}")
    print(f"Checked expected functional paths: {len(interesting_paths)}")


if __name__ == "__main__":
    main()
