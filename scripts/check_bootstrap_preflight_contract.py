#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = REPO_ROOT / "scripts" / "bootstrap_installer_preflight.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = PREFLIGHT.read_text(encoding="utf-8")

required = [
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"', 'Preflight requires the workflow contract checker'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate.py"', 'Preflight requires the GitHub check-gate inspector'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Preflight requires the GitHub check-gate contract checker'),
    ('require_file "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Preflight requires the VM verifier checkpoint refresh helper'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Preflight requires the VM verifier checkpoint refresh smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Preflight requires the VM host readiness smoke test'),
    ('require_file "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"', 'Preflight requires the VM verifier preflight wrapper'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"', 'Preflight requires the VM verifier preflight wrapper contract checker'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Preflight requires the GitHub branch-visibility smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Preflight requires the GitHub check-gate smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"', 'Preflight requires the VM verifier TCG launch smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"', 'Preflight requires the VM verifier kvm-fallback guidance smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"', 'Preflight requires the VM verifier failure-excerpt smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"', 'Preflight requires the VM verifier remote-failure excerpt smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"', 'Preflight requires the VM verifier remote-failure missing-report smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"', 'Preflight requires the VM verifier installer-failure excerpt smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"', 'Preflight requires the VM verifier preflight-wrapper smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"', 'Preflight syntax-checks the workflow contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Preflight syntax-checks the GitHub check-gate contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Preflight syntax-checks the VM verifier checkpoint refresh helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Preflight syntax-checks the VM verifier checkpoint refresh smoke test'),
    ('bash -n "$REPO_ROOT/scripts/check_github_branch_visibility.sh"', 'Preflight syntax-checks the GitHub branch-visibility helper'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Preflight syntax-checks the VM host readiness smoke test'),
    ('bash -n "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"', 'Preflight syntax-checks the VM verifier preflight wrapper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"', 'Preflight syntax-checks the VM verifier preflight wrapper contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Preflight syntax-checks the GitHub check-gate smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"', 'Preflight syntax-checks the VM verifier TCG launch smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"', 'Preflight syntax-checks the VM verifier kvm-fallback guidance smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"', 'Preflight syntax-checks the VM verifier failure-excerpt smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"', 'Preflight syntax-checks the VM verifier remote-failure excerpt smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"', 'Preflight syntax-checks the VM verifier remote-failure missing-report smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"', 'Preflight syntax-checks the VM verifier installer-failure excerpt smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"', 'Preflight syntax-checks the VM verifier preflight-wrapper smoke test'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"', 'Preflight runs the workflow contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Preflight runs the GitHub check-gate contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"', 'Preflight runs the VM verifier preflight wrapper contract checker'),
    ('bash "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Preflight runs the GitHub branch-visibility smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Preflight runs the VM host readiness smoke test'),
    ('python3 "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Preflight runs the GitHub check-gate smoke test'),
    ('python3 "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Preflight runs the VM verifier checkpoint refresh smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"', 'Preflight runs the verifier red-path smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"', 'Preflight runs the verifier GitHub fallback smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"', 'Preflight runs the verifier TCG launch smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"', 'Preflight runs the verifier kvm-fallback guidance smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"', 'Preflight runs the verifier failure-excerpt smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"', 'Preflight runs the verifier remote-failure excerpt smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"', 'Preflight runs the verifier remote-failure missing-report smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"', 'Preflight runs the verifier installer-failure excerpt smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"', 'Preflight runs the verifier preflight-wrapper smoke test'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] Bootstrap preflight contract looks sane')
