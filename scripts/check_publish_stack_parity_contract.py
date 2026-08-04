#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_publish_stack_parity.py"
SMOKE = REPO_ROOT / "scripts" / "smoke_test_publish_stack_parity.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")
smoke_text = SMOKE.read_text(encoding="utf-8")

required = [
    ('from collections import Counter', "Publish stack parity checker imports Counter for per-path delta accounting"),
    ('import re', "Publish stack parity checker imports regex support for handoff parsing"),
    ('COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"', "Publish stack parity checker targets the commit-candidate handoff artifact"),
    ('DEFAULT_ALLOWED_PATHS = [', "Publish stack parity checker defines default allowed noisy paths"),
    ('"docs/BOOTSTRAP_VM_VERIFICATION.md"', "Publish stack parity checker allows the boundary doc by default"),
    ('"docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Publish stack parity checker allows the checkpoint doc by default"),
    ('"ci-artifacts/branch-reconcile-2026-07-10.md"', "Publish stack parity checker allows the checked-in branch-reconcile handoff note by default"),
    ('def git_output(*args: str) -> str | None:', "Publish stack parity checker defines optional git output capture for inferred refs"),
    ('def changed_paths(base_ref: str, tip_ref: str) -> list[str]:', "Publish stack parity checker defines changed-path collection"),
    ('run_git("diff", "--name-only", f"{base_ref}..{tip_ref}")', "Publish stack parity checker diffs refs by changed path"),
    ('def file_text(ref: str, path: str) -> str | None:', "Publish stack parity checker defines per-ref file loading"),
    ('result = run_git("show", f"{ref}:{path}", check=False)', "Publish stack parity checker reads candidate and expected file contents through git show"),
    ('if "exists on disk, but not in" in result.stderr or "does not exist in" in result.stderr:', "Publish stack parity checker treats missing paths as absent content instead of crashing"),
    ('def path_delta(base_ref: str, tip_ref: str, path: str) -> tuple[Counter[str], Counter[str]]:', "Publish stack parity checker can read per-path diff deltas from the shared base"),
    ('run_git(\n        "diff",', "Publish stack parity checker shells out to git diff for per-path delta inspection"),
    ('def path_matches_expected_delta(', "Publish stack parity checker defines a delta-absorption matcher"),
    ('return not (expected_removed - candidate_removed or expected_added - candidate_added)', "Publish stack parity checker accepts cleaner files that absorb the expected delta even if they add extra local helper coverage"),
    ('def infer_current_handoff_refs() -> tuple[str, str, str]:', "Publish stack parity checker can infer refs from the current publish-boundary handoff"),
    ('re.search(r"^Current local checkpoint:\\s+(\\S+)$", commit_candidate_text, re.M)', "Publish stack parity checker extracts the local checkpoint ref from the handoff artifact"),
    ('base_ref = git_output("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{current_branch}@{{upstream}}")', "Publish stack parity checker derives the shared base from the current branch upstream"),
    ('expected_ref = "HEAD"', "Publish stack parity checker compares the tracked checkpoint to the current checked-out tip by default"),
    ('"--allow-path"', "Publish stack parity checker supports explicit extra allowed paths"),
    ('"--no-default-allow-paths"', "Publish stack parity checker can disable the default noisy doc allowlist"),
    ('nargs="?"', "Publish stack parity checker allows omitted refs for inferred-handoff mode"),
    ('parser.error("pass either all three refs or none to infer the current publish-boundary handoff")', "Publish stack parity checker fails clearly on partial inferred-ref input"),
    ('print("[INFO] Inferred refs from current publish-boundary handoff:")', "Publish stack parity checker reports inferred refs before running"),
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

smoke_required = [
    ('git branch -q -f local-checkpoint candidate-good', "Publish stack parity smoke test pins a tracked local checkpoint ref for inferred-handoff mode"),
    ('git commit -q -m "docs only tip"', "Publish stack parity smoke test creates a doc-only checked-out tip above the tracked checkpoint"),
    ('Current checked-out branch tip: expected (docs only tip)', "Publish stack parity smoke test records the doc-only checked-out tip in the handoff artifact"),
    ('git add ci-artifacts/branch-reconcile-2026-07-10.md', "Publish stack parity smoke test checks the inferred-handoff path while the checked-in branch-reconcile note differs"),
    ('python3 scripts/check_publish_stack_parity.py"', "Publish stack parity smoke test exercises inferred-handoff mode with omitted refs"),
    ('Checked expected functional paths: 1', "Publish stack parity smoke test asserts inferred-handoff mode ignores the doc-only tip delta"),
    ('Expected inferred-handoff parity run to ignore the doc-only tip delta.', "Publish stack parity smoke test fails clearly when doc-only-tip parity regresses"),
    ('NO_UPSTREAM_DIR="$TMP_DIR/no-upstream"', "Publish stack parity smoke test creates an isolated repo without an upstream for inferred-handoff failure coverage"),
    ("Expected inferred-handoff parity run to fail without an upstream.", "Publish stack parity smoke test fails clearly when the no-upstream fail-closed path regresses"),
    ("Could not infer refs: branch 'no-upstream' has no upstream; pass explicit refs instead.", "Publish stack parity smoke test asserts the no-upstream inferred-handoff failure guidance"),
    ('DETACHED_DIR="$TMP_DIR/detached"', "Publish stack parity smoke test creates an isolated detached-HEAD repo for inferred-handoff failure coverage"),
    ("Expected inferred-handoff parity run to fail from detached HEAD.", "Publish stack parity smoke test fails clearly when the detached-HEAD fail-closed path regresses"),
    ("Could not infer refs: detached HEAD does not provide a stable expected ref; pass explicit refs instead.", "Publish stack parity smoke test asserts the detached-HEAD inferred-handoff failure guidance"),
]

for needle, message in smoke_required:
    if needle not in smoke_text:
        fail(message)
    ok(message)

print("[PASS] Publish stack parity contract looks sane")
