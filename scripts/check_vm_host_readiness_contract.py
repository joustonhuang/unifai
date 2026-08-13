#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_vm_host_readiness.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ("PASS_COUNT=0", "VM host readiness helper tracks passing checks"),
    ("WARN_COUNT=0", "VM host readiness helper tracks warnings"),
    ("FAIL_COUNT=0", "VM host readiness helper tracks failures"),
    ("GH_INSTALLED=0", "VM host readiness helper tracks gh presence"),
    ("GH_AUTHENTICATED=0", "VM host readiness helper tracks gh auth state"),
    ("TOKEN_PRESENT=0", "VM host readiness helper tracks token fallback state"),
    ('for bin in jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen scp timeout; do', "VM host readiness helper checks the required verifier binaries"),
    ("pass '/dev/kvm exists and is writable'", "VM host readiness helper reports writable /dev/kvm as a pass"),
    ("warn '/dev/kvm exists but is not writable; verifier will fall back to TCG emulation'", "VM host readiness helper warns when /dev/kvm is not writable"),
    ("warn '/dev/kvm is absent; verifier will fall back to TCG emulation'", "VM host readiness helper warns when /dev/kvm is absent"),
    ("if command -v gh >/dev/null 2>&1; then", "VM host readiness helper checks whether gh is installed"),
    ("if gh auth status >/dev/null 2>&1; then", "VM host readiness helper checks whether gh is authenticated"),
    ("pass 'gh is installed and authenticated'", "VM host readiness helper reports authenticated gh as a pass"),
    ("warn 'gh is installed but not authenticated; curl fallback or token env will be used'", "VM host readiness helper warns when gh is unauthenticated"),
    ("warn 'gh is not installed; curl fallback or token env will be used'", "VM host readiness helper warns when gh is absent"),
    ('if [ -n "${GH_TOKEN:-}" ] || [ -n "${GITHUB_TOKEN:-}" ]; then', "VM host readiness helper checks GH_TOKEN/GITHUB_TOKEN fallback"),
    ("pass 'GitHub token env is present for curl fallback'", "VM host readiness helper reports token-backed curl fallback"),
    ("pass 'Authenticated gh covers normal GitHub API reads without token-only fallback'", "VM host readiness helper treats authenticated gh as sufficient for normal API reads"),
    ("warn 'No GH_TOKEN/GITHUB_TOKEN in environment; public API fallback may rate-limit or fail closed'", "VM host readiness helper warns when no GitHub token fallback is present"),
    ('printf \'\\nSummary: %d pass, %d warn, %d fail\\n\' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"', "VM host readiness helper prints a summary line"),
    ('printf \'Suggested next actions:\\n\'', "VM host readiness helper prints actionable recovery guidance when warnings exist"),
    ("printf -- '- Likely fix path: ensure the operator user can access /dev/kvm (for example via the kvm group), then rerun the readiness check.\\n'", "VM host readiness helper explains /dev/kvm recovery"),
    ("printf -- '- Authenticate gh on this host before the first GitHub-visible VM proof, or rely on a token-only fallback.\\n'", "VM host readiness helper explains unauthenticated gh recovery"),
    ("printf -- '- Install/authenticate gh if you want API-backed verifier checks without token-only fallback.\\n'", "VM host readiness helper explains missing gh recovery"),
    ('if [ "$TOKEN_PRESENT" -eq 0 ] && [ "$GH_AUTHENTICATED" -eq 0 ]; then', "VM host readiness helper only asks for token export when gh auth is unavailable"),
    ("printf -- '- Export GH_TOKEN or GITHUB_TOKEN if you want curl fallback to avoid unauthenticated GitHub API limits.\\n'", "VM host readiness helper explains token export recovery"),
    ('if [ "$FAIL_COUNT" -ne 0 ]; then', "VM host readiness helper fails closed when required binaries are missing"),
    ("exit 1", "VM host readiness helper exits non-zero on failure"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] VM host readiness contract looks sane")
