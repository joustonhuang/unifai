#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_vm_verifier_checkpoint_freshness.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('DOC_BOUNDARY = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFICATION.md"', "Freshness checker targets the boundary doc"),
    ('DOC_CHECKPOINT = REPO_ROOT / "docs" / "BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md"', "Freshness checker targets the checkpoint doc"),
    ('COMMIT_CANDIDATE = REPO_ROOT / "ci-artifacts" / "bootstrap-preflight" / "commit-candidate.txt"', "Freshness checker targets the handoff artifact"),
    ('def is_checkpoint_doc_only_commit(ref: str) -> bool:', "Freshness checker distinguishes doc-only checkpoint commits"),
    ('tracked_ref = "HEAD"', "Freshness checker starts from the checked-out branch tip"),
    ('while tracked_ref != upstream and is_checkpoint_doc_only_commit(tracked_ref):', "Freshness checker skips doc-only checkpoint commits when finding the tracked publish head"),
    ('current_head_ahead_count = git("rev-list", "--count", f"{upstream}..HEAD")', "Freshness checker captures the live checked-out branch ahead count"),
    ('latest_non_doc_paths = [', "Freshness checker captures the latest non-doc path list from the tracked publish head"),
    ('f"- the latest non-doc logic delta in that local stack is `{tracked_head_short}` (`{tracked_head_subject}`) in:"', "Freshness checker validates the boundary doc latest non-doc heading"),
    ('for path in latest_non_doc_paths:', "Freshness checker validates every latest non-doc path bullet in the boundary doc"),
    ('f"  - `{path}`"', "Freshness checker checks the exact latest non-doc path bullets"),
    ('f"Current branch state: ahead {current_head_ahead_count} over {upstream}\\n"', "Freshness checker validates the handoff branch-state line against HEAD"),
    ('f"Current checked-out branch tip: {current_head_short} ({current_head_subject})\\n"', "Freshness checker validates the handoff checked-out tip line for doc-only cases"),
    ('f"- The branch still needs the current branch tip `{current_head_short}` GitHub-visible; "', "Freshness checker validates the doc-only handoff blocker line against the checked-out tip"),
    ('f"- Make the current branch tip `{current_head_short}` GitHub-visible on `{upstream}`; "', "Freshness checker validates the doc-only next-move line against the checked-out tip"),
    ('"commit-candidate tip line should not be present when the tracked checkpoint is HEAD."', "Freshness checker fails closed on an unexpected tip line at HEAD"),
    ('f"- The branch still needs the local checkpoint chain through `{tracked_head_short}` "', "Freshness checker validates the direct-checkpoint blocker line when HEAD is the tracked publish head"),
    ('f"- Make local checkpoint `{tracked_head_short}` GitHub-visible on `{upstream}`.\\n"', "Freshness checker validates the direct-checkpoint next-move line when HEAD is the tracked publish head"),
    ('f"- The last recorded public blocker remains `Bootstrap Installer Preflight` failing on "',
     "Freshness checker validates the public blocker note against the live GitHub-visible head"),
    ('"[PASS] VM verifier checkpoint artifacts match current repo state"', "Freshness checker emits a passing verdict"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] VM verifier checkpoint freshness contract looks sane")
