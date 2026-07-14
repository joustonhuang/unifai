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
    ('require_file "$REPO_ROOT/little7-installer/config/supervisor-secretvault.lock"', 'Preflight requires the SecretVault lock contract file'),
    ('require_file "$REPO_ROOT/scripts/check_stage50_openclaw_config.py"', 'Preflight requires the Stage 50 OpenClaw config checker'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Preflight requires the bootstrap preflight contract checker'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_preflight_contract_contract.py"', 'Preflight requires the bootstrap preflight contract checker contract'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"', 'Preflight requires the workflow contract checker'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Preflight requires the workflow contract checker contract'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate.py"', 'Preflight requires the GitHub check-gate inspector'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Preflight requires the GitHub check-gate contract checker'),
    ('require_file "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Preflight requires the VM verifier checkpoint refresh helper'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"', 'Preflight requires the VM verifier checkpoint refresh contract checker'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Preflight requires the VM verifier checkpoint refresh smoke test'),
    ('require_file "$REPO_ROOT/scripts/check_vm_host_readiness.sh"', 'Preflight requires the VM host readiness helper'),
    ('require_file "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"', 'Preflight requires the VM host readiness contract checker'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Preflight requires the VM host readiness smoke test'),
    ('require_file "$REPO_ROOT/scripts/check_publish_stack_parity.py"', 'Preflight requires the publish stack parity checker'),
    ('require_file "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"', 'Preflight requires the publish stack parity contract checker'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"', 'Preflight requires the publish stack parity smoke test'),
    ('require_file "$REPO_ROOT/scripts/compare_publish_branch_histories.py"', 'Preflight requires the publish branch history helper'),
    ('require_file "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"', 'Preflight requires the publish branch history contract checker'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"', 'Preflight requires the publish branch history smoke test'),
    ('require_file "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"', 'Preflight requires the VM verifier preflight wrapper'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Preflight requires the VM verifier contract checker'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"', 'Preflight requires the VM verifier preflight wrapper contract checker'),
    ('require_file "$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"', 'Preflight requires the VM verifier script'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Preflight requires the GitHub branch-visibility smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Preflight requires the GitHub check-gate smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"', 'Preflight requires the verifier red-path smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"', 'Preflight requires the verifier GitHub fallback smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_gh_unauthenticated_fallback.sh"', 'Preflight requires the VM verifier unauthenticated-gh fallback smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"', 'Preflight requires the VM verifier TCG launch smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"', 'Preflight requires the VM verifier kvm-fallback guidance smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_missing_report_fail_closed.sh"', 'Preflight requires the VM verifier missing-report fail-closed smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"', 'Preflight requires the VM verifier failure-excerpt smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"', 'Preflight requires the VM verifier remote-failure excerpt smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"', 'Preflight requires the VM verifier remote-failure missing-report smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"', 'Preflight requires the VM verifier installer-failure excerpt smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"', 'Preflight requires the VM verifier preflight-wrapper smoke test'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"', 'Preflight requires the VM verifier missing-GitHub-remote smoke test'),
    ('bash -n "$INSTALLER"', 'Preflight syntax-checks installer.sh'),
    ('bash -n "$STAGE_INSTALLER"', 'Preflight syntax-checks little7-installer/install.sh'),
    ('bash "$STAGE_INSTALLER" verify', 'Preflight runs little7-installer/install.sh verify'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_stage50_openclaw_config.py"', 'Preflight syntax-checks the Stage 50 OpenClaw config checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Preflight syntax-checks the bootstrap preflight contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_preflight_contract_contract.py"', 'Preflight syntax-checks the bootstrap preflight contract checker contract'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"', 'Preflight syntax-checks the workflow contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Preflight syntax-checks the workflow contract checker contract'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_github_check_gate.py"', 'Preflight syntax-checks the GitHub check-gate inspector'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Preflight syntax-checks the GitHub check-gate contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Preflight syntax-checks the VM verifier checkpoint refresh helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"', 'Preflight syntax-checks the VM verifier checkpoint refresh contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Preflight syntax-checks the VM verifier checkpoint refresh smoke test'),
    ('bash -n "$REPO_ROOT/scripts/check_vm_host_readiness.sh"', 'Preflight syntax-checks the VM host readiness helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"', 'Preflight syntax-checks the VM host readiness contract checker'),
    ('bash -n "$REPO_ROOT/scripts/check_github_branch_visibility.sh"', 'Preflight syntax-checks the GitHub branch-visibility helper'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Preflight syntax-checks the VM host readiness smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_publish_stack_parity.py"', 'Preflight syntax-checks the publish stack parity checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"', 'Preflight syntax-checks the publish stack parity contract checker'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"', 'Preflight syntax-checks the publish stack parity smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/compare_publish_branch_histories.py"', 'Preflight syntax-checks the publish branch history helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"', 'Preflight syntax-checks the publish branch history contract checker'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"', 'Preflight syntax-checks the publish branch history smoke test'),
    ('bash -n "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"', 'Preflight syntax-checks the VM verifier preflight wrapper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Preflight syntax-checks the VM verifier contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"', 'Preflight syntax-checks the VM verifier preflight wrapper contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Preflight syntax-checks the GitHub check-gate smoke test'),
    ('bash -n "$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"', 'Preflight syntax-checks the VM verifier script'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Preflight syntax-checks the GitHub branch-visibility smoke script'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"', 'Preflight syntax-checks the verifier red-path smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"', 'Preflight syntax-checks the verifier GitHub fallback smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_gh_unauthenticated_fallback.sh"', 'Preflight syntax-checks the VM verifier unauthenticated-gh fallback smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"', 'Preflight syntax-checks the VM verifier TCG launch smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"', 'Preflight syntax-checks the VM verifier kvm-fallback guidance smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_missing_report_fail_closed.sh"', 'Preflight syntax-checks the VM verifier missing-report fail-closed smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"', 'Preflight syntax-checks the VM verifier failure-excerpt smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"', 'Preflight syntax-checks the VM verifier remote-failure excerpt smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"', 'Preflight syntax-checks the VM verifier remote-failure missing-report smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"', 'Preflight syntax-checks the VM verifier installer-failure excerpt smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"', 'Preflight syntax-checks the VM verifier preflight-wrapper smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"', 'Preflight syntax-checks the VM verifier missing-GitHub-remote smoke test'),
    ('python3 "$REPO_ROOT/scripts/check_stage50_openclaw_config.py"', 'Preflight runs the Stage 50 OpenClaw config checker'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Preflight runs the bootstrap preflight contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_preflight_contract_contract.py"', 'Preflight runs the bootstrap preflight contract checker contract'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"', 'Preflight runs the workflow contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Preflight runs the workflow contract checker contract'),
    ('python3 "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Preflight runs the GitHub check-gate contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"', 'Preflight runs the VM verifier checkpoint refresh contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"', 'Preflight runs the VM host readiness contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"', 'Preflight runs the publish stack parity contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"', 'Preflight runs the publish branch history contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Preflight runs the VM verifier contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"', 'Preflight runs the VM verifier preflight wrapper contract checker'),
    ('bash "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Preflight runs the GitHub branch-visibility smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Preflight runs the VM host readiness smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"', 'Preflight runs the publish stack parity smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"', 'Preflight runs the publish branch history smoke test'),
    ('python3 "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Preflight runs the GitHub check-gate smoke test'),
    ('python3 -B "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Preflight runs the VM verifier checkpoint refresh smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"', 'Preflight runs the verifier red-path smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"', 'Preflight runs the verifier GitHub fallback smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_gh_unauthenticated_fallback.sh"', 'Preflight runs the verifier unauthenticated-gh fallback smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"', 'Preflight runs the verifier TCG launch smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"', 'Preflight runs the verifier kvm-fallback guidance smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_missing_report_fail_closed.sh"', 'Preflight runs the verifier missing-report fail-closed smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"', 'Preflight runs the verifier failure-excerpt smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"', 'Preflight runs the verifier remote-failure excerpt smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"', 'Preflight runs the verifier remote-failure missing-report smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"', 'Preflight runs the verifier installer-failure excerpt smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"', 'Preflight runs the verifier preflight-wrapper smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"', 'Preflight runs the verifier missing-GitHub-remote smoke test'),
    ('require_grep \'check_root\\s*\\(\' "$INSTALLER"', 'Preflight requires installer.sh to keep the root check entrypoint'),
    ('require_grep \'check_os\\s*\\(\' "$INSTALLER"', 'Preflight requires installer.sh to keep the OS check entrypoint'),
    ('require_grep \'phase_8_validation\\s*\\(\' "$INSTALLER"', 'Preflight requires installer.sh to keep the phase_8_validation entrypoint'),
    ('for service in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do', 'Preflight requires installer.sh service-boundary assertions for SecretVault, Keyman, Supervisor, and OpenClaw'),
    ('require_grep "$service" "$INSTALLER"', 'Preflight enforces each installer service-boundary assertion through the service loop'),
    ('require_grep \'curl -fsSL https://openclaw.ai/install.sh \\| bash\' "$REPO_ROOT/little7-installer/stages/50_openclaw.sh"', 'Preflight requires Stage 50 to keep using the official OpenClaw installer command'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] Bootstrap preflight contract looks sane')
