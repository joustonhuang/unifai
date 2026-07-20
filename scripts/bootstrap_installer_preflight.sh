#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${1:-$REPO_ROOT/ci-artifacts/bootstrap-preflight}"
REPORT_FILE="$REPORT_DIR/report.txt"
mkdir -p "$REPORT_DIR"

exec > >(tee "$REPORT_FILE")
exec 2>&1

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
  exit 1
}

require_file() {
  local path="$1"
  [ -f "$path" ] || fail "Missing required file: ${path#$REPO_ROOT/}"
  pass "Found ${path#$REPO_ROOT/}"
}

require_grep() {
  local pattern="$1"
  local path="$2"
  grep -Eq "$pattern" "$path" || fail "Expected pattern '$pattern' in ${path#$REPO_ROOT/}"
  pass "Pattern '$pattern' present in ${path#$REPO_ROOT/}"
}

echo "== Bootstrap installer preflight =="
echo "Repo root: $REPO_ROOT"
echo "Report: $REPORT_FILE"

INSTALLER="$REPO_ROOT/installer.sh"
STAGE_INSTALLER="$REPO_ROOT/little7-installer/install.sh"

require_file "$INSTALLER"
require_file "$STAGE_INSTALLER"
require_file "$REPO_ROOT/little7-installer/config/supervisor-secretvault.lock"
require_file "$REPO_ROOT/scripts/check_stage50_openclaw_config.py"
require_file "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"
require_file "$REPO_ROOT/scripts/check_bootstrap_preflight_contract_contract.py"
require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"
require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"
require_file "$REPO_ROOT/scripts/check_github_check_gate.py"
require_file "$REPO_ROOT/scripts/check_github_check_gate_contract.py"
require_file "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"
require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness.py"
require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness_contract.py"
require_file "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_freshness.py"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"
require_file "$REPO_ROOT/scripts/check_vm_host_readiness.sh"
require_file "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"
require_file "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"
require_file "$REPO_ROOT/scripts/check_publish_stack_parity.py"
require_file "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"
require_file "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"
require_file "$REPO_ROOT/scripts/compare_publish_branch_histories.py"
require_file "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"
require_file "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"
require_file "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"
require_file "$REPO_ROOT/scripts/check_vm_verifier_contract.py"
require_file "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"
require_file "$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
require_file "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"
require_file "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_gh_unauthenticated_fallback.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_missing_report_fail_closed.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"
require_file "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"

if git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$REPO_ROOT" submodule update --init --recursive supervisor/supervisor-secretvault
  pass "supervisor-secretvault submodule initialized"
fi

bash -n "$INSTALLER"
pass "installer.sh passes bash -n"

bash -n "$STAGE_INSTALLER"
pass "little7-installer/install.sh passes bash -n"

bash "$STAGE_INSTALLER" verify
pass "little7-installer/install.sh verify passed"

python3 -m py_compile "$REPO_ROOT/scripts/check_stage50_openclaw_config.py"
pass "Stage 50 OpenClaw config checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"
pass "Bootstrap preflight contract checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_preflight_contract_contract.py"
pass "Bootstrap preflight contract checker contract passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"
pass "Bootstrap workflow contract checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"
pass "Bootstrap workflow contract checker contract passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_github_check_gate.py"
pass "GitHub check gate inspector passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_github_check_gate_contract.py"
pass "GitHub check gate contract checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"
pass "VM verifier checkpoint refresh helper passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness.py"
pass "VM verifier checkpoint freshness checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness_contract.py"
pass "VM verifier checkpoint freshness contract checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"
pass "VM verifier checkpoint refresh contract checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_freshness.py"
pass "VM verifier checkpoint freshness smoke script passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"
pass "VM verifier checkpoint refresh smoke script passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"
pass "GitHub check gate smoke script passes py_compile"

bash -n "$REPO_ROOT/scripts/check_vm_host_readiness.sh"
pass "VM host readiness helper passes bash -n"

python3 -m py_compile "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"
pass "VM host readiness contract checker passes py_compile"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"
pass "VM host readiness smoke script passes bash -n"

python3 -m py_compile "$REPO_ROOT/scripts/check_publish_stack_parity.py"
pass "Publish stack parity checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"
pass "Publish stack parity contract checker passes py_compile"

bash -n "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"
pass "Publish stack parity smoke script passes bash -n"

python3 -m py_compile "$REPO_ROOT/scripts/compare_publish_branch_histories.py"
pass "Publish branch history helper passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"
pass "Publish branch history contract checker passes py_compile"

bash -n "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"
pass "Publish branch history smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/check_github_branch_visibility.sh"
pass "GitHub branch visibility helper passes bash -n"

bash -n "$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"
pass "VM verifier local preflight helper passes bash -n"

python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_contract.py"
pass "VM verifier contract checker passes py_compile"

python3 -m py_compile "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"
pass "VM verifier preflight wrapper contract checker passes py_compile"

python3 "$REPO_ROOT/scripts/check_stage50_openclaw_config.py"
pass "Stage 50 OpenClaw config contract check passed"

python3 "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"
pass "Bootstrap preflight contract check passed"

