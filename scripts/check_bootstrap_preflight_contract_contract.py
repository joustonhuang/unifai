#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_bootstrap_preflight_contract.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('PREFLIGHT = REPO_ROOT / "scripts" / "bootstrap_installer_preflight.sh"', 'Bootstrap preflight contract checker targets bootstrap_installer_preflight.sh'),
    ('DIRTY_STATE_HELPER = REPO_ROOT / "scripts" / "check_checkpoint_handoff_dirty_state.sh"', 'Bootstrap preflight contract checker targets the checkpoint handoff dirty-state helper'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Bootstrap preflight contract checker requires the preflight checker itself'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Bootstrap preflight contract checker requires the workflow contract checker contract'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate.py"', 'Bootstrap preflight contract checker requires the GitHub check-gate inspector'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Bootstrap preflight contract checker requires the GitHub check-gate contract checker path'),
    ('require_file "$REPO_ROOT/scripts/check_github_branch_visibility.sh"', 'Bootstrap preflight contract checker requires the GitHub branch-visibility helper path'),
    ('require_file "$REPO_ROOT/scripts/check_github_branch_visibility_contract.py"', 'Bootstrap preflight contract checker requires the GitHub branch-visibility contract checker path'),
    ('require_file "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Bootstrap preflight contract checker requires the VM verifier checkpoint refresh helper path'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness.py"', 'Bootstrap preflight contract checker requires the VM verifier checkpoint freshness checker path'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness_contract.py"', 'Bootstrap preflight contract checker requires the VM verifier checkpoint freshness contract checker path'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"', 'Bootstrap preflight contract checker requires the VM verifier checkpoint refresh contract checker path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_freshness.py"', 'Bootstrap preflight contract checker requires the VM verifier checkpoint freshness smoke test path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Bootstrap preflight contract checker requires the VM verifier checkpoint refresh smoke test path'),
    ('require_file "$REPO_ROOT/scripts/check_checkpoint_handoff_dirty_state.sh"', 'Bootstrap preflight contract checker requires the checkpoint handoff dirty-state helper path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_checkpoint_handoff_dirty_state.sh"', 'Bootstrap preflight contract checker requires the checkpoint handoff dirty-state smoke test path'),
    ('require_file "$REPO_ROOT/scripts/check_vm_host_readiness.sh"', 'Bootstrap preflight contract checker requires the VM host readiness helper'),
    ('require_file "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"', 'Bootstrap preflight contract checker requires the VM host readiness contract checker path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Bootstrap preflight contract checker requires the VM host readiness smoke test path'),
    ('require_file "$REPO_ROOT/scripts/check_publish_stack_parity.py"', 'Bootstrap preflight contract checker requires the publish stack parity checker path'),
    ('require_file "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"', 'Bootstrap preflight contract checker requires the publish stack parity contract checker path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"', 'Bootstrap preflight contract checker requires the publish stack parity smoke test path'),
    ('require_file "$REPO_ROOT/scripts/compare_publish_branch_histories.py"', 'Bootstrap preflight contract checker requires the publish branch history helper path'),
    ('require_file "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"', 'Bootstrap preflight contract checker requires the publish branch history contract checker path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"', 'Bootstrap preflight contract checker requires the publish branch history smoke test path'),
    ('require_file "$REPO_ROOT/scripts/check_branch_reconcile_handoff.py"', 'Bootstrap preflight contract checker requires the branch-reconcile handoff checker path'),
    ('require_file "$REPO_ROOT/scripts/check_branch_reconcile_handoff_contract.py"', 'Bootstrap preflight contract checker requires the branch-reconcile handoff contract checker path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_branch_reconcile_handoff.sh"', 'Bootstrap preflight contract checker requires the branch-reconcile handoff smoke test path'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Bootstrap preflight contract checker requires the VM verifier contract checker'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract_contract.py"', 'Bootstrap preflight contract checker requires the VM verifier preflight wrapper contract checker contract path'),
    ('require_file "$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"', 'Bootstrap preflight contract checker requires the VM verifier script path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Bootstrap preflight contract checker requires the GitHub check-gate smoke test path'),
    ('require_file "$REPO_ROOT/scripts/smoke_test_github_branch_visibility_no_github_remote.sh"', 'Bootstrap preflight contract checker requires the GitHub branch-visibility no-GitHub-remote smoke test path'),
    ('bash -n "$INSTALLER"', 'Bootstrap preflight contract checker requires installer.sh syntax coverage'),
    ('bash -n "$STAGE_INSTALLER"', 'Bootstrap preflight contract checker requires little7-installer/install.sh syntax coverage'),
    ('bash "$STAGE_INSTALLER" verify', 'Bootstrap preflight contract checker requires little7-installer/install.sh verify coverage'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Bootstrap preflight contract checker requires self py_compile coverage'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the GitHub check-gate contract checker'),
    ('bash -n "$REPO_ROOT/scripts/check_github_branch_visibility.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the branch-visibility helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_github_branch_visibility_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the branch-visibility contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the checkpoint refresh helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the checkpoint freshness checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the checkpoint freshness contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the checkpoint refresh contract checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_freshness.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the checkpoint freshness smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the checkpoint refresh smoke test'),
    ('bash -n "$REPO_ROOT/scripts/check_checkpoint_handoff_dirty_state.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the checkpoint handoff dirty-state helper'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_checkpoint_handoff_dirty_state.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the checkpoint handoff dirty-state smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the VM host readiness contract checker'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the VM host readiness smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_publish_stack_parity.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the publish stack parity checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the publish stack parity contract checker'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the publish stack parity smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/compare_publish_branch_histories.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the publish branch history helper'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the publish branch history contract checker'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the publish branch history smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_branch_reconcile_handoff.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the branch-reconcile handoff checker'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_branch_reconcile_handoff_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the branch-reconcile handoff contract checker'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_branch_reconcile_handoff.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the branch-reconcile handoff smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Bootstrap preflight contract checker requires syntax coverage for the GitHub check-gate smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the branch-visibility smoke test'),
    ('bash -n "$REPO_ROOT/scripts/smoke_test_github_branch_visibility_no_github_remote.sh"', 'Bootstrap preflight contract checker requires syntax coverage for the branch-visibility no-GitHub-remote smoke test'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract_contract.py"', 'Bootstrap preflight contract checker requires py_compile coverage for the VM verifier preflight wrapper contract checker contract'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for itself'),
    ('\'CHECKPOINT_HANDOFF_PATHS=(\'', 'Bootstrap preflight contract checker requires explicit tracking of the verifier checkpoint handoff artifact set'),
    ("'collect_checkpoint_handoff_dirty_paths() {'", 'Bootstrap preflight contract checker requires centralized dirty-handoff collection'),
    ("'check_checkpoint_handoff_dirty_state() {'", 'Bootstrap preflight contract checker requires centralized dirty-state classification'),
    ("'UNIFAI_PREFLIGHT_PRE_REFRESH_HANDOFF_PATHS=\"$pre_refresh_paths\" \\\\'", 'Bootstrap preflight contract checker requires passing pre-refresh handoff paths into the helper'),
    ("'UNIFAI_PREFLIGHT_REFRESHED_HANDOFF_PATHS=\"$refreshed_paths\" \\\\'", 'Bootstrap preflight contract checker requires passing refreshed handoff paths into the helper'),
    ("'bash \"$REPO_ROOT/scripts/check_checkpoint_handoff_dirty_state.sh\"'", 'Bootstrap preflight contract checker requires delegating dirty-state classification to the helper'),
    ("'collect_checkpoint_handoff_dirty_paths pre_refresh_handoff_paths'", 'Bootstrap preflight contract checker requires a pre-refresh dirty-handoff snapshot'),
    ("'collect_checkpoint_handoff_dirty_paths refreshed_handoff_paths'", 'Bootstrap preflight contract checker requires a post-refresh dirty-handoff snapshot'),
    ('\'UNIFAI_PREFLIGHT_REFRESHED_HANDOFF_PATHS="$(printf \\\'%s\\\\n\\\' "${refreshed_handoff_paths[@]}")"\'', 'Bootstrap preflight contract checker requires serializing refreshed handoff paths for the helper'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the workflow contract checker contract'),
    ('python3 "$REPO_ROOT/scripts/check_github_check_gate_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the GitHub check-gate contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_github_branch_visibility_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the branch-visibility contract checker'),
    ('python3 "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"', 'Bootstrap preflight contract checker requires runtime coverage for the checkpoint refresh helper'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness.py"', 'Bootstrap preflight contract checker requires runtime coverage for the checkpoint freshness checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the checkpoint freshness contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the checkpoint refresh contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the VM host readiness contract checker'),
    ('bash "$REPO_ROOT/scripts/smoke_test_checkpoint_handoff_dirty_state.sh"', 'Bootstrap preflight contract checker requires the checkpoint handoff dirty-state smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"', 'Bootstrap preflight contract checker requires the VM host readiness smoke test'),
    ('python3 "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the publish stack parity contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the publish branch history contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_branch_reconcile_handoff.py"', 'Bootstrap preflight contract checker requires runtime coverage for the branch-reconcile handoff checker'),
    ('python3 "$REPO_ROOT/scripts/check_branch_reconcile_handoff_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the branch-reconcile handoff contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the VM verifier contract checker'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the VM verifier preflight wrapper contract checker contract'),
    ('python3 -B "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_freshness.py"', 'Bootstrap preflight contract checker requires bytecode-cache-proof runtime coverage for the checkpoint freshness smoke test'),
    ('python3 -B "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"', 'Bootstrap preflight contract checker requires bytecode-cache-proof runtime coverage for the checkpoint refresh smoke test'),
    ('python3 "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"', 'Bootstrap preflight contract checker requires the GitHub check-gate smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"', 'Bootstrap preflight contract checker requires the publish stack parity smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"', 'Bootstrap preflight contract checker requires the publish branch history smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_branch_reconcile_handoff.sh"', 'Bootstrap preflight contract checker requires the branch-reconcile handoff smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"', 'Bootstrap preflight contract checker requires the branch-visibility smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_github_branch_visibility_no_github_remote.sh"', 'Bootstrap preflight contract checker requires the branch-visibility no-GitHub-remote smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"', 'Bootstrap preflight contract checker requires the verifier GitHub fallback smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"', 'Bootstrap preflight contract checker requires the verifier red-path smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"', 'Bootstrap preflight contract checker requires the missing-GitHub-remote preflight smoke test'),
    ('for service in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do', 'Bootstrap preflight contract checker requires the installer service-boundary loop'),
    ('require_grep "$service" "$INSTALLER"', 'Bootstrap preflight contract checker requires per-service installer grep assertions'),
    ('\'require_grep \\\'curl -fsSL https://openclaw.ai/install.sh \\\\| bash\\\' "$REPO_ROOT/little7-installer/stages/50_openclaw.sh"\'', 'Bootstrap preflight contract checker requires the Stage 50 OpenClaw installer grep'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

helper_required = [
    ('helper_text = DIRTY_STATE_HELPER.read_text(encoding="utf-8")', 'Bootstrap preflight contract checker reads the checkpoint handoff dirty-state helper text'),
    ('helper_required = [', 'Bootstrap preflight contract checker keeps explicit helper-specific coverage requirements'),
    ("'[FAIL] Bootstrap preflight refreshed checkpoint handoff artifacts but they are not committed yet:'", 'Bootstrap preflight contract checker requires a fail-closed message for dirty refreshed handoff artifacts in the helper'),
    ('\'[INFO] Checkpoint handoff artifacts that were already dirty before this rerun and still need review:\'', 'Bootstrap preflight contract checker requires mixed-state handoff guidance in the helper'),
    ('\'Review/add/commit the refreshed verifier checkpoint handoff before treating this ref as preflight-green.\'', 'Bootstrap preflight contract checker requires recovery guidance for a dirty refreshed handoff in the helper'),
    ('\'[FAIL] Bootstrap preflight checkpoint handoff artifacts were already dirty before refresh and are still not committed:\'', 'Bootstrap preflight contract checker requires a fail-closed message for pre-existing dirty handoff artifacts in the helper'),
    ('\'Review/add/commit the existing verifier checkpoint handoff dirtiness before treating this ref as preflight-green.\'', 'Bootstrap preflight contract checker requires recovery guidance for pre-existing dirty handoff artifacts in the helper'),
    ('for needle, message in helper_required:', 'Bootstrap preflight contract checker validates helper-specific requirements'),
    ('if needle not in helper_text:', 'Bootstrap preflight contract checker checks the dirty-state helper text directly'),
]

for needle, message in helper_required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] Bootstrap preflight contract checker contract looks sane')
