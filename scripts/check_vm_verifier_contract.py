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
    ('print_artifact_excerpt() {', 'Verifier defines a reusable artifact excerpt helper'),
    ('UNIFAI_VM_VERIFY_FORCE_NO_GH', 'Verifier supports explicit no-gh smoke testing'),
    ('UNIFAI_VM_VERIFY_FORCE_TCG', 'Verifier supports explicit TCG smoke testing'),
    ('gh disabled by UNIFAI_VM_VERIFY_FORCE_NO_GH; using curl-based GitHub API fallback', 'Verifier announces forced gh fallback mode'),
    ('gh not found; using curl-based GitHub API fallback', 'Verifier announces implicit gh fallback mode'),
    ('local token="${GH_TOKEN:-${GITHUB_TOKEN:-}}"', 'Verifier accepts GH_TOKEN or GITHUB_TOKEN for curl fallback'),
    ('sha_json="$(github_api "repos/$REPO_SLUG/commits/$REF" 2>&1)"', 'Verifier captures GitHub API failures while resolving the commit ref'),
    ('[FAIL] Could not resolve commit SHA for $REPO_SLUG@$REF', 'Verifier fails closed when SHA resolution fails'),
    ("[INFO] If '$REF' is a local-only commit, push it first or use a GitHub-visible branch/ref.", 'Verifier explains local-only commit refs are not valid VM verifier inputs'),
    ("SHA=\"$(printf '%s' \"$sha_json\" | jq -r '.sha')\"", 'Verifier resolves commit SHA from captured GitHub API JSON'),
    ('[INFO] UNIFAI_VM_VERIFY_FORCE_TCG=1; forcing TCG emulation', 'Verifier announces forced TCG mode for smoke testing'),
    ('if [ -w /dev/kvm ]; then', 'Verifier checks whether /dev/kvm is writable'),
    ('[INFO] Using KVM acceleration', 'Verifier reports KVM acceleration when available'),
    ('[INFO] /dev/kvm is not writable; falling back to TCG emulation', 'Verifier reports TCG fallback when KVM is unavailable'),
    ('Likely fix path: ensure the operator user can access /dev/kvm (for example via the kvm group), then rerun the verifier for faster KVM-backed proof.', 'Verifier explains likely /dev/kvm recovery when KVM is unavailable'),
    ('QEMU_ACCEL_ARGS=(-enable-kvm -cpu host)', 'Verifier uses host CPU only under KVM'),
    ('QEMU_ACCEL_ARGS=(-cpu max)', 'Verifier uses a portable CPU model in TCG mode'),
    ('>"$QEMU_LOG" 2>&1 &', 'Verifier redirects QEMU stdout/stderr into qemu.log'),
    ('print_artifact_excerpt "serial log" "$SERIAL_LOG"', 'Verifier surfaces serial log excerpts on failure'),
    ('print_artifact_excerpt "qemu log" "$QEMU_LOG"', 'Verifier surfaces qemu log excerpts on failure'),
    ('print_artifact_excerpt "installer output" "$WORK_DIR/installer-output.log"', 'Verifier surfaces installer output excerpts on failure'),
    ('print_artifact_excerpt "vm report" "$REPORT"', 'Verifier surfaces VM report excerpts on failure'),
    ('[FAIL] VM verification passed remotely but the report could not be copied back; evidence bundle: $WORK_DIR', 'Verifier fails closed when the remote report cannot be copied back after a green run'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

if 'for bin in gh jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen timeout; do' in text:
    fail('Verifier should not require gh as a mandatory binary anymore')
ok('Verifier no longer requires gh as a mandatory binary')

print('[PASS] VM verifier contract looks sane')