python3 "$REPO_ROOT/scripts/check_bootstrap_preflight_contract_contract.py"
pass "Bootstrap preflight contract checker contract check passed"

python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract.py"
pass "Bootstrap workflow contract check passed"

python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"
pass "Bootstrap workflow contract checker contract check passed"

python3 "$REPO_ROOT/scripts/check_github_check_gate_contract.py"
pass "GitHub check gate contract check passed"

python3 "$REPO_ROOT/scripts/refresh_vm_verifier_checkpoint_state.py"
pass "VM verifier checkpoint state refreshed"

python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness.py"
pass "VM verifier checkpoint freshness check passed"

python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_freshness_contract.py"
pass "VM verifier checkpoint freshness contract check passed"

python3 "$REPO_ROOT/scripts/check_vm_verifier_checkpoint_refresh_contract.py"
pass "VM verifier checkpoint refresh contract check passed"

python3 "$REPO_ROOT/scripts/check_vm_host_readiness_contract.py"
pass "VM host readiness contract check passed"

python3 "$REPO_ROOT/scripts/check_publish_stack_parity_contract.py"
pass "Publish stack parity contract check passed"

python3 "$REPO_ROOT/scripts/check_compare_publish_branch_histories_contract.py"
pass "Publish branch history contract check passed"

python3 "$REPO_ROOT/scripts/check_vm_verifier_contract.py"
pass "VM verifier contract check passed"

python3 "$REPO_ROOT/scripts/check_vm_verifier_preflight_contract.py"
pass "VM verifier preflight wrapper contract check passed"

bash -n "$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
pass "VM verifier script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"
pass "GitHub branch visibility smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"
pass "VM verifier red-path smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"
pass "VM verifier GitHub fallback smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_gh_unauthenticated_fallback.sh"
pass "VM verifier unauthenticated-gh fallback smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"
pass "VM verifier TCG launch smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"
pass "VM verifier kvm-fallback guidance smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_missing_report_fail_closed.sh"
pass "VM verifier missing-report fail-closed smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"
pass "VM verifier failure-excerpt smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"
pass "VM verifier remote-failure excerpt smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"
pass "VM verifier remote-failure missing-report smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"
pass "VM verifier installer-failure excerpt smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"
pass "VM verifier preflight wrapper smoke script passes bash -n"

bash -n "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"
pass "VM verifier preflight no-GitHub-remote smoke script passes bash -n"

bash "$REPO_ROOT/scripts/smoke_test_github_branch_visibility.sh"
pass "GitHub branch visibility smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_host_readiness.sh"
pass "VM host readiness smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_publish_stack_parity.sh"
pass "Publish stack parity smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_compare_publish_branch_histories.sh"
pass "Publish branch history smoke test passed"

python3 "$REPO_ROOT/scripts/smoke_test_github_check_gate.py"
pass "GitHub check gate smoke test passed"

python3 -B "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_freshness.py"
pass "VM verifier checkpoint freshness smoke test passed"

python3 -B "$REPO_ROOT/scripts/smoke_test_vm_verifier_checkpoint_refresh.py"
pass "VM verifier checkpoint refresh smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"
pass "VM verifier red-path smoke test failed closed as expected"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"
pass "VM verifier GitHub fallback smoke test failed closed as expected"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_gh_unauthenticated_fallback.sh"
pass "VM verifier unauthenticated-gh fallback smoke test failed closed as expected"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_tcg_launch.sh"
pass "VM verifier TCG launch smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_kvm_fallback_guidance.sh"
pass "VM verifier kvm-fallback guidance smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_missing_report_fail_closed.sh"
pass "VM verifier missing-report fail-closed smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_failure_excerpts.sh"
pass "VM verifier failure-excerpt smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_excerpts.sh"
pass "VM verifier remote-failure excerpt smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_remote_failure_missing_report.sh"
pass "VM verifier remote-failure missing-report smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_installer_failure_excerpts.sh"
pass "VM verifier installer-failure excerpt smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_wrapper.sh"
pass "VM verifier preflight wrapper smoke test passed"

bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_preflight_no_github_remote.sh"
pass "VM verifier preflight no-GitHub-remote smoke test passed"

require_grep 'check_root\s*\(' "$INSTALLER"
require_grep 'check_os\s*\(' "$INSTALLER"
require_grep 'phase_8_validation\s*\(' "$INSTALLER"

for service in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do
  require_grep "$service" "$INSTALLER"
done

require_grep 'curl -fsSL https://openclaw.ai/install.sh \| bash' "$REPO_ROOT/little7-installer/stages/50_openclaw.sh"
pass "Stage 50 uses official OpenClaw installer"

cat <<'EOF'

== Preflight summary ==
This preflight only proves installer structure and cheap sanity checks.
It does NOT prove a fresh VM can boot the stack end-to-end.
For the common local VM prep path, run: bash scripts/run_vm_verifier_preflight.sh <github-visible-ref>
If you only want to inspect host-side friction first, run: bash scripts/check_vm_host_readiness.sh
Run the local VM verifier after GitHub checks are green.
EOF
