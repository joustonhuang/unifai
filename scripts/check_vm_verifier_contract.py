#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFIER = REPO_ROOT / "scripts" / "vm" / "verify_bootstrap_in_vm.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = VERIFIER.read_text(encoding="utf-8")

required = [
    ('QEMU_LOG="$WORK_DIR/qemu.log"', 'Verifier captures QEMU output into qemu.log'),
    ('UNIFAI_VM_VERIFY_FORCE_NO_GH', 'Verifier supports explicit no-gh smoke testing'),
    ('gh disabled by UNIFAI_VM_VERIFY_FORCE_NO_GH; using curl-based GitHub API fallback', 'Verifier announces forced gh fallback mode'),
    ('gh not found; using curl-based GitHub API fallback', 'Verifier announces implicit gh fallback mode'),
    ('local token="${GH_TOKEN:-${GITHUB_TOKEN:-}}"', 'Verifier accepts GH_TOKEN or GITHUB_TOKEN for curl fallback'),
    ("SHA=\"$(github_api \"repos/$REPO_SLUG/commits/$REF\" | jq -r '.sha')\"", 'Verifier resolves commit SHA through the shared GitHub API helper'),
    ('[FAIL] Could not resolve commit SHA for $REPO_SLUG@$REF', 'Verifier fails closed when SHA resolution fails'),
    ('if [ -w /dev/kvm ]; then', 'Verifier checks whether /dev/kvm is writable'),
    ('[INFO] Using KVM acceleration', 'Verifier reports KVM acceleration when available'),
    ('[INFO] /dev/kvm is not writable; falling back to TCG emulation', 'Verifier reports TCG fallback when KVM is unavailable'),
    ('QEMU_ACCEL_ARGS=(-enable-kvm -cpu host)', 'Verifier uses host CPU only under KVM'),
    ('QEMU_ACCEL_ARGS=(-cpu max)', 'Verifier uses a portable CPU model in TCG mode'),
    ('>"$QEMU_LOG" 2>&1 &', 'Verifier redirects QEMU stdout/stderr into qemu.log'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

if 'for bin in gh jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen timeout; do' in text:
    fail('Verifier should not require gh as a mandatory binary anymore')
ok('Verifier no longer requires gh as a mandatory binary')

print('[PASS] VM verifier contract looks sane')
